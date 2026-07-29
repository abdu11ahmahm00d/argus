import asyncio
import cv2
import numpy as np
import structlog

log = structlog.get_logger()


class Camera:
    def __init__(
        self, source: str, width: int = 640, height: int = 480, queue_maxsize: int = 3
    ):
        self.source = source
        self.width = width
        self.height = height
        self.queue: asyncio.Queue[np.ndarray] = asyncio.Queue(maxsize=queue_maxsize)
        self._cap: cv2.VideoCapture | None = None
        self._running = False

    async def start(self):
        self._cap = cv2.VideoCapture(self.source)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera source: {self.source}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._running = True
        log.info("camera_started", source=self.source)

    async def capture_loop(self):
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                log.warning("camera_read_failed")
                await asyncio.sleep(0.1)
                continue
            frame = cv2.resize(frame, (self.width, self.height))
            if self.queue.full():
                try:
                    self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await self.queue.put(frame)
            await asyncio.sleep(0)
        log.info("camera_loop_ended")

    async def get_frame(self) -> np.ndarray | None:
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    async def stop(self):
        self._running = False
        if self._cap:
            self._cap.release()
        log.info("camera_stopped")

    @property
    def running(self) -> bool:
        return self._running
