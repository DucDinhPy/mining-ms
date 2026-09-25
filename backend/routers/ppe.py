from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

from backend.services.ppe_detect import detect_ppe

router = APIRouter(prefix="/api", tags=["ppe"])

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
        await websocket.send_json({
            "error": str(error),
        })
        await websocket.close()

