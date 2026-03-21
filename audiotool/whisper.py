import os
from audiotool.segment import Segment
from faster_whisper import WhisperModel


def transcribe(input_file):
    # whisper large-v3 を GPU でロード
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16")
        print("GPU (CUDA) model loaded successfully.")
    except Exception as e:
        print(f"Error loading GPU model: {e}")
        return

    print("Transcribing...")
    segments, info = model.transcribe(
        input_file, language="ja", word_timestamps=True)
    result = []
    for segment in segments:
        result.append(Segment(segment.start, segment.end, text=segment.text))
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
