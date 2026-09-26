from pathlib import Path
from threading import Lock

import asyncio
import time

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
WEIGHT_PATH = BASE_DIR / "weights" / "best_1.pt"

SOURCE = "rtsp://127.0.0.1:8554/camera01"

if not WEIGHT_PATH.is_file():
    raise FileNotFoundError(f"Can not find: {WEIGHT_PATH}")

model = YOLO(WEIGHT_PATH)
model_lock = Lock()

import time

should_stop = False

while not should_stop:
    print(f"Connecting to {SOURCE}...")

    cap = cv2.VideoCapture(SOURCE, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("Cannot open RTSP stream. Retrying in 3 seconds...")
        cap.release()
        time.sleep(3)
        continue

    print("RTSP stream connected")

    while True:
        success, frame = cap.read()

        if not success:
            print("Stream disconnected. Reconnecting...")
            break

        with model_lock:
            results = model.predict(
                source=frame,
                imgsz=640,
                conf=0.4,
                iou=0.7,
                device=0,
                verbose=False,
            )

        annotated_frame = results[0].plot()

        cv2.imshow("PPE RTSP Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            should_stop = True
            break

    cap.release()

    if not should_stop:
        time.sleep(2)

cv2.destroyAllWindows()
