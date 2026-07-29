from dataclasses import dataclass, field
from datetime import datetime
from transitions import Machine
import structlog
from core.tracker import ObjectTrack

log = structlog.get_logger()


class ThreatStateMachine:
    states = ["IDLE", "MONITORING", "WARNING", "INTERCEPT", "AUTHORIZED"]

    def __init__(self, max_occupancy: int = 2, repeat_limit: int = 3):
        self.max_occupancy = max_occupancy
        self.repeat_limit = repeat_limit
        self.violation_count: dict[str, int] = {}
        self.occupancy = 0
        self.escalation_flag = False
        self.last_event: SystemEvent | None = None
        self._no_detection_timer = 0
        self._on_transition_callbacks = []

        self.machine = Machine(
            model=self,
            states=ThreatStateMachine.states,
            initial="IDLE",
            auto_transitions=False,
        )

        self.machine.add_transition(
            "to_monitoring", "IDLE", "MONITORING", after="on_enter_monitoring"
        )
        self.machine.add_transition(
            "to_warning", ["IDLE", "MONITORING"], "WARNING", after="on_enter_warning"
        )
        self.machine.add_transition(
            "to_intercept", "WARNING", "INTERCEPT", after="on_enter_intercept"
        )
        self.machine.add_transition(
            "to_authorized",
            ["MONITORING", "WARNING"],
            "AUTHORIZED",
            after="on_enter_authorized",
        )
        self.machine.add_transition("to_idle", "*", "IDLE", after="on_enter_idle")
        self.machine.add_transition(
            "to_monitoring_from_authorized",
            "AUTHORIZED",
            "MONITORING",
            after="on_enter_monitoring",
        )
        self.machine.add_transition(
            "to_warning_from_intercept",
            "INTERCEPT",
            "WARNING",
            after="on_enter_warning",
        )

    def on_enter_idle(self):
        self.occupancy = 0
        log.info("state_idle")
        self._emit_event("IDLE")

    def on_enter_monitoring(self):
        log.info("state_monitoring")
        self._emit_event("MONITORING")

    def on_enter_warning(self):
        log.info("state_warning")
        self._emit_event("WARNING")

    def on_enter_intercept(self):
        log.info("state_intercept")
        self._emit_event("INTERCEPT")

    def on_enter_authorized(self):
        log.info("state_authorized")
        self._emit_event("AUTHORIZED")

    def _emit_event(self, state: str):
        self.last_event = SystemEvent(
            timestamp=datetime.now(),
            state=state,
            worker_name="",
            helmet_number=None,
            threat_score=0.0,
            zone_name="",
            time_to_entry=None,
            violation_count=0,
            occupancy=self.occupancy,
        )
        for cb in self._on_transition_callbacks:
            cb(self.last_event)

    def register_callback(self, cb):
        self._on_transition_callbacks.append(cb)

    def evaluate(self, track: ObjectTrack, zone: str, danger_polygon: list):
        centroid = track.get_centroid()
        speed = track.get_speed()
        score = ThreatScorer.score(track)

        if zone == "outside":
            return

        is_compliant = track.class_name == "capped"
        is_approaching = False
        time_to_entry = float("inf")

        if danger_polygon and speed > 1.0:
            predicted = track.predict()
            is_approaching = track.is_approaching_zone(predicted, danger_polygon)
            time_to_entry = track.time_to_zone_entry(
                (float(centroid[0]), float(centroid[1])),
                track.get_velocity(),
                danger_polygon,
            )

        track_key = track.worker_name or f"worker_{track.track_id}"
        if track.class_name == "uncapped":
            self.violation_count[track_key] = self.violation_count.get(track_key, 0) + 1
            if self.violation_count[track_key] >= self.repeat_limit:
                self.escalation_flag = True
        else:
            self.violation_count[track_key] = 0

        if zone == "danger" and is_compliant:
            self.occupancy += 1

        over_capacity = self.occupancy > self.max_occupancy

        if is_approaching and not is_compliant:
            if self.state != "INTERCEPT":
                self.to_intercept()
                self.last_event.time_to_entry = time_to_entry
        elif zone == "danger" and is_compliant:
            if self.state != "AUTHORIZED":
                self.to_authorized()
        elif zone == "safe" and not is_compliant:
            if self.state in ("IDLE", "MONITORING"):
                self.to_warning()
        elif zone == "safe" and is_compliant:
            if self.state == "IDLE":
                self.to_monitoring()

        self.last_event = SystemEvent(
            timestamp=datetime.now(),
            state=self.state,
            worker_name=track.worker_name or "",
            helmet_number=track.helmet_number,
            threat_score=score,
            zone_name=zone,
            time_to_entry=time_to_entry if time_to_entry != float("inf") else None,
            violation_count=self.violation_count.get(track_key, 0),
            occupancy=self.occupancy,
        )


class ThreatScorer:
    @staticmethod
    def score(
        track: ObjectTrack,
        safe_zone_area: float = 100000.0,
        max_expected_speed: float = 20.0,
    ) -> float:
        bbox_area = 0
        size_score = (
            min(bbox_area / safe_zone_area, 1.0) * 0.3 if safe_zone_area > 0 else 0
        )
        speed = track.get_speed()
        velocity_score = min(speed / max_expected_speed, 1.0) * 0.4
        compliance_score = (1.0 if track.class_name == "uncapped" else 0.0) * 0.3
        return size_score + velocity_score + compliance_score


@dataclass
class SystemEvent:
    timestamp: datetime
    state: str
    worker_name: str
    helmet_number: int | None
    threat_score: float
    zone_name: str
    time_to_entry: float | None
    violation_count: int
    occupancy: int
