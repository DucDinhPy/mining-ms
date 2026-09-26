import asyncio
import logging
import threading
from typing import Any

import httpx

from backend.workers.camera_worker import CameraWorker


logger = logging.getLogger(__name__)


class CameraManager:
    def __init__(
        self,
        camera_api_url: str,
        sync_interval: float = 15.0,
        detection_fps: float = 5.0,
    ):
        self.camera_api_url = camera_api_url.rstrip("/")
        self.sync_interval = sync_interval
        self.detection_fps = detection_fps

        self._workers: dict[str, CameraWorker] = {}
        self._lock = threading.Lock()

        self._client: httpx.AsyncClient | None = None
        self._sync_task: asyncio.Task | None = None
        self._stop_event: asyncio.Event | None = None

    async def start(self) -> None:
        if self._sync_task is not None:
            return

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
        )
        self._stop_event = asyncio.Event()

        try:
            await self.sync_once()
        except Exception:
            logger.exception(
                "Initial camera synchronization failed"
            )

        self._sync_task = asyncio.create_task(
            self._sync_loop(),
            name="camera-manager-sync",
        )

        logger.info("Camera manager started")

    async def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()

        if self._sync_task is not None:
            self._sync_task.cancel()

            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

            self._sync_task = None

        with self._lock:
            workers = list(self._workers.values())
            self._workers.clear()

        await asyncio.gather(
            *[
                asyncio.to_thread(worker.stop)
                for worker in workers
            ],
            return_exceptions=True,
        )

        if self._client is not None:
            await self._client.aclose()
            self._client = None

        logger.info("Camera manager stopped")

    async def sync_once(self) -> None:
        cameras = await self._fetch_all_cameras()

        desired_cameras = {
            str(camera["id"]): camera
            for camera in cameras
            if self._should_run(camera)
        }

        with self._lock:
            current_workers = dict(self._workers)

        for camera_id, worker in current_workers.items():
            camera = desired_cameras.get(camera_id)

            must_stop = (
                camera is None
                or camera.get("streamUrl") != worker.stream_url
            )

            if not must_stop:
                continue

            await asyncio.to_thread(worker.stop)

            with self._lock:
                self._workers.pop(camera_id, None)

        for camera_id, camera in desired_cameras.items():
            with self._lock:
                existing_worker = self._workers.get(camera_id)

            if existing_worker is not None:
                continue

            worker = CameraWorker(
                camera_id=camera_id,
                name=camera.get("name") or camera_id,
                stream_url=camera["streamUrl"],
                detection_fps=self.detection_fps,
            )

            worker.start()

            with self._lock:
                self._workers[camera_id] = worker

        logger.info(
            "Camera sync completed. Active workers: %s",
            len(desired_cameras),
        )

    def get_worker(
        self,
        camera_id: str,
    ) -> CameraWorker | None:
        with self._lock:
            return self._workers.get(camera_id)

    def get_all_health(self) -> list[dict[str, Any]]:
        with self._lock:
            workers = list(self._workers.values())

        return [
            worker.get_health()
            for worker in workers
        ]

    async def _sync_loop(self) -> None:
        if self._stop_event is None:
            return

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.sync_interval,
                )
                break

            except asyncio.TimeoutError:
                try:
                    await self.sync_once()

                except asyncio.CancelledError:
                    raise

                except Exception:
                    logger.exception(
                        "Could not synchronize cameras"
                    )

    async def _fetch_all_cameras(
        self,
    ) -> list[dict[str, Any]]:
        if self._client is None:
            raise RuntimeError(
                "CameraManager has not been started"
            )

        cameras: list[dict[str, Any]] = []
        page = 1
        page_size = 100

        while True:
            response = await self._client.get(
                self.camera_api_url,
                params={
                    "page": page,
                    "pageSize": page_size,
                },
            )
            response.raise_for_status()

            payload = response.json()
            items = payload.get("items", [])

            cameras.extend(items)

            total_count = int(
                payload.get("totalCount", len(cameras))
            )

            if len(cameras) >= total_count:
                break

            if not items:
                break

            page += 1

        return cameras

    @staticmethod
    def _should_run(
        camera: dict[str, Any],
    ) -> bool:
        status = camera.get("status")
        stream_url = str(
            camera.get("streamUrl") or ""
        ).strip()

        is_online = (
            status == 1
            or str(status).lower() == "online"
        )

        return is_online and bool(stream_url)