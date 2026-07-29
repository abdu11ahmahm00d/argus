## 7. Software Environment

### Project Name and Folder Structure

```
argus/
├── config/
│   └── config.yaml              ← all parameters
├── core/
│   ├── detection.py             ← YOLOv8 helmet inference
│   ├── ocr.py                   ← EasyOCR number reading
│   ├── clahe.py                 ← preprocessing pipeline
│   ├── tracker.py               ← Kalman filter
│   ├── geometry.py              ← zone polygon math
│   ├── threat.py                ← state machine + scorer
│   ├── heatmap.py               ← worker position overlay
│   └── face.py                  ← RetinaFace + ArcFace entry
├── comms/
│   ├── camera.py                ← IP Webcam reader
│   ├── serial_bridge.py         ← Arduino Bluetooth serial
│   └── telegram_bot.py          ← bot + slash commands
├── dashboard/
│   ├── index.html               ← Three.js live view
│   └── js/
│       └── main.js              ← heatmap + overlays
├── arduino/
│   └── argus/
│       ├── argus.ino            ← main sketch
│       └── protocol.h           ← command constants
├── training/
│   ├── train.py                 ← YOLOv8 fine-tune script
│   ├── validate.py              ← mAP + confusion matrix
│   └── dataset/                 ← Roboflow export here
│       ├── data.yaml
│       ├── train/
│       ├── valid/
│       └── test/
├── scripts/
│   ├── calibrate.py             ← click-to-set zone polygons
│   ├── test_serial.py           ← manual Arduino command test
│   └── enroll_worker.py         ← ArcFace face enrollment
├── workers/
│   └── embeddings.pkl           ← ArcFace stored embeddings
├── logs/
│   └── session.log              ← structured session log
├── main.py                      ← single entry point
└── requirements.txt
```

### Install Order

```
Step 1 — Python environment
uv init argus
uv add ultralytics easyocr opencv-python numpy
uv add filterpy insightface onnxruntime-gpu
uv add fastapi uvicorn websockets
uv add pyserial-asyncio pydantic pyyaml
uv add transitions structlog python-telegram-bot

Step 2 — Arduino IDE Libraries
Open Arduino IDE → Tools → Manage Libraries
Install: ArduinoJson by Benoit Blanchon (v7.x)
Install: Servo (built-in — no install needed)
SoftwareSerial (built-in — no install needed)

Step 3 — Telegram Bot Setup
Open Telegram → search @BotFather
/newbot → follow prompts → copy bot token
Save token to config.yaml
Add your Telegram user ID to config.yaml as supervisor_id

Step 4 — Phone Camera
Install IP Webcam app (Android, free)
Open → Start Server → note IP:PORT shown on screen
(e.g. 192.168.1.5:8080)
Add to config.yaml under camera.source

Step 5 — Bluetooth
Power Arduino with HC-05 connected
Laptop Bluetooth settings → scan → pair HC-05
Default PIN: 1234
Note assigned COM port → add to config.yaml

Step 6 — YOLOv8 Dataset
Go to roboflow.com/universe
Search: "Hard Hat Workers"
Download in YOLOv8 format → extract to training/dataset/
Confirm data.yaml inside dataset folder
```

---

## 8. Phase 1 — Camera + Zone Calibration

**Goal:** Camera reads live frames. Two zone polygons defined and saved.

### Hardware steps
- Open IP Webcam on phone, press Start Server
- Confirm laptop and phone on same WiFi network
- Note IP address shown in IP Webcam app

### Software steps

**`comms/camera.py`**
- [ CODE PLACEHOLDER ] `cv2.VideoCapture(source_url)` opens phone stream
- [ CODE PLACEHOLDER ] Async frame capture loop, populates `asyncio.Queue(maxsize=3)`
- [ CODE PLACEHOLDER ] Drops oldest frame if queue full — keeps pipeline real-time
- [ CODE PLACEHOLDER ] Resizes all frames to 640×480 on capture
- [ CODE PLACEHOLDER ] Returns raw BGR numpy array per frame

**`scripts/calibrate.py`**
- [ CODE PLACEHOLDER ] Opens live camera feed in OpenCV window
- [ CODE PLACEHOLDER ] Prompts: "Click 4 corners of OUTER tape square, press Enter"
- [ CODE PLACEHOLDER ] Records 4 mouse click coordinates → outer_zone polygon
- [ CODE PLACEHOLDER ] Prompts: "Click 4 corners of INNER tape square, press Enter"
- [ CODE PLACEHOLDER ] Records 4 mouse click coordinates → danger_zone polygon
- [ CODE PLACEHOLDER ] Draws both polygons overlaid on frame for visual confirmation
- [ CODE PLACEHOLDER ] Saves both polygons to `config/config.yaml` on keypress S

**`core/geometry.py`**
- [ CODE PLACEHOLDER ] `is_inside_zone(point, polygon)` using `cv2.pointPolygonTest`
- [ CODE PLACEHOLDER ] `get_zone_name(point)` returns "danger", "safe", or "outside"
- [ CODE PLACEHOLDER ] `draw_zones(frame)` draws semi-transparent overlays:
  - Safe zone: green fill, 20% opacity, green border
  - Danger zone: red fill, 20% opacity, red border
