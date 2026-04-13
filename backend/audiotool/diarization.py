import torch
import logging
from pyannote.audio import Pipeline
from .segment import Segment

logger = logging.getLogger(__name__)

def diarization(input_file):
    logger.info("Loading Pyannote diarization model...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=True)
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pipeline.to(device)
    logger.info(f"Pyannote diarization model loaded on device: {device}")

    logger.info("Diarizing...")
    diarization = pipeline(input_file)

    result = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        result.append(Segment(turn.start, turn.end, speaker=speaker))
    logger.info("Diarization completed.")
    return result


if __name__ == "__main__":
    segments = diarization("input/audio.wav")
    for segment in segments:
        print(segment)
