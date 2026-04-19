import os
import torch
import logging
from pyannote.audio import Pipeline
from .segment import Segment

logger = logging.getLogger(__name__)


def diarization(input_file):
    logger.info("Loading Pyannote diarization model...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=os.environ.get("HF_TOKEN", True))

    device = torch.device("cuda")
    pipeline.to(device)
    logger.info(f"Pyannote diarization model loaded on device: {device}")

    logger.info("Diarizing...")
    diarization_result = pipeline(input_file)

    result = []
    for turn, _, speaker in diarization_result.itertracks(yield_label=True):
        result.append(Segment(turn.start, turn.end, speaker=speaker))
    logger.info("Diarization completed.")

    # 処理終了後にモデルをアンロードしてVRAMを解放する
    logger.info("Unloading Pyannote model from VRAM...")
    try:
        del diarization_result
        del pipeline
    except NameError:
        pass
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Pyannote model unloaded.")

    return result


if __name__ == "__main__":
    segments = diarization("input/audio.wav")
    for segment in segments:
        print(segment)
