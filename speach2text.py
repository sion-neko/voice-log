import os
import requests
from faster_whisper import WhisperModel

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

try:
    model = WhisperModel("large-v3", device="cuda", compute_type="float16") 
    print("GPU (CUDA) model loaded successfully.")
except Exception as e:
    print(f"Error loading GPU model: {e}")
    print("Falling back to CPU...")
    model = WhisperModel("large-v3", device="cpu")

print("Transcribing...")
segments, info = model.transcribe("input/sample.mp3", language="ja")

text = ""
for segment in segments:
    print(segment.text, end="", flush=True)
    text += segment.text
print("\nDone transcription.")

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