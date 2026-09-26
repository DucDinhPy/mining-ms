import logging
import threading
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

import cv2

from backend.services.ppe_detect import detect_frame


logger = logging.getLogger(__name__)


class CameraWorker:
    def __init__(
        self,
        camera_id: str,
        name: str,
        stream_url: str,
        detection_fps: float = 5.0,
        reconnect_delay: float = 3.0,
        jpeg_quality: int = 75,
    ):
        self.camera_id = camera_id
        self.name = name
        self.stream_url = stream_url
        self.detection_fps = detection_fps
        self.reconnect_delay = reconnect_delay
        self.jpeg_quality = jpeg_quality

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self._status = "stopped"
        self._last_error: str | None = None
        self._latest_snapshot: dict[str, Any] | None = None
        self._sequence = 0

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name=f"camera-{self.camera_id}",
            daemon=True,
        )
        self._thread.start()

        logger.info(
            "Camera worker started: %s (%s)",
            self.name,
            self.camera_id,
        )

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=10)

            if self._thread.is_alive():
                logger.warning(
                    "Camera worker did not stop in time: %s",
                    self.camera_id,
                )

        self._thread = None
        self._set_status("stopped")

        logger.info(
            "Camera worker stopped: %s (%s)",
            self.name,
            self.camera_id,
        )

    def get_snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            return deepcopy(self._latest_snapshot)

    def get_health(self) -> dict[str, Any]:
        with self._lock:
            return {
                "camera_id": self.camera_id,
                "name": self.name,
                "stream_url": self.stream_url,
                "status": self._status,
                "last_error": self._last_error,
                "sequence": self._sequence,
                "has_snapshot": self._latest_snapshot is not None,
                "thread_alive": self.is_running,
            }

    def _run(self) -> None:
        while not self._stop_event.is_set():
            capture = None

            try:
                self._set_status("connecting")

                logger.info(
                    "Connecting camera %s to %s",
                    self.camera_id,
                    self.stream_url,
                )

                capture = cv2.VideoCapture(
                    self.stream_url,
                    cv2.CAP_FFMPEG,
                )

                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                if not capture.isOpened():
                    raise ConnectionError(
                        f"Cannot open RTSP stream: {self.stream_url}"
                    )

                self._set_status("online", clear_error=True)

                logger.info(
                    "Camera connected: %s (%s)",
                    self.name,
                    self.camera_id,
                )

                self._read_stream(capture)

            except Exception as error:
                logger.exception(
                    "Camera worker error: %s (%s)",
                    self.name,
                    self.camera_id,
                )
                self._set_status(
                    "offline",
                    error=str(error),
                )

            finally:
                if capture is not None:
                    capture.release()

            if not self._stop_event.is_set():
                self._stop_event.wait(self.reconnect_delay)

        self._set_status("stopped")

    def _read_stream(self, capture: cv2.VideoCapture) -> None:
        interval = 1.0 / max(self.detection_fps, 0.1)
        next_detection_at = 0.0

        while not self._stop_event.is_set():
            success, frame = capture.read()

            if not success or frame is None:
                raise ConnectionError(
                    f"Lost RTSP stream: {self.stream_url}"
                )

            now = time.monotonic()

            if now < next_detection_at:
                continue

            next_detection_at = now + interval

            try:
                result = detect_frame(frame)

                encoded, jpeg_buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [
                        cv2.IMWRITE_JPEG_QUALITY,
                        self.jpeg_quality,
                    ],
                )

                if not encoded:
                    raise ValueError("Could not encode camera frame")

                self._publish_snapshot(
                    result=result,
                    jpeg=jpeg_buffer.tobytes(),
                )

            except Exception as error:
                logger.exception(
                    "PPE detection failed for camera %s",
                    self.camera_id,
                )
                self._record_error(str(error))

    def _publish_snapshot(
        self,
        result: dict[str, Any],
        jpeg: bytes,
    ) -> None:
        with self._lock:
            self._sequence += 1
            self._status = "online"
            self._last_error = None

            self._latest_snapshot = {
                "camera_id": self.camera_id,
                "camera_name": self.name,
                "sequence": self._sequence,
                "captured_at": datetime.now(
                    timezone.utc,
                ).isoformat(),
                "width": result["width"],
                "height": result["height"],
                "detections": result["detections"],
                "jpeg": jpeg,
            }

    def _set_status(
        self,
        status: str,
        error: str | None = None,
        clear_error: bool = False,
    ) -> None:
        with self._lock:
            self._status = status

            if error is not None:
                self._last_error = error
            elif clear_error:
                self._last_error = None

    def _record_error(self, error: str) -> None:
        with self._lock:
            self._last_error = error