- [ CODE PLACEHOLDER ] `get_zone_centroid(polygon)` for heatmap zone labeling

### Validation test
Run `calibrate.py`. Click outer tape corners. Click inner tape corners. Both polygons should appear as colored overlays on the live feed. Place a chess piece inside inner square — confirm `is_inside_zone` returns true for danger zone. Place piece between squares — confirm returns true for safe zone only.

---

## 9. Phase 2 — YOLOv8 Helmet Detection

**Goal:** Every detected person classified as helmeted or non-helmeted in real time.

### Dataset
Hard Hat Workers Dataset from Roboflow Universe — 7,035 labeled images, 3 classes: `helmet`, `person`, `head` (person without helmet). Free download, YOLOv8 format. Zero photos to collect.

### Software steps

**`training/train.py`**
- [ CODE PLACEHOLDER ] Load `data.yaml` from dataset folder
- [ CODE PLACEHOLDER ] `YOLO('yolov8n.pt').train(data='training/dataset/data.yaml', epochs=50, imgsz=640, device=0)`
- [ CODE PLACEHOLDER ] Model saved to `training/runs/detect/train/weights/best.pt`
- [ CODE PLACEHOLDER ] Expected training time: ~30 minutes on GTX 1080

**`training/validate.py`**
- [ CODE PLACEHOLDER ] Load best.pt, run validation on test split
- [ CODE PLACEHOLDER ] Print mAP50, mAP50-95, confusion matrix per class
- [ CODE PLACEHOLDER ] Target: mAP50 > 0.75 before proceeding

**`core/detection.py`**
- [ CODE PLACEHOLDER ] Load trained model from config path
- [ CODE PLACEHOLDER ] `detect(frame)` → runs inference, returns list of Detection objects
- [ CODE PLACEHOLDER ] Each Detection: `bbox, class_name, confidence, centroid`
- [ CODE PLACEHOLDER ] Filter confidence < 0.45 → discard
- [ CODE PLACEHOLDER ] `class_name` maps: "helmet" → compliant, "head" → non-compliant, "person" → unknown
- [ CODE PLACEHOLDER ] Runs in ThreadPoolExecutor to avoid blocking asyncio loop

### Validation test
Run detection standalone on live camera feed. Hold a chess piece with paper circle under camera — bounding box with "helmet" label should appear. Hold plain piece — "head" label. Confirm confidence scores print correctly. Confirm GPU is being used (check task manager or `nvidia-smi`).

---

## 10. Phase 3 — EasyOCR Helmet Number Reading

**Goal:** Read the number written on the paper helmet circle. Map to worker name.

### Software steps

**`core/ocr.py`**
- [ CODE PLACEHOLDER ] `easyocr.Reader(['en'])` initialised once at startup (slow first load)
- [ CODE PLACEHOLDER ] `read_helmet_number(frame, bbox)` function:
  - Crop top 40% of bounding box (where paper circle is)
  - Pass crop to `reader.readtext(crop)`
  - Filter results: keep only single digit or double digit integers
  - Return first valid integer found, or None if unreadable
- [ CODE PLACEHOLDER ] `get_worker_name(number)` looks up number in `config.yaml` workers dict
- [ CODE PLACEHOLDER ] Returns "Unknown Worker" if number not in config

**`config/config.yaml` workers section**
```yaml
workers:
  1: "Karim Ahmed"
  2: "Rahim Mia"
  3: "Jamal Hossain"
  4: "Faruk Islam"
  5: "Sumon Das"
```

### Validation test
Hold helmeted chess piece under camera. Console should print: `Helmet detected — Number: 3 — Worker: Jamal Hossain`. Hold piece at slight angle — confirm OCR still reads correctly. Hold non-helmeted piece — OCR should return None, no name lookup attempted.

---

## 11. Phase 4 — CLAHE Preprocessing Pipeline

**Goal:** Improve helmet crop quality under harsh or uneven lighting before OCR and ArcFace.

### What CLAHE does
CLAHE (Contrast Limited Adaptive Histogram Equalization) applied to the L channel of LAB colorspace enhances local contrast without distorting colors. Improves OCR accuracy on shadowed helmet tops and face recognition in dim storage room conditions.

### Software steps

**`core/clahe.py`**
- [ CODE PLACEHOLDER ] `clahe_enhance(crop_bgr)` function:
  - Convert BGR crop to LAB colorspace: `cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)`
  - Split channels: `L, A, B = cv2.split(lab)`
  - Apply CLAHE to L channel: `clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))`
  - Merge channels back: `cv2.merge([L_enhanced, A, B])`
  - Convert back to BGR: `cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)`
  - Return enhanced BGR crop
- [ CODE PLACEHOLDER ] Applied to helmet crop BEFORE OCR read
- [ CODE PLACEHOLDER ] Applied to face crop BEFORE ArcFace embedding generation
- [ CODE PLACEHOLDER ] `clipLimit` and `tileGridSize` configurable in `config.yaml`

