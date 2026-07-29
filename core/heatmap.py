import io
import cv2
import numpy as np
import structlog
from core.geometry import draw_zones, get_zone_centroid, is_inside_zone
from core.tracker import ObjectTrack

log = structlog.get_logger()

COLOR_MAP = {
    "capped": (0, 255, 0),
    "uncapped": (0, 0, 255),
    "unknown": (128, 128, 128),
}
REPEAT_OFFENDER_COLOR = (0, 165, 255)
MARBLE_COLOR = (128, 0, 128)
DANGER_COMPLIANT_COLOR = (255, 0, 0)


class HeatmapRenderer:
    def __init__(self, safe_zone: list, danger_zone: list, config: dict):
        self.safe_zone = safe_zone
        self.danger_zone = danger_zone
        self.config = config

    def draw(
        self,
        frame: np.ndarray,
        tracks: list[ObjectTrack],
        fsm_state: str,
        repeat_offenders: set[int] | None = None,
    ) -> np.ndarray:
        display = draw_zones(frame.copy(), self.safe_zone, self.danger_zone)

        for track in tracks:
            centroid = track.get_centroid()
            cx, cy = int(centroid[0]), int(centroid[1])

            is_repeat = repeat_offenders and track.track_id in repeat_offenders
            if is_repeat:
                color = REPEAT_OFFENDER_COLOR
            elif track.class_name == "capped":
                in_danger = (
                    is_inside_zone((cx, cy), self.danger_zone)
                    if self.danger_zone
                    else False
                )
                color = DANGER_COMPLIANT_COLOR if in_danger else COLOR_MAP["capped"]
            else:
                color = COLOR_MAP.get(track.class_name, COLOR_MAP["unknown"])

            for i, pos in enumerate(track.history[-30:]):
                alpha = i / len(track.history)
                trail_color = tuple(int(c * alpha) for c in color)
                cv2.circle(display, (int(pos[0]), int(pos[1])), 2, trail_color, -1)

            cv2.circle(display, (cx, cy), 6, color, -1)
            cv2.circle(display, (cx, cy), 6, (255, 255, 255), 1)

            vx, vy = track.get_velocity()
            speed = track.get_speed()
            if speed > 1.0:
                scale = min(speed / 2.0, 30.0)
                end_x = int(cx + vx * scale)
                end_y = int(cy + vy * scale)
                cv2.arrowedLine(
                    display, (cx, cy), (end_x, end_y), (255, 255, 255), 1, tipLength=0.3
                )

            if speed > 1.0:
                pred = track.predict()
                px, py = int(pred[0]), int(pred[1])
                ghost = display.copy()
                cv2.circle(ghost, (px, py), 6, color, -1)
                display = cv2.addWeighted(ghost, 0.5, display, 0.5, 0)

            label = f"#{track.track_id}"
            if track.worker_name:
                label += f" {track.worker_name}"
            if track.class_name == "uncapped":
                label += " ⚠️"
            cv2.putText(
                display,
                label,
                (cx + 10, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1,
            )

        if self.danger_zone:
            dz_centroid = get_zone_centroid(self.danger_zone)
            danger_count = sum(
                1
                for t in tracks
                if is_inside_zone(
                    (int(t.get_centroid()[0]), int(t.get_centroid()[1])),
                    self.danger_zone,
                )
            )
            max_occ = self.config.get("threat", {}).get("max_occupancy", 2)
            occ_text = f"Danger zone: {danger_count}/{max_occ}"
            cv2.putText(
                display,
                occ_text,
                (dz_centroid[0] - 40, dz_centroid[1]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        cv2.putText(
            display,
            f"State: {fsm_state}",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )

        return display

    def get_snapshot(
        self,
        frame: np.ndarray,
        tracks: list[ObjectTrack],
        fsm_state: str,
        repeat_offenders: set[int] | None = None,
    ) -> bytes:
        annotated = self.draw(frame, tracks, fsm_state, repeat_offenders)
        success, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            return b""
        return io.BytesIO(buf).getvalue()
