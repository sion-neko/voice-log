import os
import bisect
from audiotool.whisper import transcribe
from audiotool.diarization import diarization
from audiotool.summarize import summarize


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


def process_audio(input_file, only_transcription):
    segments_transcribe = transcribe(input_file)
    segments_diarization = diarization(input_file)

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
    text = ""
    for segment in segments_merged:
        text += f"{segment.start:.2f} - {segment.end:.2f} | {segment.speaker} | {segment.text}\n"

    if not only_transcription:
        summary = summarize(text)
        return summary
    else:
        return text


if __name__ == "__main__":
    cuda_setup()
    INPUT_FILE = "input/audio.wav"
    ONLY_TRANSCRIPTION = True

    # process_audio is the main processing logic
    result = process_audio(INPUT_FILE, ONLY_TRANSCRIPTION)
    print(result)