### Validation test
Take a phone photo of a numbered paper in low light. Run `clahe_enhance()` and display side by side with original. Number should be visibly clearer in enhanced version. Then test OCR accuracy on both — enhanced version should have higher read rate.

---

## 12. Phase 5 — Kalman Tracker + Marble Demo

**Goal:** Track every object's position and velocity. Predict zone-entry for marble and approaching chess pieces.

### Why the marble
Chess pieces are placed by hand — no continuous movement for Kalman to track velocity on. The marble rolls continuously, giving Kalman a real velocity vector to compute. This is the demo moment that proves the prediction layer is real.

### Software steps

**`core/tracker.py`**
- [ CODE PLACEHOLDER ] `filterpy.kalman.KalmanFilter` with state `[x, y, vx, vy]`
- [ CODE PLACEHOLDER ] Observation matrix maps `[x, y]` centroid to state vector
- [ CODE PLACEHOLDER ] Constant velocity motion model — F matrix standard 4-state CV model
- [ CODE PLACEHOLDER ] Process noise Q — tuned so tracker follows fast marble movement
- [ CODE PLACEHOLDER ] Measurement noise R — tuned for camera resolution
- [ CODE PLACEHOLDER ] `update(centroid)` — feeds detection into filter each frame
- [ CODE PLACEHOLDER ] `predict()` — returns predicted position N frames ahead (config: 0.5s)
- [ CODE PLACEHOLDER ] `get_velocity()` — returns `[vx, vy]` in pixels/frame
- [ CODE PLACEHOLDER ] `get_speed()` — returns scalar speed magnitude
- [ CODE PLACEHOLDER ] `is_approaching_zone(predicted_pos, danger_polygon)` — bool
- [ CODE PLACEHOLDER ] `time_to_zone_entry(pos, velocity, danger_polygon)` — returns float seconds
- [ CODE PLACEHOLDER ] Track age counter — resets tracker if no detection for `max_age` frames
- [ CODE PLACEHOLDER ] Speed threshold flag — `is_running()` returns True if speed > config threshold

**Dashboard overlay additions in `core/geometry.py`**
- [ CODE PLACEHOLDER ] Draw current centroid dot per tracked object
- [ CODE PLACEHOLDER ] Draw velocity vector arrow from centroid (scaled)
- [ CODE PLACEHOLDER ] Draw predicted position as ghost dot (50% opacity)
- [ CODE PLACEHOLDER ] Draw trail of last 30 frame positions as fading line
- [ CODE PLACEHOLDER ] Display time-to-zone-entry countdown text near object

### Validation test
Roll marble from outside outer tape toward inner tape. Dashboard should show:
- Centroid dot following marble
- Velocity arrow pointing ahead of marble
- Ghost dot 0.5s ahead of actual position
- Time-to-zone countdown decreasing
- At predicted entry — INTERCEPT state fires before marble physically crosses inner tape

Test with slow roll: time-to-entry should be larger, response fires earlier relatively.
Test with fast roll: time-to-entry smaller, confirms speed detection works.

---

## 13. Phase 6 — Threat State Machine

**Goal:** Single source of truth for system state. All modules read from it, only pipeline writes to it.

### Five States

```
IDLE        → No detections anywhere. System armed. All LEDs off.
MONITORING  → Worker in safe zone WITH helmet. Green LED soft pulse. No alerts.
WARNING     → Worker in safe zone WITHOUT helmet. Yellow LED. Telegram alert.
INTERCEPT   → Non-compliant object approaching danger zone.
              Kalman predicted entry within threshold. Full response.
AUTHORIZED  → Compliant worker (helmet on) crossing into danger zone.
              Green LED. Green flag. Telegram notification.
```

### Transitions

```
IDLE        → MONITORING   : helmeted worker detected in safe zone
IDLE        → WARNING      : non-helmeted worker detected in safe zone
MONITORING  → WARNING      : worker removes helmet mid-session
MONITORING  → AUTHORIZED   : helmeted worker crosses into danger zone
WARNING     → INTERCEPT    : non-compliant worker Kalman-predicted to enter danger zone
WARNING     → IDLE         : worker exits outer perimeter
INTERCEPT   → WARNING      : object stops or changes direction away from zone
INTERCEPT   → IDLE         : object exits outer perimeter
AUTHORIZED  → MONITORING   : worker exits danger zone back to safe zone
ANY         → IDLE         : no detections for 5 consecutive seconds
```

### Software steps

**`core/threat.py`**
- [ CODE PLACEHOLDER ] `transitions` library FSM with 5 states and all transitions above
- [ CODE PLACEHOLDER ] Each state has `on_enter_` callback that triggers appropriate hardware response
- [ CODE PLACEHOLDER ] `ThreatScorer.score(detection, track)` → float 0.0–1.0
  - size_score = bbox_area / safe_zone_area × 0.3
  - velocity_score = speed / max_expected_speed × 0.4
  - compliance_score = 1.0 if no helmet, 0.0 if helmet × 0.3
