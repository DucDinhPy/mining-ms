import asyncio
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.ppe_detect import detect_ppe


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["ppe"],
)


@router.websocket("/ws/detect")
async def realtime_detection(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            image_bytes = await websocket.receive_bytes()

            result = await asyncio.to_thread(
                detect_ppe,
                image_bytes,
            )

            await websocket.send_json(result)

    except WebSocketDisconnect:
        pass

    except Exception as error:
        logger.exception("Webcam detection error")

        try:
            await websocket.send_json({
                "type": "error",
                "message": str(error),
            })
            await websocket.close(code=1011)
        except RuntimeError:
            pass


@router.websocket("/ws/cameras/{camera_id}")
async def camera_detection_stream(
    websocket: WebSocket,
    camera_id: str,
):
    await websocket.accept()

    camera_manager = getattr(
        websocket.app.state,
        "camera_manager",
        None,
    )

    if camera_manager is None:
        await websocket.send_json({
            "type": "error",
            "message": "Camera manager is unavailable.",
        })
        await websocket.close(code=1011)
        return

    worker = camera_manager.get_worker(camera_id)

    if worker is None:
        await websocket.send_json({
            "type": "error",
            "message": (
                "Camera was not found or is not Online."
            ),
        })
        await websocket.close(code=4404)
        return

    last_sequence = 0
    last_status_at = 0.0

    try:
        while True:
            worker = camera_manager.get_worker(camera_id)

            if worker is None:
                await websocket.send_json({
                    "type": "error",
                    "message": "Camera worker is no longer active.",
                })
                await websocket.close(code=4404)
                return

            snapshot = worker.get_snapshot()

            if (
                snapshot is not None
                and snapshot["sequence"] > last_sequence
            ):
                jpeg = snapshot.pop("jpeg")
                last_sequence = snapshot["sequence"]

                await websocket.send_json({
                    "type": "frame_metadata",
                    **snapshot,
                })

                await websocket.send_bytes(jpeg)

            else:
                now = time.monotonic()

                if now - last_status_at >= 2:
                    health = worker.get_health()

                    await websocket.send_json({
                        "type": "camera_status",
                        "camera_id": camera_id,
                        "name": health["name"],
                        "status": health["status"],
                        "last_error": health["last_error"],
                        "sequence": health["sequence"],
                    })

                    last_status_at = now

            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        logger.info(
            "Camera WebSocket disconnected: %s",
            camera_id,
        )

    except Exception:
        logger.exception(
            "Camera WebSocket error: %s",
            camera_id,
        )

        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass