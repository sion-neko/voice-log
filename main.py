import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
from datetime import datetime
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"]
)


@app.post("/summarize")
def summarize(file: UploadFile = File(...)):
    with open("audio_temp.wav", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # result = process_audio("audio_temp.wav", True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diarization_result = {"created_at": now, "segments": []}
    diarization_result["segments"].append({
        "start": 0,
        "end": 10,
        "speaker": "Speaker 1",
        "text": "Hello World"
    })
    os.remove("audio_temp.wav")
    return diarization_result


@app.get("/")
def read_root():
    return {"message": "Hello World"}
