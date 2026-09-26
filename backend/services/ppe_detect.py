from pathlib import Path
from threading import Lock

import asyncio
import time

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ultralytics import YOLO

BACKEND_DIR = Path(__file__).resolve().parents[1]
WEIGHT_PATH = BACKEND_DIR / "weights" / "best_1.pt"

SOURCE = 6

if not WEIGHT_PATH.is_file():
    raise FileNotFoundError(f"Can not find: {WEIGHT_PATH}")

model = YOLO(WEIGHT_PATH)
model_lock = Lock()

def detect_ppe(image_bytes: bytes, conf: float = 0.4):
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    return detect_frame(frame, conf)

def detect_frame(frame: np.ndarray, conf: float = 0.4):
    if frame is None:
        raise ValueError("Invalid video frame")

    height, width = frame.shape[:2]

    with model_lock:
        result = model.predict(
            source=frame,
            imgsz=640,
            conf=conf,
            iou=0.7,
            device=0,
            verbose=False,
        )[0]

    detections = []

    if result.boxes is not None:
        boxes = result.boxes.xyxy.cpu().tolist()
        scores = result.boxes.conf.cpu().tolist()
        classes = result.boxes.cls.cpu().tolist()

        for box, score, class_id in zip(boxes, scores, classes):
            detections.append({
                "class_name": model.names[int(class_id)],
                "confidence": round(float(score), 4),
                "bbox": [
                    round(float(value), 2)
                    for value in box
                ],
            })

    return {
        "width": width,
        "height": height,
        "detections": detections,
    }