- [ CODE PLACEHOLDER ] Repeat offender tracker: dict mapping worker name to violation count
- [ CODE PLACEHOLDER ] If violation_count[worker] >= 3 → escalation flag set
- [ CODE PLACEHOLDER ] Zone occupancy counter: int tracking helmeted workers inside danger zone
- [ CODE PLACEHOLDER ] Over-capacity flag: True when occupancy > config max_occupancy
- [ CODE PLACEHOLDER ] `SystemEvent` dataclass emitted on each state transition:
  - timestamp, state, worker_name, helmet_number, threat_score,
  - zone_name, time_to_entry, violation_count, occupancy

---

## 14. Phase 7 — Arduino Firmware + Serial Bridge

**Goal:** Python sends JSON commands over Bluetooth. Arduino executes instantly.

### Arduino Firmware

**`arduino/argus/protocol.h`**
- [ CODE PLACEHOLDER ] `#define CMD_BARRIER_DROP "BARRIER_DROP"`
- [ CODE PLACEHOLDER ] `#define CMD_BARRIER_RAISE "BARRIER_RAISE"`
- [ CODE PLACEHOLDER ] `#define CMD_FLAG_RAISE "FLAG_RAISE"`
- [ CODE PLACEHOLDER ] `#define CMD_FLAG_LOWER "FLAG_LOWER"`
- [ CODE PLACEHOLDER ] `#define CMD_LASER_ON "LASER_ON"`
- [ CODE PLACEHOLDER ] `#define CMD_LASER_OFF "LASER_OFF"`
- [ CODE PLACEHOLDER ] `#define CMD_BUZZ "BUZZ"`
- [ CODE PLACEHOLDER ] `#define CMD_LED_RED "LED_RED"`
- [ CODE PLACEHOLDER ] `#define CMD_LED_GREEN "LED_GREEN"`
- [ CODE PLACEHOLDER ] `#define CMD_LED_OFF "LED_OFF"`
- [ CODE PLACEHOLDER ] `#define CMD_PING "PING"`
- [ CODE PLACEHOLDER ] `#define CMD_RESET "RESET"`

**`arduino/argus/argus.ino`**
- [ CODE PLACEHOLDER ] `SoftwareSerial btSerial(10, 11)` — Bluetooth on pins 10/11
- [ CODE PLACEHOLDER ] `Servo servo1, servo2` attached to pins 9, 6
- [ CODE PLACEHOLDER ] All pin modes set in `setup()`
- [ CODE PLACEHOLDER ] `loop()` reads btSerial for incoming JSON, parses with ArduinoJson
- [ CODE PLACEHOLDER ] Switch-case on `cmd` field dispatches to handler functions
- [ CODE PLACEHOLDER ] `handleBarrierDrop()` → `servo1.write(0)` + laser on
- [ CODE PLACEHOLDER ] `handleBarrierRaise()` → `servo1.write(90)` + laser off
- [ CODE PLACEHOLDER ] `handleFlagRaise()` → `servo2.write(90)`
- [ CODE PLACEHOLDER ] `handleFlagLower()` → `servo2.write(0)`
- [ CODE PLACEHOLDER ] `handleBuzz(duration_ms)` → buzzer on for duration
- [ CODE PLACEHOLDER ] `handleLedRed(state)` → red LED on/off/blink
- [ CODE PLACEHOLDER ] `handleLedGreen(state)` → green LED on/off/blink
- [ CODE PLACEHOLDER ] `handleReset()` → all outputs off, servos to rest position
- [ CODE PLACEHOLDER ] `handlePing()` → sends ACK JSON with uptime
- [ CODE PLACEHOLDER ] Switch pin 2 checked in loop — if LOW → skip all outputs (hardware disarm)

### Command JSON Schema

```json
{"cmd": "BARRIER_DROP"}
{"cmd": "BARRIER_RAISE"}
{"cmd": "FLAG_RAISE"}
{"cmd": "FLAG_LOWER"}
{"cmd": "LASER_ON"}
{"cmd": "LASER_OFF"}
{"cmd": "BUZZ", "duration": 1000}
{"cmd": "LED_RED", "mode": "blink", "count": 3}
{"cmd": "LED_GREEN", "mode": "on"}
{"cmd": "LED_OFF", "target": "all"}
{"cmd": "PING"}
{"cmd": "RESET"}
```

### ACK Response Schema

```json
{"ack": "OK", "cmd": "BARRIER_DROP", "uptime": 48291}
{"ack": "ERR", "reason": "servo_fault"}
```

### Python Serial Bridge

**`comms/serial_bridge.py`**
- [ CODE PLACEHOLDER ] `pyserial-asyncio` opens Bluetooth COM port at 9600 baud
- [ CODE PLACEHOLDER ] Async `send(command_dict)` coroutine — serializes to JSON + newline, writes
- [ CODE PLACEHOLDER ] Async `read_ack()` — waits for ACK with 200ms timeout
- [ CODE PLACEHOLDER ] Command queue — prevents simultaneous sends
- [ CODE PLACEHOLDER ] Reconnection loop — retries every 5s on disconnect
- [ CODE PLACEHOLDER ] All sent commands + ACKs logged via structlog

