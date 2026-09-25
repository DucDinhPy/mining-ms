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

SOURCE = 6

if not WEIGHT_PATH.is_file():
    raise FileNotFoundError(f"Can not find: {WEIGHT_PATH}")

model = YOLO(WEIGHT_PATH)
model_lock = Lock()

cap = cv2.VideoCapture(SOURCE)

while True:
    success, frame = cap.read()

    if not success:
        break

    results = model(frame)

    annotated = results[0].plot()

    cv2.imshow("PPE Detection", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
