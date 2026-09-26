import asyncio

from backend.workers.camera_manager import CameraManager


async def main():
    manager = CameraManager(
        camera_api_url="http://localhost:5057/api/cameras",
        sync_interval=10,
        detection_fps=5,
    )

    try:
        await manager.start()

        while True:
            print(manager.get_all_health())
            await asyncio.sleep(5)

    finally:
        await manager.stop()


if __name__ == "__main__":
    asyncio.run(main())