**`scripts/test_serial.py`**
- [ CODE PLACEHOLDER ] Interactive terminal: type any command JSON → sends to Arduino → prints ACK
- [ CODE PLACEHOLDER ] Preset shortcut keys: B=barrier drop, R=reset, L=laser on, etc.

### Validation test
Flash argus.ino to Arduino. Open test_serial.py. Send `{"cmd":"PING"}` — Arduino replies with uptime. Send `{"cmd":"BARRIER_DROP"}` — servo 1 rotates to 0°, laser turns on. Send `{"cmd":"FLAG_RAISE"}` — servo 2 rotates to 90°. Send `{"cmd":"RESET"}` — everything returns to rest. Send `{"cmd":"BUZZ","duration":500}` — buzzer sounds for 500ms. Confirm ALL commands work before proceeding. Nothing else is built until this validation passes.

---

## 15. Phase 8 — Telegram Bot + Slash Commands

**Goal:** Supervisor command interface. Real-time alerts. Remote arm/disarm.

### Bot Setup
```
Open Telegram → @BotFather → /newbot → follow prompts
Copy bot token to config.yaml
Open @userinfobot → copy your numeric user ID
Add user ID to config.yaml as supervisor_id
Test: send /start to your new bot — confirm it responds
```

### Automatic Alert Messages

| Trigger | Message Format |
|---|---|
| Non-compliant in safe zone | `⚠️ Worker #3 (Jamal Hossain) detected without helmet — Safe Zone — 14:23:07 [YOLOv8: 94%]` |
| Zone intercept | `🚨 Worker #3 (Jamal Hossain) intercepted — predicted entry in 4.2s — no helmet — laser active` |
| Compliant zone entry | `✅ Worker #2 (Rahim Mia) entered crane zone with helmet — 14:25:33 — Occupancy: 1/2` |
| Repeat offender | `🔴 ESCALATION — Worker #3 (Jamal Hossain) — 3rd violation this session` |
| Over capacity | `ℹ️ Worker #5 (Sumon Das) entered crane zone — Occupancy: 3/2 — OVER CAPACITY` |
| Speed alert | `⚡ Fast movement detected near danger zone — 2.3× normal speed — 14:31:44` |
| System armed | `🟢 ARGUS armed — session started — 09:00:00` |
| System disarmed | `⚫ ARGUS disarmed — 17:30:00` |
| Entry log | `📥 Worker #1 (Karim Ahmed) entered site — 08:57:23` |
| Exit log | `📤 Worker #1 (Karim Ahmed) left site — 17:28:44` |

### Slash Commands

| Command | Response |
|---|---|
| `/status` | `Workers in danger zone: 1 · Safe zone: 3 · Total on site: 4` |
| `/heatmap` | Sends annotated camera snapshot as photo |
| `/compliance` | `Helmet compliance this session: 80.8% (38/47 detections)` |
| `/workers` | Lists all identified workers currently tracked with zones |
| `/log` | Entry/exit timestamps for all workers today |
| `/report` | Full session summary — violations, interventions, compliance score |
| `/arm` | Arms system — `🟢 ARGUS armed` |
| `/disarm` | Disarms system — `⚫ ARGUS disarmed` |
| `/startshift` | Starts timed shift session with timestamp |
| `/endshift` | Ends session, auto-generates and sends full report |
| `/help` | Lists all commands with descriptions |

### Software steps

**`comms/telegram_bot.py`**
- [ CODE PLACEHOLDER ] `python-telegram-bot` Application initialised with bot token
- [ CODE PLACEHOLDER ] `send_alert(message, photo_path=None)` async function — sends to supervisor_id
- [ CODE PLACEHOLDER ] Handler registered for each slash command
- [ CODE PLACEHOLDER ] `/heatmap` handler calls `heatmap.get_snapshot()` → sends as photo
- [ CODE PLACEHOLDER ] `/status` handler reads current FSM state + zone occupancy counters
- [ CODE PLACEHOLDER ] `/report` handler reads session log, formats summary, sends as message
- [ CODE PLACEHOLDER ] `/arm` and `/disarm` handlers update system armed flag + send Arduino RESET
- [ CODE PLACEHOLDER ] Incoming message filter: only responds to supervisor_id — ignores all others
- [ CODE PLACEHOLDER ] Bot runs as separate asyncio task alongside main pipeline

### Validation test
Send `/arm` to bot — system should log "armed" and send confirmation. Send `/status` — should reply with current counts (all zero on empty setup). Place a plain chess piece inside outer zone — should receive violation alert within 3 seconds including YOLOv8 confidence score. Send `/heatmap` — should receive photo of annotated camera frame within 5 seconds. Send `/disarm` — confirm no further alerts fire when piece is moved.

---

## 16. Phase 9 — Heatmap Overlay System

