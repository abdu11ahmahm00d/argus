import asyncio
import signal
import sys
from datetime import datetime
import yaml
import structlog

from comms.camera import Camera
from comms.serial_bridge import SerialBridge
from comms.telegram_bot import TelegramBot
from core.detection import Detector, Detection
from core.tracker import TrackerManager
from core.geometry import get_zone_name, draw_zones
from core.threat import ThreatStateMachine
from core.heatmap import HeatmapRenderer
from core.clahe import clahe_enhance

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
)
log = structlog.get_logger()


class AppContext:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
        self.camera: Camera | None = None
        self.detector: Detector | None = None
        self.tracker: TrackerManager | None = None
        self.fsm: ThreatStateMachine | None = None
        self.serial: SerialBridge | None = None
        self.telegram: TelegramBot | None = None
        self.heatmap: HeatmapRenderer | None = None
        self.armed = True
        self._running = True
        self._last_frame = None
        self._tracked_objects = []
        self._repeat_offenders: set[int] = set()

    def init_modules(self):
        cam_cfg = self.cfg["camera"]
        self.camera = Camera(
            cam_cfg["source"],
            cam_cfg["width"],
            cam_cfg["height"],
            cam_cfg["queue_maxsize"],
        )

        model_cfg = self.cfg["model"]
        self.detector = Detector(model_cfg["path"], model_cfg["confidence_threshold"])

        kal_cfg = self.cfg["kalman"]
        self.tracker = TrackerManager(
            kal_cfg["max_age"],
            kal_cfg["speed_threshold"],
            kal_cfg["predict_frames_ahead"],
        )

        thr_cfg = self.cfg["threat"]
        self.fsm = ThreatStateMachine(
            thr_cfg["max_occupancy"], thr_cfg["repeat_offender_limit"]
        )

        ser_cfg = self.cfg["serial"]
        self.serial = SerialBridge(ser_cfg["port"], ser_cfg["baud"], ser_cfg["timeout"])

        tel_cfg = self.cfg["telegram"]
        self.telegram = TelegramBot(tel_cfg["token"], tel_cfg["supervisor_id"])

        zones = self.cfg.get("zones", {})
        safe_zone = zones.get("outer_zone", [])
        danger_zone = zones.get("danger_zone", [])
        self.heatmap = HeatmapRenderer(safe_zone, danger_zone, self.cfg)

    async def arduino_health_check(self):
        log.info("checking_arduino")
        for attempt in range(3):
            ok = await self.serial.ping()
            if ok:
                log.info("arduino_online", attempt=attempt + 1)
                return True
            log.warning("arduino_ping_failed", attempt=attempt + 1)
            await asyncio.sleep(1)
        log.warning("arduino_unreachable — continuing without hardware")
        return False

    async def run(self):
        self.init_modules()
        await self.camera.start()
        await self.serial.connect()

        hw_ok = await self.arduino_health_check()

        self.fsm.register_callback(self._on_state_change)

        # Start coroutines
        await asyncio.gather(
            self.camera.capture_loop(),
            self.main_pipeline(),
            self.telegram.start_polling(),
            return_exceptions=True,
        )

    async def main_pipeline(self):
        zones = self.cfg.get("zones", {})
        safe_zone = zones.get("outer_zone", [])
        danger_zone = zones.get("danger_zone", [])

        log.info("pipeline_started", zones_configured=bool(safe_zone and danger_zone))

        while self._running:
            frame = await self.camera.get_frame()
            if frame is None:
                await asyncio.sleep(0.01)
                continue

            self._last_frame = frame

            if not self.armed:
                continue

            detections = await self.detector.detect(frame)
            self.tracker.age_all()

            for det in detections:
                self.tracker.update_or_create(
                    centroid=det.centroid,
                    class_name=det.class_name,
                )
                track = self._find_track(det.centroid)
                if track is None:
                    continue

                if (
                    det.class_name != "unknown"
                    and det.crop is not None
                    and det.crop.size > 0
                ):
                    enhanced = clahe_enhance(
                        det.crop,
                        self.cfg["clahe"]["clip_limit"],
                        self.cfg["clahe"]["tile_grid_size"],
                    )

                zone = get_zone_name(det.centroid, safe_zone, danger_zone)
                if zone == "outside":
                    continue

                self.fsm.evaluate(track, zone, danger_zone)

                self._repeat_offenders = {
                    t.track_id
                    for t in self.tracker.get_active_tracks()
                    if t.worker_name
                    and self.fsm.violation_count.get(t.worker_name, 0)
                    >= self.cfg["threat"]["repeat_offender_limit"]
                }

            self._tracked_objects = self.tracker.get_active_tracks()
            await asyncio.sleep(0)

    def _find_track(self, centroid):
        import numpy as np

        for t in self._tracked_objects:
            c = t.get_centroid()
            d = np.linalg.norm(np.array(centroid) - np.array([c[0], c[1]]))
            if d < 50:
                return t
        return None

    def _on_state_change(self, event):
        log.info("state_change", state=event.state, zone=event.zone_name)
        asyncio.create_task(self._dispatch_hardware(event))

    async def _dispatch_hardware(self, event):
        if not self.serial.connected:
            return

        if event.state == "INTERCEPT":
            await self.serial.send({"cmd": "BARRIER_DROP"})
            await self.serial.send({"cmd": "BUZZ", "duration": 2000})
            await self.serial.send({"cmd": "LED_RED", "mode": "on"})
            msg = f"🚨 Worker {event.worker_name} intercepted — "
            if event.time_to_entry:
                msg += f"predicted entry in {event.time_to_entry:.1f}s — "
            msg += "laser active"
            await self.telegram.send_alert(msg)

        elif event.state == "WARNING":
            await self.serial.send({"cmd": "LED_RED", "mode": "on"})
            msg = (
                f"⚠️ {event.worker_name} detected without protection — {event.zone_name}"
            )
            if self._last_frame is not None and self.heatmap:
                jpg = self.heatmap.get_snapshot(
                    self._last_frame,
                    self._tracked_objects,
                    event.state,
                    self._repeat_offenders,
                )
                await self.telegram.send_alert(msg, photo_bytes=jpg)
            else:
                await self.telegram.send_alert(msg)

        elif event.state == "AUTHORIZED":
            await self.serial.send({"cmd": "FLAG_RAISE"})
            await self.serial.send({"cmd": "LED_GREEN", "mode": "on"})
            await self.telegram.send_alert(
                f"✅ {event.worker_name} entered danger zone with helmet — "
                f"Occupancy: {event.occupancy}/{self.cfg['threat']['max_occupancy']}"
            )

        elif event.state == "MONITORING":
            await self.serial.send({"cmd": "LED_GREEN", "mode": "on"})

        elif event.state == "IDLE":
            await self.serial.send({"cmd": "RESET"})

    async def shutdown(self):
        self._running = False
        log.info("shutdown_started")
        try:
            await self.telegram.send_alert(
                f"⚫ ARGUS shutdown — {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception:
            pass
        if self.serial.connected:
            await self.serial.send({"cmd": "RESET"})
            await self.serial.close()
        await self.camera.stop()
        await self.telegram.stop()
        log.info("shutdown_complete")


async def main():
    app = AppContext()
    signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(app.shutdown()))
    try:
        await app.run()
    except Exception as e:
        log.error("fatal_error", error=str(e))
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
