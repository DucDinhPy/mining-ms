from typing import Any

from backend.workers.camera_manager import CameraManager


def list_camera_runtime_status(
    camera_manager: CameraManager,
) -> dict[str, Any]:
    cameras = []

    for health in camera_manager.get_all_health():
        cameras.append({
            "camera_id": health["camera_id"],
            "name": health["name"],
            "runtime_status": health["status"],
            "last_error": health["last_error"],
            "has_snapshot": health["has_snapshot"],
            "thread_alive": health["thread_alive"],
        })

    return {
        "count": len(cameras),
        "cameras": cameras,
    }


def get_latest_ppe_detections(
    camera_manager: CameraManager,
    camera_id: str,
) -> dict[str, Any]:
    worker = camera_manager.get_worker(camera_id)

    if worker is None:
        return {
            "found": False,
            "camera_id": camera_id,
            "message": (
                "Camera worker was not found or is not active."
            ),
        }

    snapshot = worker.get_snapshot()

    if snapshot is None:
        return {
            "found": True,
            "camera_id": camera_id,
            "camera_name": worker.name,
            "message": "No PPE detection result is available yet.",
        }

    snapshot.pop("jpeg", None)

    return {
        "found": True,
        **snapshot,
    }