**Goal:** Real-time annotated overhead view showing all tracked workers with status, trails, and zone info.

### What the Heatmap Shows

```
Overhead camera frame with overlays:

Green filled dot     = compliant worker (helmet on, safe zone)
Red filled dot       = non-compliant worker (no helmet)
Orange filled dot    = repeat offender (3+ violations this session)
Blue filled dot      = compliant worker inside danger zone
Purple filled dot    = marble / unidentified fast-moving object
Grey dot             = worker just entered, not yet classified

Fading trail line    = last 30 frames of position history per object
                       (brightness fades toward oldest position)

Velocity arrow       = current movement direction per tracked object
                       (scaled to speed magnitude)

Zone overlays        = semi-transparent green (safe) + red (danger)
                       polygons drawn on frame

Worker label         = number + name + compliance status beside each dot
                       (e.g. "#3 Jamal ⚠️")

Zone occupancy badge = "Danger zone: 1/2" shown in corner of danger zone
```

### On-Demand Telegram Delivery

When supervisor sends `/heatmap`:
- Current annotated frame captured from live pipeline
- All overlays drawn on frame
- Saved as JPEG to temp file
- Sent as Telegram photo reply
- Temp file deleted

### Software steps

**`core/heatmap.py`**
- [ CODE PLACEHOLDER ] `HeatmapRenderer.draw(frame, tracked_objects, fsm_state)` function
- [ CODE PLACEHOLDER ] For each tracked object: draw dot with color based on status
- [ CODE PLACEHOLDER ] Draw trail: loop through last 30 positions, alpha decreasing toward oldest
- [ CODE PLACEHOLDER ] Draw velocity arrow using `cv2.arrowedLine`
- [ CODE PLACEHOLDER ] Draw worker label text beside each dot
- [ CODE PLACEHOLDER ] Draw zone overlays from geometry module
- [ CODE PLACEHOLDER ] Draw occupancy badge inside danger zone polygon
- [ CODE PLACEHOLDER ] `get_snapshot()` → returns annotated frame as JPEG bytes for Telegram

### Validation test
Place 3 chess pieces inside outer zone — 2 helmeted, 1 plain. Heatmap should show 2 green dots, 1 red dot, all labeled with worker names. Send `/heatmap` to Telegram — photo received shows same state. Move a piece — trail line should follow. Roll marble — purple dot with velocity arrow should track it.

---

## 17. Phase 10 — RetinaFace + ArcFace Entry Verification

**Goal:** Verify worker identity at the outer perimeter entry point using face recognition. Justifies RetinaFace + ArcFace in research paper.

> Note: This is the research extension layer. The system works fully without it.
> Add this after all other phases are complete and stable.

### How Enrollment Works

```
Supervisor sends worker's photo via Telegram to the bot
        ↓
Telegram bot receives photo, saves to temp file
        ↓
RetinaFace detects and crops face from photo
        ↓
CLAHE preprocessing applied to crop
        ↓
ArcFace generates 512-dimensional embedding
        ↓
Embedding saved to workers/embeddings.pkl:
{"Karim Ahmed": [0.23, -0.81, 0.44, ...]}
        ↓
Bot replies: "✅ Karim Ahmed enrolled successfully"
```

### Live Verification

```
Worker approaches outer perimeter entry
        ↓
Camera detects face via RetinaFace
        ↓
CLAHE preprocessing on face crop
        ↓
ArcFace generates embedding for live face
        ↓
Cosine similarity vs all stored embeddings:
  similarity > 0.6 → MATCH → confirmed identity
  similarity < 0.6 → NO MATCH → unknown person
        ↓
Identity confirmed → Telegram: "📥 Karim Ahmed
entered site — face verified — 09:02:11"
        ↓
Unknown person → Telegram: "🚨 Unidentified
person entered site perimeter — photo attached"
```

### Software steps

**`scripts/enroll_worker.py`**
- [ CODE PLACEHOLDER ] Standalone enrollment script for testing outside Telegram
- [ CODE PLACEHOLDER ] Accepts image path as argument
- [ CODE PLACEHOLDER ] Runs full enrollment pipeline
- [ CODE PLACEHOLDER ] Prints embedding dimensions and cosine similarity to existing entries

**`core/face.py`**
- [ CODE PLACEHOLDER ] `insightface.app.FaceAnalysis` initialised with buffalo_l model
- [ CODE PLACEHOLDER ] `enroll(image_path, worker_name)` — detects face, CLAHE, generate embedding, save to pkl
- [ CODE PLACEHOLDER ] `verify(frame)` — detect face in live frame, CLAHE, generate embedding,
  compare against all stored embeddings, return best match name + similarity score
- [ CODE PLACEHOLDER ] Similarity threshold configurable in config.yaml (default 0.6)
- [ CODE PLACEHOLDER ] Unknown person → returns None name, similarity 0.0
- [ CODE PLACEHOLDER ] `load_embeddings()` and `save_embeddings()` for pkl persistence

