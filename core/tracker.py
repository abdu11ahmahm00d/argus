import numpy as np
from filterpy.kalman import KalmanFilter
import structlog

log = structlog.get_logger()


class ObjectTrack:
    def __init__(self, track_id: int, centroid: tuple[float, float], dt: float = 1.0):
        self.track_id = track_id
        self.kf = KalmanFilter(dim_x=4, dim_z=2)
        self.kf.F = np.array(
            [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float
        )
        self.kf.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=float)
        self.kf.P *= 10.0
        self.kf.R = np.eye(2) * 5.0
        self.kf.Q = np.eye(4) * 0.1
        self.kf.x[:2] = np.array([[centroid[0]], [centroid[1]]])
        self.age = 0
        self.history: list[tuple[float, float]] = [centroid]
        self.class_name: str | None = None
        self.worker_name: str | None = None
        self.helmet_number: int | None = None

    def update(self, centroid: tuple[float, float]):
        self.kf.predict()
        self.kf.update(np.array([[centroid[0]], [centroid[1]]]))
        self.age = 0
        self.history.append(centroid)
        if len(self.history) > 30:
            self.history.pop(0)

    def predict(self, steps_ahead: int = 15) -> tuple[float, float]:
        f = self.kf.F.copy()
        f[0, 2] = steps_ahead
        f[1, 3] = steps_ahead
        pred = f @ self.kf.x
        return (float(pred[0, 0]), float(pred[1, 0]))

    def get_velocity(self) -> tuple[float, float]:
        return (float(self.kf.x[2, 0]), float(self.kf.x[3, 0]))

    def get_speed(self) -> float:
        vx, vy = self.get_velocity()
        return float(np.sqrt(vx**2 + vy**2))

    def get_centroid(self) -> tuple[float, float]:
        return (float(self.kf.x[0, 0]), float(self.kf.x[1, 0]))

    def is_running(self, threshold: float = 5.0) -> bool:
        return self.get_speed() > threshold

    def is_approaching_zone(
        self, predicted_pos: tuple[float, float], danger_polygon: list
    ) -> bool:
        import cv2

        pt = (int(predicted_pos[0]), int(predicted_pos[1]))
        danger_np = (
            np.array(danger_polygon, dtype=np.int32) if danger_polygon else np.array([])
        )
        if danger_np.size == 0:
            return False
        return cv2.pointPolygonTest(danger_np, pt, False) >= 0

    def time_to_zone_entry(
        self,
        pos: tuple[float, float],
        velocity: tuple[float, float],
        danger_polygon: list,
    ) -> float:
        if not self.is_approaching_zone(
            (pos[0] + velocity[0] * 30, pos[1] + velocity[1] * 30), danger_polygon
        ):
            return float("inf")
        speed = self.get_speed()
        if speed < 0.1:
            return float("inf")
        cx, cy = pos
        pts = np.array(danger_polygon, dtype=np.int32)
        distances = [
            np.linalg.norm(np.array([cx, cy]) - pt.astype(float))
            for pt in pts.reshape(-1, 2)
        ]
        min_dist = min(distances)
        return min_dist / speed


class TrackerManager:
    def __init__(
        self, max_age: int = 30, speed_threshold: float = 5.0, predict_frames: int = 15
    ):
        self.tracks: dict[int, ObjectTrack] = {}
        self.next_id = 0
        self.max_age = max_age
        self.speed_threshold = speed_threshold
        self.predict_frames = predict_frames

    def update_or_create(
        self,
        centroid: tuple[float, float],
        class_name: str | None = None,
        worker_name: str | None = None,
        helmet_number: int | None = None,
    ):
        matched_id = self._match_track(centroid)
        if matched_id is not None:
            track = self.tracks[matched_id]
            track.update(centroid)
            if class_name:
                track.class_name = class_name
            if worker_name:
                track.worker_name = worker_name
            if helmet_number is not None:
                track.helmet_number = helmet_number
        else:
            track = ObjectTrack(self.next_id, centroid)
            track.class_name = class_name
            track.worker_name = worker_name
            track.helmet_number = helmet_number
            self.tracks[self.next_id] = track
            self.next_id += 1

    def _match_track(
        self, centroid: tuple[float, float], max_dist: float = 50.0
    ) -> int | None:
        best_id, best_dist = None, max_dist
        for tid, track in self.tracks.items():
            tc = track.get_centroid()
            d = np.linalg.norm(np.array(centroid) - np.array(tc))
            if d < best_dist:
                best_dist = d
                best_id = tid
        return best_id

    def age_all(self):
        to_delete = []
        for tid, track in self.tracks.items():
            track.age += 1
            if track.age > self.max_age:
                to_delete.append(tid)
        for tid in to_delete:
            log.debug("track_expired", track_id=tid)
            del self.tracks[tid]

    def get_active_tracks(self) -> list[ObjectTrack]:
        return list(self.tracks.values())
