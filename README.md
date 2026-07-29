# 🛡️ ARGUS — Autonomous Real-time Guard for Unsafe Sites

**ARGUS** is a computer vision safety enforcement system for construction sites. It detects whether workers are wearing safety helmets using YOLOv8, tracks their movement with Kalman filters, and triggers physical responses (LEDs, buzzer, barrier, laser) over Bluetooth to an Arduino Uno.

> **v1 (completed):** Ultrasonic sweep scanner with laser — a servo-mounted sonar that scans a field and pinpoints any object with a laser beam. Photos available on request.
>
> **v2 (this repo):** Camera-based YOLOv8 helmet detection over an overhead phone camera feed. Adds ML classification, predictive tracking, telemetry, and Telegram supervisor interface.

---

## System Pipeline

```
┌──────────────┐   WiFi    ┌──────────────┐   JSON    ┌─────────────┐
│  Phone (IP   │ ────────→ │  Laptop with  │ ────────→ │  Arduino    │
│  Webcam app) │  MJPEG    │  GTX 1080     │  Bluetooth │  Uno R3     │
│  overhead    │  stream   │  Python +     │  HC-05     │             │
└──────────────┘           │  YOLOv8       │  9600 baud │  ─── LED    │
                           │               │            │  ─── Buzzer │
                           │               │            │  ─── Laser  │
                           │               │            │  ─── Servos │
                           │               │            │  ─── Switch │
                           └──────────────┘            └──────┬──────┘
                                                              │
                                                              ▼
                                                     ┌─────────────────┐
                                                     │   Hardware      │
                                                     │   Responses     │
                                                     │   (LED/buzzer/  │
                                                     │    barrier/     │
                                                     │    laser/flag)  │
                                                     └─────────────────┘
                             ┌─────────────────┐
                             │   Telegram Bot  │
                             │   (supervisor   │
                             │    interface)   │
                             └─────────────────┘
```

### Per-Frame Pipeline

```
Camera frame → YOLOv8 detection → brain ROI extraction → CLAHE enhancement
    → class check (helmet/head/person) → Kalman tracker update
    → zone membership (safe/danger/outside) → threat state machine
    → Arduino serial command → Telegram alert → heatmap overlay
```

---

## Features

| Feature | Implementation |
|---|---|
| **Helmet detection** | YOLOv8n trained on Roboflow Hard Hat Workers (7,035 images, 3 classes) |
| **Zone enforcement** | Two configurable polygons — safe zone (green) and danger zone (red) |
| **CLAHE preprocessing** | Contrast-limited adaptive histogram equalisation for harsh lighting |
| **Kalman tracking** | Constant-velocity filter predicting position 15 frames ahead |
| **Predictive intercept** | Barrel drops BEFORE a non-compliant object enters the danger zone |
| **5-state FSM** | IDLE → MONITORING → WARNING → INTERCEPT → AUTHORIZED |
| **Bluetooth serial** | JSON commands over HC-05 at 9600 baud to Arduino |
| **Telegram bot** | Real-time alerts, `/heatmap` snapshots, `/status`, `/arm`/`/disarm` |
| **Repeat offender** | Auto-escalation after 3+ violations per worker |
| **Heatmap overlay** | Annotated camera feed with trails, velocity arrows, occupancy badges |
| **Hardware override** | Physical switch to disarm all responses instantaneously |
| **DC power** | 2×18650 + LM2596 buck converter → field-portable operation |

---

## Repository Structure

```
argus/
├── config/
│   └── config.yaml              ← All parameters (camera, model, serial, Telegram)
├── core/
│   ├── detection.py             ← YOLOv8 inference wrapper
│   ├── clahe.py                 ← CLAHE preprocessing pipeline
│   ├── tracker.py               ← Kalman filter + velocity prediction
│   ├── geometry.py              ← Zone polygon math (point-in-polygon, overlay)
│   ├── threat.py                ← 5-state FSM + threat scorer
│   └── heatmap.py               ← Annotated camera overlay renderer
├── comms/
│   ├── camera.py                ← Async IP Webcam frame capture
│   ├── serial_bridge.py         ← Async Bluetooth serial (JSON + ACK protocol)
│   └── telegram_bot.py          ← Supervisor bot with slash commands
├── arduino/
│   └── argus/
│       ├── argus.ino            ← Arduino firmware (command dispatcher)
│       └── protocol.h           ← Command constants + pin assignments
├── training/
│   ├── train.py                 ← YOLOv8 fine-tune entry point
│   ├── validate.py              ← Validation with mAP/precision/recall
│   └── download_dataset.py      ← Downloads Roboflow Hard Hat Workers dataset
├── scripts/
│   ├── calibrate.py             ← Click-to-set zone polygons on live feed
│   └── test_serial.py           ← Interactive Arduino command test tool
├── hardware/
│   ├── BOM.md                   ← Bill of materials with costs
│   └── wiring.md                ← Complete pin wiring guide
├── docs/
│   ├── hardware_spec.md         ← Full hardware specification and assembly
│   └── software_guide.md        ← Software phases and validation
├── dashboard/                   ← Three.js live 3D radar view (optional extension)
├── workers/                     ← ArcFace embeddings (optional face recognition)
├── logs/                        ← Session log output
├── main.py                      ← Single entry point — starts everything
├── requirements.txt             ← Python dependencies
└── pyproject.toml               ← Project metadata
```

