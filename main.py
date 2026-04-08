from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import os
import uuid

app = FastAPI()

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def mejorar_frame(frame):
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    sharp = cv2.filter2D(frame, -1, kernel)

    alpha = 1.5
    beta = 20
    contrast = cv2.convertScaleAbs(sharp, alpha=alpha, beta=beta)

    b, g, r = cv2.split(contrast)
    b = cv2.add(b, 20)
    r = cv2.add(r, 30)
    cinematic = cv2.merge((b, g, r))

    cinematic = cv2.convertScaleAbs(cinematic, alpha=1.15, beta=-15)

    return cinematic

def procesar_video(input_path, output_path):
    clip = VideoFileClip(input_path)

    def process_frame(frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = mejorar_frame(frame)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    new_clip = clip.fl_image(process_frame)
    new_clip.write_videofile(output_path, codec="libx264", bitrate="8000k")

@app.get("/")
def home():
    return {"message": "JFLcineBoost funcionando 🚀"}

@app.post("/mejorar-video")
async def mejorar_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())

    input_path = f"{UPLOAD_FOLDER}/{file_id}.mp4"
    output_path = f"{OUTPUT_FOLDER}/{file_id}.mp4"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    background_tasks.add_task(procesar_video, input_path, output_path)

    return {"message": "Video en proceso", "file_id": file_id}

@app.get("/descargar/{file_id}")
def descargar(file_id: str):
    output_path = f"{OUTPUT_FOLDER}/{file_id}.mp4"
    return FileResponse(output_path, media_type="video/mp4")
