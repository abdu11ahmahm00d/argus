import cv2
import numpy as np
import structlog

log = structlog.get_logger()


def is_inside_zone(point: tuple[int, int], polygon: list) -> bool:
    pt = (int(point[0]), int(point[1]))
    return cv2.pointPolygonTest(np.array(polygon, dtype=np.int32), pt, False) >= 0


def get_zone_name(point: tuple[int, int], safe_zone: list, danger_zone: list) -> str:
    if is_inside_zone(point, danger_zone):
        return "danger"
    if is_inside_zone(point, safe_zone):
        return "safe"
    return "outside"


def draw_zones(frame: np.ndarray, safe_zone: list, danger_zone: list) -> np.ndarray:
    overlay = frame.copy()
    if safe_zone:
        pts = np.array(safe_zone, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(overlay, [pts], (0, 255, 0))
        cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
    if danger_zone:
        pts = np.array(danger_zone, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(overlay, [pts], (0, 0, 255))
        cv2.polylines(frame, [pts], True, (0, 0, 255), 2)
    return cv2.addWeighted(overlay, 0.2, frame, 0.8, 0)


def get_zone_centroid(polygon: list) -> tuple[int, int]:
    if not polygon:
        return (0, 0)
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return (int(sum(xs) / len(xs)), int(sum(ys) / len(ys)))