---

## Quick Start

### 1. Hardware Requirements

See [hardware/BOM.md](hardware/BOM.md) for the full bill of materials. Minimum:

| Component | Purpose |
|---|---|
| Arduino Uno R3 | Executes physical responses |
| HC-05 Bluetooth module | Wireless laptop ↔ Arduino |
| 2× MG90S micro servos | Barrier arm + green clearance flag |
| Red LED (LilyPad) | Violation indicator |
| Green LED | Compliance indicator |
| Active buzzer | Audible alarm |
| Laser module (650nm) | Red boundary line on intercept |
| HC-SR04 ultrasonic | Secondary speed sensor |
| 2× 18650 + LM2596 buck | Field power supply |
| Phone with IP Webcam | Overhead camera feed |

### 2. Software Setup

```bash
# Create environment
uv init argus
uv add ultralytics easyocr opencv-python numpy filterpy
uv add pyserial-asyncio pydantic pyyaml transitions structlog python-telegram-bot
uv add fastapi uvicorn websockets

# Or use pip
pip install -r requirements.txt
```

### 3. Download Dataset

```bash
python training/download_dataset.py
```

You need a free Roboflow account and API key. The script downloads the **Hard Hat Workers** dataset (7,035 images, YOLOv8 format) into `training/dataset/`.

### 4. Train Model

```bash
python training/train.py
```

Expected: ~30 minutes on a GTX 1080, 50 epochs, mAP50 > 0.75.

### 5. Arduino Firmware

1. Open `arduino/argus/argus.ino` in Arduino IDE
2. Install library: **ArduinoJson** by Benoit Blanchon (v7.x)
3. Select board: Arduino Uno
4. Upload to Arduino

### 6. Configure

Edit `config/config.yaml`:

```yaml
camera:
  source: "http://192.168.1.5:8080/video"  # Your phone's IP Webcam URL

serial:
  port: "COM7"  # Your HC-05 COM port

telegram:
  token: "YOUR_BOT_TOKEN"     # From @BotFather
  supervisor_id: 123456789     # Your Telegram user ID
```

### 7. Calibrate Zones

```bash
python scripts/calibrate.py
```

Click 4 corners of outer tape square → Enter → click 4 corners of inner tape → Enter.

### 8. Run

```bash
python main.py
```

---

## How It Works

### Zone System

Two physical tape squares on the floor define the visual boundaries:
- **Outer square** — safe zone (workers can roam freely)
- **Inner square** — danger zone (crane swing radius, restricted)

The calibration tool maps these to polygon coordinates in `config.yaml`.

### Detection Pipeline

| Step | Module | What Happens |
|---|---|---|
| 1 | `camera.py` | Async frame capture from IP Webcam at 30 FPS |
| 2 | `detection.py` | YOLOv8 inference on 640×640 input |
| 3 | `clahe.py` | CLAHE applied to each detection crop for OCR |
| 4 | `tracker.py` | Kalman filter updates position + velocity |
| 5 | `geometry.py` | Checks if centroid is inside safe/danger zone |
| 6 | `threat.py` | Evaluates state, transitions FSM, scores threat |
| 7 | `serial_bridge.py` | Sends JSON command to Arduino over Bluetooth |
| 8 | `telegram_bot.py` | Sends alert with confidence + zone + photo |
| 9 | `heatmap.py` | Draws all overlays on frame for display/Telegram |

### State Machine

```
                ┌────────────────────────────────────┐
                │               IDLE                  │
                └──┬────────────────────────────┬────┘
        helmeted  │                    non-helmeted │
           ┌──────▼──────┐              ┌──────────▼────┐
           │  MONITORING  │              │   WARNING     │
           └──┬───────────┘              └──┬────────────┘
  crosses into │                  approaches │ danger zone
  danger zone  │                          ┌──▼──────────┐
     ┌────────▼───────┐                  │  INTERCEPT   │
     │   AUTHORIZED   │                  └──┬──────────┘
     └────────┬───────┘     stops/safe │
              │              ┌─────────▼──────┐
              └──────────────►    IDLE/TBD     │
                             └────────────────┘
```

### Arduino Command Protocol

Commands are JSON strings sent over HC-05 Bluetooth at 9600 baud:

