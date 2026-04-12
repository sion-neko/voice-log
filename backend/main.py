import os
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
from audiotool.core import process_audio
from audiotool.summarize import summarize as summarize_audio
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def _save_json(data: dict, filename: str, timestamp: str) -> str:
    """タイムスタンプ付きフォルダを作成し、結果をJSONファイルに保存する"""
    folder = os.path.join(OUTPUT_DIR, timestamp)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{filename}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {filepath}")
    return filepath


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
        print(f"Adding DLL directory: {path}")
        os.add_dll_directory(path)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Segment(BaseModel):
    start: float
    end: float
    speaker: str | None = None
    text: str


class SummarizeRequest(BaseModel):
    segments: list[Segment]


# 直近のtranscriptionタイムスタンプを保持（summarizeと同じファイル名ペアにする）
_last_timestamp: str = ""


@app.post("/transcription")
def transcription(file: UploadFile = File(...)):
    global _last_timestamp
    with open("audio_temp.wav", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    result = process_audio("audio_temp.wav")
    os.remove("audio_temp.wav")

    # ファイル出力
    _last_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _save_json(result, "transcription", _last_timestamp)

    return result


@app.post("/summarize")
def summarize(body: SummarizeRequest):
    segments = [seg.model_dump() for seg in body.segments]
    result = summarize_audio(segments)

    # ファイル出力（transcriptionと同じタイムスタンプを使用）
    ts = _last_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    _save_json(result, "summary", ts)

    return result


@app.get("/")
def read_root():
    return {"message": "Hello World"}
