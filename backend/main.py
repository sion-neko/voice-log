import os
import json
import logging
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import shutil
from pathlib import Path
from audiotool.core import process_audio
from audiotool.summarize import summarize as summarize_audio
from datetime import datetime
from audiotool.notion import format_and_save_summary

OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def _save_json(data: dict, filename: str, folder_name: str) -> str:
    folder = OUTPUT_DIR / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / f"{filename}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved: {filepath}")
    return filepath


def _update_status(folder_name: str, step: str, status: str):
    folder = OUTPUT_DIR / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    status_file = folder / "status.json"
    
    current_status = {
        "transcription": "none",
        "summary": "none",
        "notion": "none"
    }
    
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                current_status.update(json.load(f))
        except:
            pass
            
    current_status[step] = status
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(current_status, f, ensure_ascii=False, indent=2)


# GPUライブラリ (CUDA/cuDNN) のパスを動的に追加
base_path = os.path.dirname(os.path.abspath(__file__))
cuda_paths = [
    os.path.join(base_path, "venv", "Lib", "site-packages",
                 "nvidia", "cublas", "bin"),
    os.path.join(base_path, "venv", "Lib", "site-packages",
                 "nvidia", "cudnn", "bin"),
]
for path in cuda_paths:
    if os.path.exists(path):
        logger.info(f"Adding DLL directory: {path}")
        os.add_dll_directory(path)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory="output"), name="outputs")


def process_audio_background(input_filepath: str, folder_name: str, start_step: str = "transcription"):
    """バックグラウンドで文字起こしと要約を実行する（リトライ時は指定ステップから開始）"""
    logger.info(
        f"[{folder_name}] Starting background processing (Step: {start_step}). Target file: {input_filepath}")

    folder_path = OUTPUT_DIR / folder_name
    transcription_result = {}

    # 1. 文字起こし + 話者分析
    if start_step == "transcription":
        _update_status(folder_name, "transcription", "processing")
        try:
            logger.info(f"[{folder_name}] Starting audio transcription and speaker analysis...")
            transcription_result = process_audio(input_filepath)
            logger.info(f"[{folder_name}] Transcription completed successfully.")
            _update_status(folder_name, "transcription", "success")
        except Exception as e:
            logger.error(f"[{folder_name}] Error in transcription: {e}", exc_info=True)
            transcription_result = {
                "segments": [{"start": 0.0, "end": 0.0, "speaker": "SYSTEM", "text": f"文字起こし処理に失敗しました: {e}"}]
            }
            _update_status(folder_name, "transcription", "failed")
        finally:
            try:
                _save_json(transcription_result, "transcription", folder_name)
            except Exception as e_save:
                logger.error(f"[{folder_name}] Failed to save transcription.json: {e_save}", exc_info=True)
    else:
        # ステップが「要約」または「Notion」からの場合、既存の文字起こし結果をロードする
        try:
            with open(folder_path / "transcription.json", "r", encoding="utf-8") as f:
                transcription_result = json.load(f)
            logger.info(f"[{folder_name}] Loaded existing transcription for {start_step} retry.")
        except Exception as e:
            logger.error(f"[{folder_name}] Failed to load transcription for retry: {e}")
            return

    # 2. 要約
    summary_result = {}
    if start_step in ["transcription", "summary"]:
        _update_status(folder_name, "summary", "processing")
        try:
            segments = transcription_result.get("segments", [])
            if not segments or (len(segments) > 0 and segments[0].get("text", "").startswith("文字起こし処理に失敗しました")):
                logger.warning(f"[{folder_name}] Transcription error or empty. Skipping summarization.")
                summary_result = {"topics": [{"title": "エラー", "summary": "文字起こしデータが無効なため要約できません。", "highlights": []}]}
                _update_status(folder_name, "summary", "failed")
            else:
                logger.info(f"[{folder_name}] Starting summarization generation...")
                summary_result = summarize_audio(segments)
                logger.info(f"[{folder_name}] Summarization completed successfully.")
                _update_status(folder_name, "summary", "success")
        except Exception as e:
            logger.error(f"[{folder_name}] Error in summarization: {e}", exc_info=True)
            summary_result = {"topics": [{"title": "エラー", "summary": f"要約処理に失敗しました: {e}", "highlights": []}]}
            _update_status(folder_name, "summary", "failed")
        finally:
            try:
                _save_json(summary_result, "summary", folder_name)
            except Exception as e_save:
                logger.error(f"[{folder_name}] Failed to save summary.json: {e_save}", exc_info=True)
    else:
        # ステップが「Notion」からの場合、既存の要約結果をロードする
        try:
            with open(folder_path / "summary.json", "r", encoding="utf-8") as f:
                summary_result = json.load(f)
            logger.info(f"[{folder_name}] Loaded existing summary for Notion retry.")
        except Exception as e:
            logger.error(f"[{folder_name}] Failed to load summary for Notion retry: {e}")
            return

    # 3. Notion 出力
    if start_step in ["transcription", "summary", "notion"]:
        # 要約が「エラー」等の場合はスキップする
        topics = summary_result.get("topics", [])
        if topics and topics[0].get("title") == "エラー":
             logger.warning(f"[{folder_name}] Skipping Notion output due to previous error.")
             return

        _update_status(folder_name, "notion", "processing")
        try:
            filename = os.path.basename(input_filepath)
            logger.info(f"[{folder_name}] Saving summary to Notion...")
            format_and_save_summary(filename, summary_result)
            logger.info(f"[{folder_name}] Successfully saved summary to Notion.")
            _update_status(folder_name, "notion", "success")
        except Exception as e_notion:
            logger.error(f"[{folder_name}] Failed to save summary to Notion: {e_notion}", exc_info=True)
            _update_status(folder_name, "notion", "failed")

    logger.info(f"[{folder_name}] Background processing completed.")



