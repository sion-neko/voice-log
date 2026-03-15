import os
import requests
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline

# GPUライブラリ (CUDA/cuDNN) のパスを動的に追加
base_path = os.path.dirname(os.path.abspath(__file__))
cuda_paths = [
    os.path.join(base_path, "venv", "Lib", "site-packages", "nvidia", "cublas", "bin"),
    os.path.join(base_path, "venv", "Lib", "site-packages", "nvidia", "cudnn", "bin"),
]

for path in cuda_paths:
    if os.path.exists(path):
        print(f"Adding DLL directory: {path}")
        os.add_dll_directory(path)

def main(input_file, only_transcription):
    # whisper large-v3 を GPU でロード
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16") 
        print("GPU (CUDA) model loaded successfully.")
    except Exception as e:
        print(f"Error loading GPU model: {e}")
        return

    print("Transcribing...")
    segments, info = model.transcribe(input_file, language="ja", word_timestamps=True)

    with open("output.txt", "w", encoding="utf-8") as f:
        for segment in segments:
            for word in segment.words:
                print("[%.2fs -> %.2fs] %s" % (word.start, word.end, word.word))
                f.write(word.word)

    text = ""
    for segment in segments:
        print(segment.text, end="", flush=True)
        text += segment.text
    print("\nDone transcription.")

    if not only_transcription:
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "qwen3.5:4b",
            "prompt": "要約してください。" + text,
            "stream": False
        }

        print("Summarizing with Ollama...")
        try:
            res = requests.post(url, json=data)
            print("\nSummary:")
            print(res.json()["response"])
        except Exception as e:
            print(f"\nError connecting to Ollama: {e}")

if __name__ == "__main__":
    INPUT_FILE = "input/lesson.wav"
    ONLY_TRANSCRIPTION = True
    main(INPUT_FILE, ONLY_TRANSCRIPTION)