**Telegram enrollment handler in `comms/telegram_bot.py`**
- [ CODE PLACEHOLDER ] Handler for photo messages with caption format: "enroll:Karim Ahmed"
- [ CODE PLACEHOLDER ] Downloads photo, calls `face.enroll()`, sends confirmation

### Validation test
Take a clear photo of yourself. Send to Telegram bot with caption "enroll:Test Worker". Bot should reply enrolled successfully. Stand in front of camera at perimeter entry. Console should print: "Test Worker — similarity: 0.82 — MATCH". Now have a different person stand — should print: "Unknown — similarity: 0.31 — NO MATCH."

---

## 18. Phase 11 — Full Integration

**Goal:** Single `main.py` entry point. One command starts entire ARGUS system.

### Startup Sequence

```
python main.py
        ↓
Load config.yaml → validate with Pydantic
        ↓
Initialise all modules
        ↓
Arduino PING health check (3 retries)
        ↓
If PING fails → log error, continue without hardware
        ↓
Telegram bot sends: "🟢 ARGUS armed — session started"
        ↓
asyncio.gather() starts all coroutines:
  ├── Camera capture coroutine (30 FPS)
  ├── Main pipeline coroutine (per frame processing)
  ├── Telegram bot polling coroutine
  └── FastAPI WebSocket server (dashboard)
        ↓
System live — FSM in IDLE state
```

### Per-Frame Pipeline

```
Dequeue frame from camera queue
        ↓
Run YOLOv8 detection (ThreadPoolExecutor)
        ↓
For each detection:
    Apply CLAHE to bounding box crop
    Run EasyOCR if helmet class → get number → get name
    Check zone membership via geometry module
    If outside all zones → skip
    Run friend-foe: helmet vs no-helmet
    Update Kalman tracker with centroid
    Compute threat score
    Check repeat offender status
    Check zone occupancy limit
    Check speed threshold
    Transition FSM state
    Emit SystemEvent
        ↓
SystemEvent dispatched to (asyncio.gather):
    ├── serial_bridge.send() → Arduino hardware response
    ├── telegram_bot.send_alert() → supervisor message
    └── ws_server.broadcast() → dashboard update
        ↓
HeatmapRenderer.draw() updates overlay on frame
Next frame
```

### Graceful Shutdown

```
Ctrl+C pressed
        ↓
Telegram bot sends: "⚫ ARGUS shutdown — [timestamp]"
        ↓
Arduino RESET command sent
        ↓
Serial port closed
        ↓
Session log finalized
        ↓
Process exits cleanly
```

### Software steps

**`main.py`**
- [ CODE PLACEHOLDER ] Config loaded and validated
- [ CODE PLACEHOLDER ] All module instances created and stored in AppContext dataclass
- [ CODE PLACEHOLDER ] Arduino health check with retry logic
- [ CODE PLACEHOLDER ] `asyncio.gather()` runs all coroutines
- [ CODE PLACEHOLDER ] `signal.signal(SIGINT)` handles graceful shutdown

### Full Integration Validation Checklist

- [ ] Empty setup: system stays IDLE, zero false detections, dashboard shows blue ring
- [ ] Plain chess piece in safe zone: WARNING state, yellow LED, Telegram alert received with confidence score
- [ ] Helmeted chess piece in safe zone: MONITORING state, green LED soft pulse, no alert
- [ ] Rolling marble toward inner tape: Kalman trail visible, countdown shows, INTERCEPT fires before marble crosses inner tape, barrier drops, laser on, red LED, Telegram alert
- [ ] Helmeted chess piece crossing inner tape: AUTHORIZED state, green flag raises, Telegram entry notification
- [ ] Same piece violates 3 times: escalation Telegram message received
- [ ] `/status` command: correct worker counts returned
- [ ] `/heatmap` command: annotated photo received with correct dot colors
- [ ] `/disarm` command: piece moved, no alerts fire
- [ ] `/arm` command: alerts resume
- [ ] `/endshift` command: full session report generated and sent
- [ ] Battery-powered test: disconnect all USB cables, confirm full system runs on batteries
- [ ] 10-minute continuous run: no crashes, no memory leaks, stable frame rate

---

## 19. Demo Runbook

> Rehearse this twice before presentation day. Each act takes under 90 seconds.

### Setup (10 minutes before instructor arrives)
- [ ] Tape squares laid flat, no lifted corners
- [ ] Toy car placed inside inner square
- [ ] Helmeted chess pieces (numbers 1, 2, 3) on left side of outer square
- [ ] Plain chess pieces on right side
- [ ] Marble nearby, not yet inside perimeter
- [ ] Arduino powered from battery — NO USB CABLE visible
- [ ] Phone mounted overhead, IP Webcam running
- [ ] Laptop open, `python main.py` running
- [ ] Telegram open on phone showing "ARGUS armed" message
- [ ] Dashboard open at `localhost:8080` on full screen

---

### Act 1 — System Introduction (60 seconds)

Point to dashboard. Explain: two zones visible as colored overlays — green safe zone, red danger zone. System is armed and monitoring. All zone sectors blue — no violation history.

