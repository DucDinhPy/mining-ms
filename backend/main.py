import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.routers import ppe
from backend.workers.camera_manager import CameraManager


logger = logging.getLogger(__name__)

CAMERA_API_URL = os.getenv(
    "CAMERA_API_URL",
    "http://127.0.0.1:5057/api/cameras",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    camera_manager = CameraManager(
        camera_api_url=CAMERA_API_URL,
        sync_interval=15,
        detection_fps=5,
    )

    app.state.camera_manager = camera_manager

    await camera_manager.start()

    try:
        yield
    finally:
        await camera_manager.stop()


app = FastAPI(
    title="MiningProject API",
    lifespan=lifespan,
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


app.include_router(ppe.router)