class RetryRequest(BaseModel):
    step: str


@app.post("/upload")
def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = file.filename or "unknown.wav"
    stem = Path(original_filename).stem
    folder_name = f"{timestamp}_{stem}"
    folder_path = OUTPUT_DIR / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)

    # 保存
    audio_path = folder_path / original_filename
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info(
        f"[{folder_name}] Received upload file '{original_filename}'. Saved to {audio_path}")
        
    _update_status(folder_name, "transcription", "none")
    _update_status(folder_name, "summary", "none")
    _update_status(folder_name, "notion", "none")
    
    background_tasks.add_task(process_audio_background,
                              str(audio_path), folder_name)

    return {"message": "POSTしました。バックグラウンドで処理を開始します。", "folder": folder_name}


@app.get("/results")
def get_results():
    results = []
    if not OUTPUT_DIR.exists():
        return results

    for folder in sorted(OUTPUT_DIR.iterdir(), key=lambda x: x.name, reverse=True):
        if not folder.is_dir():
            continue

        has_summary = (folder / "summary.json").exists()
        has_transcription = (folder / "transcription.json").exists()

        audio_filename = None
        for f in folder.iterdir():
            if f.is_file() and f.suffix.lower() in [".wav"]:
                audio_filename = f.name
                break

        # フォルダ名からパース
        parts = folder.name.split("_", 2)
        if len(parts) >= 3:
            timestamp_str = f"{parts[0][:4]}/{parts[0][4:6]}/{parts[0][6:]} {parts[1][:2]}:{parts[1][2:4]}:{parts[1][4:]}"
            title = parts[2]
        else:
            timestamp_str = ""
            title = folder.name

        # transcription.jsonから作成日時を取得
        if has_transcription and not timestamp_str:
            try:
                with open(folder / "transcription.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    created_at = data.get("created_at")
                    if created_at:
                        timestamp_str = created_at
            except:
                pass
                
        # Status parsing
        status_data = {
            "transcription": "success" if has_transcription else "none",
            "summary": "success" if has_summary else "none",
            "notion": "none"
        }
        status_file = folder / "status.json"
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    status_data.update(json.load(f))
            except:
                pass

        results.append({
            "id": folder.name,
            "title": title,
            "timestamp": timestamp_str,
            "transcription_status": status_data["transcription"],
            "summary_status": status_data["summary"],
            "notion_status": status_data["notion"],
            "audio_filename": audio_filename
        })

    return {"results": results}


@app.post("/retry/{folder_id}")
def retry_step(folder_id: str, request: RetryRequest, background_tasks: BackgroundTasks):
    folder_path = OUTPUT_DIR / folder_id
    if not folder_path.exists():
        return {"error": "Folder not found"}
        
    step = request.step
    if step not in ["transcription", "summary", "notion"]:
        return {"error": "Invalid step"}

    # 音声ファイルを探す（1つ目に見つかった .wav を対象にする）
    input_filepath = None
    for f in folder_path.iterdir():
        if f.is_file() and f.suffix.lower() in [".wav"]:
            input_filepath = str(f)
            break
            
    if not input_filepath:
        return {"error": "Audio file not found for retry"}

    # 後続のステータスをリセット
    _update_status(folder_id, step, "processing")
    if step == "transcription":
        _update_status(folder_id, "summary", "none")
        _update_status(folder_id, "notion", "none")
    elif step == "summary":
        _update_status(folder_id, "notion", "none")
        
    background_tasks.add_task(process_audio_background, input_filepath, folder_id, step)
    return {"message": f"{step}からの再処理を開始します"}


@app.get("/")
def read_root():
    return {"message": "Hello World"}