Point to toy car: "This is the crane. The red zone is its swing radius."
Point to plain chess pieces: "These workers have no helmets."
Point to paper-helmeted pieces: "These are compliant workers."

---

### Act 2 — Non-Compliant Worker (60 seconds)

Place a plain chess piece inside the outer tape but outside the inner tape.

**What happens:**
- Bounding box appears immediately on camera feed: "head — 0.91"
- State transitions WARNING
- Yellow LED pulses
- Telegram message arrives: "⚠️ Worker detected without helmet — Safe Zone — [time] [94%]"

Show the Telegram message to the instructor.

**Say:** *"The system identified a worker without a helmet in the safe zone. The supervisor was notified immediately with confidence score. No physical intervention yet — the worker is not in immediate danger."*

---

### Act 3 — Kalman Marble Intercept (90 seconds)

This is the most important act. Roll the marble slowly from outside the outer tape toward the inner tape.

**What happens:**
- Marble contour detected entering outer zone
- Purple dot appears on heatmap with velocity arrow pointing ahead
- Ghost dot appears 0.5s ahead of actual marble position
- Countdown appears: "Zone entry: 3.8s"
- Countdown decreases as marble approaches
- BEFORE marble crosses inner tape: INTERCEPT fires
  - Servo 1 rotates — barrier drops across inner tape
  - Laser turns on — red line projects across inner boundary
  - Red LED continuous
  - Buzzer sounds
  - Telegram: "🚨 Fast object intercepted — predicted entry in 2.1s — laser active"

**Say:** *"The Kalman filter computed the marble's velocity vector and predicted zone entry 2 seconds before it happened. The barrier dropped and the laser fired on prediction — not reaction. That is the difference between prevention and response."*

Now roll the marble fast — show it being intercepted with a smaller time-to-entry value. Tell the instructor the time-to-entry adapts to speed.

---

### Act 4 — Repeat Offender (30 seconds)

Place the same plain chess piece inside outer zone 3 times in a row.

**What happens:**
- First two: standard WARNING messages
- Third: escalation Telegram message arrives:
  "🔴 ESCALATION — Worker #3 (Jamal Hossain) — 3rd violation this session"
- Heatmap shows orange dot for that piece instead of red

**Say:** *"The system remembers. Chronic violators are flagged separately and escalated to the supervisor. This is actionable intelligence for site management."*

---

### Act 5 — Compliant Worker Entry (30 seconds)

Move a helmeted chess piece (number 2) from safe zone across inner tape into danger zone.

**What happens:**
- Compliant classification confirmed
- AUTHORIZED state
- Green LED pulses
- Servo 2 raises green flag
- Telegram: "✅ Worker #2 (Rahim Mia) entered crane zone with helmet — Occupancy: 1/2"

---

### Act 6 — Supervisor Commands (60 seconds)

Send these commands live from Telegram while instructor watches:

`/status` → reads out current zone occupancies
`/compliance` → shows helmet compliance percentage
`/heatmap` → annotated photo arrives in Telegram
`/disarm` → system disarms, move chess piece, confirm no alert fires
`/arm` → system re-arms, move chess piece, confirm alert fires again
`/endshift` → full session report generated and sent as text

**Say:** *"The supervisor never needs to be physically present. Every decision, every override, every report — from Telegram, from anywhere."*

---

### Closing Line

*"ARGUS combines YOLOv8 object detection trained on 7,000 labeled construction site images, CLAHE preprocessing for harsh lighting conditions, Kalman predictive tracking for pre-emptive intervention, ArcFace biometric verification for identity confirmation, and a Telegram-based supervisor interface — all running on a laptop GPU communicating wirelessly to an Arduino Uno for under ৳700 in hardware. This is not a prototype of a future system. This is a deployable system today."*

---

## 20. Build Timeline

| Phase | Task | Estimated Time |
|---|---|---|
| 0 | Environment setup, Telegram bot token, Bluetooth pairing | 2 hours |
| 1 | Camera + zone calibration | 3 hours |
| 2 | YOLOv8 training + validation | 4 hours (30 min training, rest validation) |
| 3 | EasyOCR helmet number reading | 3 hours |
| 4 | CLAHE preprocessing pipeline | 1 hour |
| 5 | Kalman tracker + marble validation | 4 hours |
| 6 | Threat state machine | 3 hours |
| 7 | Arduino firmware + serial bridge | 4 hours |
| 8 | Telegram bot + all slash commands | 4 hours |
| 9 | Heatmap overlay system | 3 hours |
| 10 | RetinaFace + ArcFace entry verification | 5 hours |
| 11 | Full integration + validation checklist | 4 hours |
| Demo | Rehearsal × 2 | 2 hours |
| **Total** | | **~42 hours** |

> Realistic spread: 8–10 focused coding days.
> Phase 7 (Arduino) must be done before Phase 11 (integration).
> All other phases can be developed and tested independently.

---

*Document version 1.0 · ARGUS · DIU Software Engineering 2026*
*Autonomous Real-time Guard for Unsafe Sites*
