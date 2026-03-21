import os
from fastapi import FastAPI
from audiotool.core import process_audio

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


@app.get("/summarize")
def summarize():
    result = process_audio("input/audio.wav", True)
    return {"message": result}