```json
{"cmd": "BARRIER_DROP"}              // Servo 1 → 0°, laser ON
{"cmd": "BARRIER_RAISE"}            // Servo 1 → 90°, laser OFF
{"cmd": "FLAG_RAISE"}              // Servo 2 → 90° (green flag up)
{"cmd": "FLAG_LOWER"}              // Servo 2 → 0° (flag down)
{"cmd": "LASER_ON"}                // Laser module ON
{"cmd": "LASER_OFF"}               // Laser module OFF
{"cmd": "BUZZ", "duration": 1000}  // Buzzer for 1 second
{"cmd": "LED_RED", "mode": "on"}   // Red LED ON
{"cmd": "LED_GREEN", "mode": "on"} // Green LED ON
{"cmd": "LED_OFF", "target": "all"}// All LEDs OFF
{"cmd": "PING"}                    // Health check → ACK with uptime
{"cmd": "RESET"}                   // All outputs to rest state
```

Arduino replies with ACK:
```json
{"ack": "OK", "cmd": "BARRIER_DROP", "uptime": 48291}
```

### Telegram Bot Commands

| Command | Response |
|---|---|
| `/status` | Current zone occupancy and FSM state |
| `/heatmap` | Annotated camera snapshot |
| `/compliance` | Helmet compliance percentage this session |
| `/workers` | Tracked workers and their zones |
| `/arm` | Enable system responses |
| `/disarm` | Disable system responses |
| `/help` | All available commands |

---

## Demo Script

> Estimated: 6 acts × 60–90 seconds = ~7 minutes.

| Act | Action | System Response |
|---|---|---|
| 1 | Show setup | Two zones visible, FSM in IDLE |
| 2 | Place plain chess piece in safe zone | WARNING → Telegram alert with confidence |
| 3 | Roll marble toward danger zone | INTERCEPT → barrier drops, laser on, buzzer |
| 4 | Same piece ×3 violations | ESCALATION notification |
| 5 | Move helmeted piece into danger zone | AUTHORIZED → green flag, green LED |
| 6 | `/heatmap` → `/status` → `/disarm` → `/arm` | All remote commands work |

See [`docs/software_guide.md`](docs/software_guide.md) for the full demo runbook.

---

## Training Your Own Dataset

The system can be retrained for any object detection task. The Roboflow Hard Hat Workers dataset is the default, but you can substitute your own:

### Custom Dataset (e.g. Jenga blocks + Sprite cap helmets)

This was the original ARGUS prototype concept — using Jenga blocks as construction workers and Sprite caps as safety helmets. To replicate:

1. Collect ~25+ photos of Jenga blocks with Sprite cap on + ~25+ without
2. Upload to [Roboflow](https://roboflow.com) and annotate (2 classes: `capped`, `uncapped`)
3. Export in YOLOv8 format
4. Replace `training/dataset/data.yaml` with yours
5. Update `config.yaml` class mapping to match
6. Run `python training/train.py`

```yaml
# config.yaml for custom dataset
model:
  classes:
    capped: 0    # Jenga block with Sprite cap
    uncapped: 1  # Bare Jenga block
```

### Expected Training Performance

| Hardware | Resolution | Epochs | Time | Expected mAP50 |
|---|---|---|---|---|
| GTX 1080 | 640×640 | 50 | ~30 min | > 0.75 |
| RTX 3060 | 640×640 | 50 | ~20 min | > 0.80 |
| RTX 4090 | 640×640 | 50 | ~8 min | > 0.85 |

---

## Performance

| Metric | Value |
|---|---|
| Detection FPS (GTX 1080) | ~30 FPS |
| Full pipeline latency | ~500ms–2s |
| Frame resolution | 640×480 |
| YOLO input size | 640×640 |
| Bluetooth baud rate | 9600 |
| Command payload size | ~30 bytes |
| Kalman prediction | 15 frames ahead |
| Zone calibration | 4-click per polygon |

---

## v1 → v2 Evolution

**v1 (Ultrasonic Scanner):** An Arduino sweep scanner using HC-SR04 on a servo to scan a 180° field. When an object is detected, a laser pinpoints its location and a buzzer sounds. No camera, no ML, no classification.

**v2 (Camera + YOLO):** Adds an overhead camera feed, GPU-accelerated YOLOv8 detection, CLAHE preprocessing, Kalman predictive tracking, zone-based state machine, Bluetooth serial to Arduino, real-time Telegram alerts, and heatmap overlays. The v1 ultrasonic sensor remains as a secondary speed/distance sensor.

Photos of the v1 hardware build are available on request.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Citation

If you use ARGUS in academic work:

```bibtex
@misc{mahmood2026argus,
  title = {ARGUS: Autonomous Real-time Guard for Unsafe Sites},
  author = {Mahmood, Abdullah},
  year = {2026},
  howpublished = {\url{https://github.com/abdu11ahmahm00d/argus}}
}
```
