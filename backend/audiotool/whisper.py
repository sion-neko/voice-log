import logging
from .segment import Segment

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


def transcribe(input_file):
    # whisper large-v3 を GPU でロード
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16")
        logger.info("GPU (CUDA) model loaded successfully for faster-whisper.")
    except Exception as e:
        logger.error(f"Error loading GPU model: {e}")
        return

    logger.info("Transcribing...")
    segments, info = model.transcribe(
        input_file, language="ja", word_timestamps=True)

    duration = info.duration
    logger.info(f"Target audio duration: {duration:.2f} seconds")

    result = []
    _last_percentage = 0
    for segment in segments:
        result.append(Segment(segment.start, segment.end, text=segment.text))
        percentage = int((segment.end / duration) * 100) if duration > 0 else 0
        if percentage >= _last_percentage + 5:  # log every 5%
            logger.info(
                f"Transcription progress: {percentage}% ({segment.end:.2f}s / {duration:.2f}s)")
            _last_percentage = percentage

    logger.info("Transcription completed.")

    # 処理終了後にモデルをアンロードしてVRAMを解放する
    logger.info("Unloading Whisper model from VRAM...")
    try:
        del segments
        del model
    except NameError:
        pass
    import gc
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Whisper model unloaded.")

    return result


if __name__ == "__main__":
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

    segments = transcribe("input/audio.wav")
    for segment in segments:
        print(segment.text, end="", flush=True)
    print("\nDone transcription.")
