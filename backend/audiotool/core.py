import os
import bisect
from datetime import datetime
from .whisper import transcribe
from .diarization import diarization
import concurrent.futures


def cuda_setup():
    # GPUライブラリ (CUDA/cuDNN) のパスを動的に追加
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


import logging
logger = logging.getLogger(__name__)

def process_audio(input_file):
    logger.info(f"Starting process_audio for {input_file}")
    
    logger.info("--> Calling transcribe() in subprocess to avoid VRAM collision")
    segments_transcribe = transcribe(input_file)
    logger.info("<-- Returned from transcribe()")
    
    logger.info("--> Calling diarization() in subprocess")
    segments_diarization = diarization(input_file)
    logger.info("<-- Returned from diarization()")

    # マージ
    sd_starts = [sd.start for sd in segments_diarization]

    segments_merged = []
    for st in segments_transcribe:
        idx = bisect.bisect_right(sd_starts, st.start) - 1

        st.speaker = segments_diarization[idx].speaker if idx >= 0 else None

        if segments_merged and segments_merged[-1].speaker == st.speaker:
            segments_merged[-1].text += st.text
            segments_merged[-1].end = st.end
        else:
            segments_merged.append(st)

    # 確認
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diarization_result = {"created_at": now, "segments": []}
    for segment in segments_merged:
        diarization_result["segments"].append({
            "start": segment.start,
            "end": segment.end,
            "speaker": segment.speaker,
            "text": segment.text
        })
    return diarization_result


if __name__ == "__main__":
    cuda_setup()
    INPUT_FILE = "input/audio.wav"

    # process_audio is the main processing logic
    result = process_audio(INPUT_FILE)
    print(result)
