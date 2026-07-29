import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from ultralytics import YOLO
import numpy as np
import structlog

log = structlog.get_logger()


@dataclass
class Detection:
    bbox: tuple[int, int, int, int]
    class_name: str
    confidence: float
    centroid: tuple[int, int]
    crop: np.ndarray | None = None


CLASS_MAP = {0: "capped", 1: "uncapped", 2: "unknown"}


class Detector:
    def __init__(self, model_path: str, confidence_threshold: float = 0.45):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self._executor = ThreadPoolExecutor(max_workers=1)
        log.info("detector_loaded", model_path=model_path)

    async def detect(self, frame: np.ndarray) -> list[Detection]:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(self._executor, self.model, frame, False)
        detections = []
        for r in results:
            if r.boxes is None:
                continue
            for box, cls, conf in zip(
                r.boxes.xyxy.cpu().numpy(),
                r.boxes.cls.cpu().numpy(),
                r.boxes.conf.cpu().numpy(),
            ):
                if conf < self.confidence_threshold:
                    continue
                x1, y1, x2, y2 = map(int, box[:4])
                class_id = int(cls)
                class_name = CLASS_MAP.get(class_id, "unknown")
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                crop = frame[y1:y2, x1:x2].copy() if y2 > y1 and x2 > x1 else None
                detections.append(
                    Detection(
                        bbox=(x1, y1, x2, y2),
                        class_name=class_name,
                        confidence=float(conf),
                        centroid=(cx, cy),
                        crop=crop,
                    )
                )
        return detections
