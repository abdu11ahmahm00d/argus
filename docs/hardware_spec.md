# ⚠️ ARGUS
## Autonomous Real-time Guard for Unsafe Sites
### Full Build Pipeline — Hardware + Software Scaffolding
### DIU Software Engineering · Arduino Course Project · 2026

---

> **Project Identity:**
> ARGUS is a multi-layer computer vision safety enforcement system for construction sites.
> Two physical tape squares define visual boundaries. Two OpenCV polygons define the logic.
> Chess pieces simulate workers. A rolling marble demonstrates Kalman velocity tracking.
> A toy car or bottle represents the crane/machine. Arduino executes all physical responses.
> Telegram bot is the supervisor interface. GTX 1080 Max-Q laptop is the brain.

---

> **Research Paper Title:**
> *"ARGUS: A Multi-Layer Computer Vision Safety Enforcement System
> for Construction Site Hazard Prevention in Resource-Constrained Environments"*

---

## Table of Contents

1. [Component Inventory](#1-component-inventory)
2. [Prototype Environment Setup](#2-prototype-environment-setup)
3. [Arduino Pin Wiring — Complete](#3-arduino-pin-wiring--complete)
4. [Power Supply Wiring](#4-power-supply-wiring)
5. [Servo Mechanism Build](#5-servo-mechanism-build)
6. [Pre-Build Verification Checklist](#6-pre-build-verification-checklist)
7. [Software Environment](#7-software-environment)
8. [Phase 1 — Camera + Zone Calibration](#8-phase-1--camera--zone-calibration)
9. [Phase 2 — YOLOv8 Helmet Detection](#9-phase-2--yolov8-helmet-detection)
10. [Phase 3 — EasyOCR Helmet Number Reading](#10-phase-3--easyocr-helmet-number-reading)
11. [Phase 4 — CLAHE Preprocessing Pipeline](#11-phase-4--clahe-preprocessing-pipeline)
12. [Phase 5 — Kalman Tracker + Marble Demo](#12-phase-5--kalman-tracker--marble-demo)
13. [Phase 6 — Threat State Machine](#13-phase-6--threat-state-machine)
14. [Phase 7 — Arduino Firmware + Serial Bridge](#14-phase-7--arduino-firmware--serial-bridge)
15. [Phase 8 — Telegram Bot + Slash Commands](#15-phase-8--telegram-bot--slash-commands)
16. [Phase 9 — Heatmap Overlay System](#16-phase-9--heatmap-overlay-system)
17. [Phase 10 — RetinaFace + ArcFace Entry Verification](#17-phase-10--retinaface--arcface-entry-verification)
18. [Phase 11 — Full Integration](#18-phase-11--full-integration)
19. [Demo Runbook](#19-demo-runbook)
20. [Build Timeline](#20-build-timeline)

---

## 1. Component Inventory

### Hardware You Already Have

| Component | Qty | Role in ARGUS |
|---|---|---|
| Arduino Uno R3 | 1 | Executes all physical responses |
| HC-SR04 Ultrasonic Sensor | 1 | Detects marble/fast object speed as secondary sensor |
| MG90S Micro Servo Motor | 2 | Servo 1: barrier stick drop · Servo 2: green flag raise |
| LM2596 DC-DC Buck Converter | 1 | Regulates 7.4V → 5V stable for Arduino + servos |
| 18650 Li-ion Battery | 2 | Series pack = 7.4V field power |
| Laser Module (650nm 5mW) | 1 | Projects red line across inner zone boundary on threat |
| LilyPad Red LED | 1 | Violation indicator — continuous red on intercept |
| Active Buzzer Module (3-pin) | 1 | Audible alarm on zone intercept |
| Breadboard | 1 | All circuit connections |
| Jumper Wires M-M + M-F | 1 bundle | All connections |
| Switch | 1 | Master arm/disarm hardware toggle |
| HC-05 Bluetooth Module | 1 | Wireless laptop ↔ Arduino serial bridge |

### Additional Items for Prototype (Zero Cost)

| Item | Simulates | Preparation |
|---|---|---|
| Black electrical tape | Zone boundaries (visual) | Two squares on flat surface |
| Chess pieces × 5–6 | Construction workers | Leave 3 plain, stick paper helmet circles on 3 |
| Paper circles (3cm diameter) | Helmets | Cut from white paper, write number 1–5 in thick black marker |
| Toy car / water bottle | Crane / heavy machine | Place inside inner tape square |
| Marble (1–2) | Rolling fast object for Kalman demo | Any standard marble |
| Popsicle stick or thin cardboard strip | Barrier arm on Servo 1 | Tape to servo horn |
| Green paper rectangle (3×5cm) | Clearance flag on Servo 2 | Tape to servo horn |
| Phone (Android) | Overhead camera | Mount overhead on book stack |
| Stack of books or cardboard box | Camera mount | 40–50cm height above floor |
| Rubber band or zip tie | Laser mount on Servo 1 horn | Holds laser module to servo |

### Additional Items to Purchase

| Item | Cost | Where |
|---|---|---|
| SW-420 Vibration Sensor (optional) | ৳60 | RoboticsBD — for marble impact detection |
| Extra jumper wires if needed | ৳100 | RoboticsBD |

---

## 2. Prototype Environment Setup

### Physical Floor Layout

```
          [Phone camera overhead, 40–50cm height, facing straight down]
                                    |
        ┌───────────────────────────▼───────────────────────────┐
        │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ ← OUTER TAPE SQUARE
        │░   SAFE ZONE                                       ░│    (black electrical tape)
        │░   Chess pieces roam here                          ░│
        │░   Marble rolls here                               ░│
        │░                                                   ░│
        │░   ┌─────────────────────────────────────────┐    ░│ ← INNER TAPE SQUARE
        │░   │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│    ░│    (black electrical tape)
        │░   │▓   DANGER ZONE                         ▓│    ░│
        │░   │▓   [toy car / bottle = the machine]    ▓│    ░│
        │░   │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│    ░│
        │░   └─────────────────────────────────────────┘    ░│
        │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
        └───────────────────────────────────────────────────────┘

[Arduino box placed beside the outer tape square — not inside it]
[Servo 1 positioned so barrier arm drops across inner tape edge]
[Laser mounted on Servo 1 horn, aimed across inner tape boundary]
```

### Step-by-Step Physical Arrangement

**Step 1 — Choose your surface**
Use a table or clear floor area. Minimum size: 60×60cm. Flat, matte surface preferred — shiny surfaces cause camera glare.

**Step 2 — Lay outer tape square**
Cut 4 strips of black electrical tape. Form a square approximately 50×50cm. This is the safe zone visual boundary. Press firmly — tape must not lift during demo.

**Step 3 — Lay inner tape square**
Cut 4 shorter strips. Form a square approximately 25×25cm centered inside the outer square. Leave at least 10cm gap between inner and outer squares on all sides. This is the danger zone visual boundary.

**Step 4 — Place the machine**
Place a toy car, water bottle, or any object inside the inner square. This represents the crane or heavy machinery. It does not move during the demo.

**Step 5 — Prepare chess pieces**
- Take 3 chess pieces. Cut 3 white paper circles (~3cm diameter). Write numbers 1, 2, 3 in thick black marker. Stick one circle flat on top of each piece using tape or glue. These are compliant workers.
- Leave 3 chess pieces plain with no paper circle. These are non-compliant workers.
- Confirm numbers are clearly visible from 40–50cm camera height. Test by holding phone above and checking the camera image.

**Step 6 — Build camera mount**
Stack books or fold a cardboard box to 40–50cm height beside the setup. Place phone flat on top facing straight down. The entire outer tape square must be visible in the camera frame with some margin. Confirm phone is stable and will not shift during demo.

**Step 7 — Position Arduino box**
Place Arduino + breadboard assembly beside the outer tape, not inside it. Servo 1 must be positioned so its arm (popsicle stick) physically crosses the inner tape edge when it rotates. Test this manually before wiring. The arm should rest parallel to the inner tape edge in rest position, and drop perpendicular across it on trigger.

**Step 8 — Servo 1 barrier positioning**
Servo 1 at 90° = barrier raised (parallel to tape, not blocking). Servo 1 at 0° = barrier dropped (perpendicular across inner tape, blocking entry). Confirm this range works physically before wiring anything.

**Step 9 — Servo 2 flag positioning**
Servo 2 at 0° = flag down (resting). Servo 2 at 90° = flag raised (green clearance signal). Tape green paper rectangle to servo horn. Confirm flag is visible from camera angle.

**Step 10 — Laser alignment**
Mount laser module to Servo 1 horn with rubber band or zip tie. At servo 90° (barrier raised), laser should point horizontally across the inner tape boundary — projecting a visible red line across the zone entry path. Test this alignment before wiring by manually holding servo and powering laser briefly.

---

## 3. Arduino Pin Wiring — Complete

> ⚠️ Wire in this exact order. Do not power anything until Step 4 power supply wiring is complete.
> Use the switch to keep everything off during wiring.

### Pin Assignment Table

| Component | Arduino Pin | Wire Color Suggestion | Notes |
|---|---|---|---|
| HC-05 TX | Pin 10 (SoftSerial RX) | Yellow | Do NOT use pins 0/1 |
| HC-05 RX | Pin 11 (SoftSerial TX) | Orange | Do NOT use pins 0/1 |
| Servo 1 Signal | Pin 9 | White | Barrier + laser servo |
| Servo 2 Signal | Pin 6 | White | Flag servo |
| Laser Signal | Pin 5 | Red | Digital HIGH/LOW control |
| Red LED Signal | Pin 4 | Red | LilyPad has built-in resistor |
| Green LED Signal | Pin 3 | Green | If adding separate green LED |
| Buzzer Signal | Pin 3 | Purple | Or Pin 2 if green LED on Pin 3 |
| HC-SR04 TRIG | Pin 7 | Blue | |
| HC-SR04 ECHO | Pin 8 | Green | |
| Switch | Pin 2 | Grey | INPUT_PULLUP mode |

> Note on Pin 3: Buzzer and Green LED share the same pin only if you trigger them
> together always. If you want independent control, use Pin 3 for buzzer and add
> green LED on Pin A0 (analog pin used as digital).

### Revised Clean Pin Assignment (Recommended)

| Component | Arduino Pin |
|---|---|
| HC-05 TX | 10 |
| HC-05 RX | 11 |
| Servo 1 (barrier + laser) | 9 |
| Servo 2 (green flag) | 6 |
| Laser Module | 5 |
| Red LED (LilyPad) | 4 |
| Buzzer | 3 |
| Green LED | A0 (used as digital) |
| HC-SR04 TRIG | 7 |
| HC-SR04 ECHO | 8 |
| Switch | 2 |

### HC-05 Bluetooth Module Wiring

```
HC-05 VCC  ──────────────────────  Arduino 5V
HC-05 GND  ──────────────────────  Arduino GND
HC-05 TXD  ──────────────────────  Arduino Pin 10
HC-05 RXD  ──────────────────────  Arduino Pin 11

⚠️ HC-05 RXD expects 3.3V logic. Arduino outputs 5V.
   Add a voltage divider on the RXD line:
   Pin 11 → 1kΩ resistor → HC-05 RXD
                         → 2kΩ resistor → GND
   This protects the HC-05 from 5V damage.
```

### Servo 1 Wiring (Barrier + Laser servo)

```
Servo 1 Signal (white/orange wire)  ──  Arduino Pin 9
Servo 1 VCC    (red wire)           ──  Buck converter 5V output
Servo 1 GND    (black/brown wire)   ──  Common GND rail

⚠️ Never power servos from Arduino 5V pin.
   Always use buck converter output.
   Servos draw up to 500mA each — Arduino 5V pin
   maxes at 200mA total and will reset under servo load.
```

### Servo 2 Wiring (Green flag servo)

```
Servo 2 Signal (white/orange wire)  ──  Arduino Pin 6
Servo 2 VCC    (red wire)           ──  Buck converter 5V output
Servo 2 GND    (black/brown wire)   ──  Common GND rail
```

### Laser Module Wiring

```
Laser VCC / Signal  ──  Arduino Pin 5
Laser GND           ──  Arduino GND

⚠️ This laser module is controlled by digital HIGH/LOW on Pin 5.
   HIGH = laser on. LOW = laser off.
   If module has 3 pins (VCC, GND, Signal):
   VCC → Arduino 5V (constant power)
   Signal → Arduino Pin 5 (controls on/off)
   GND → Arduino GND
```

### LilyPad Red LED Wiring

```
LilyPad LED  +  ──  Arduino Pin 4
LilyPad LED  -  ──  Arduino GND

Note: LilyPad LED has built-in resistor. No external resistor needed.
```

### Green LED Wiring

```
Green LED  +  ──  220Ω resistor  ──  Arduino Pin A0
Green LED  -  ──  Arduino GND

Note: Standard LED needs 220Ω resistor. Not built-in like LilyPad.
      Use A0 as: pinMode(A0, OUTPUT); digitalWrite(A0, HIGH/LOW);
```

### Active Buzzer Wiring

```
Buzzer VCC / Signal  ──  Arduino Pin 3
Buzzer GND           ──  Arduino GND

Note: 3-pin active buzzer:
      Pin 1 (VCC)    → Arduino 5V (constant)
      Pin 2 (GND)    → Arduino GND
      Pin 3 (Signal) → Arduino Pin 3
      HIGH = buzzer on. LOW = off.
```

### HC-SR04 Ultrasonic Sensor Wiring

```
HC-SR04 VCC   ──  Arduino 5V
HC-SR04 GND   ──  Arduino GND
HC-SR04 TRIG  ──  Arduino Pin 7
HC-SR04 ECHO  ──  Arduino Pin 8

Placement: Mount at inner tape square edge, pointing horizontally
           across the danger zone entrance. Detects marble speed
           and close-range object entry independently of camera.
```

### Switch Wiring

```
Switch terminal 1  ──  Arduino Pin 2
Switch terminal 2  ──  Arduino GND

In Arduino code: pinMode(2, INPUT_PULLUP);
When switch open: Pin 2 reads HIGH = system armed
When switch closed: Pin 2 reads LOW = system disarmed

This is the hardware override. Flipping the switch during demo
immediately disarms all physical responses regardless of software state.
```

### Breadboard Common Rails

```
Breadboard positive rail (+)  ──  Buck converter 5V output
Breadboard negative rail (-)  ──  Arduino GND

All component VCC connections go to breadboard + rail.
All component GND connections go to breadboard - rail.
This keeps wiring clean and avoids overloading Arduino pins.
```

---

## 4. Power Supply Wiring

> Complete this section before connecting anything to Arduino.
> Measure output voltage before connecting. Wrong voltage kills components.

### Battery Pack Assembly

```
Battery 1 positive  ──┐
                       ├──  Buck converter VIN+
Battery 2 negative  ──┘

Battery 1 negative  ──┐
                       ├──  Buck converter VIN-
Battery 2 positive  ──┘
(series connection = 7.4V total)

Switch inserted on positive line between
battery pack positive and buck converter VIN+:

Battery Pack (+) ── Switch ── Buck VIN+
Battery Pack (-) ─────────── Buck VIN-
```

### Buck Converter Calibration

```
Step 1: Connect batteries through switch. Switch OFF.
Step 2: Turn switch ON.
Step 3: Set multimeter to DC voltage, 20V range.
Step 4: Probe buck converter output terminals.
Step 5: Adjust trim potentiometer on LM2596 slowly.
Step 6: Stop when multimeter reads exactly 5.0V (±0.1V).
Step 7: Turn switch OFF.
Step 8: Now connect buck converter output to breadboard rails.

⚠️ Never skip this calibration step.
   7.4V directly to Arduino or servos = permanent damage.
   5.2V+ to servos = overheating.
   4.8V- = servos and Arduino behave erratically.
```

### Power Distribution

```
Buck converter 5V output  ──  Breadboard + rail
                          ──  Arduino VIN pin (powers Arduino from buck)
Buck converter GND        ──  Breadboard - rail
                          ──  Arduino GND

Servo 1 VCC  ──  Breadboard + rail
Servo 2 VCC  ──  Breadboard + rail
Both servo GNDs  ──  Breadboard - rail

⚠️ Do NOT connect Arduino 5V pin to the breadboard rail.
   Arduino's 5V pin is output only from its onboard regulator.
   Power Arduino through VIN pin from the buck converter instead.
   This means Arduino and all components share one clean 5V source.
```

---

## 5. Servo Mechanism Build

### Servo 1 — Barrier + Laser Arm

**Materials:** Servo 1, popsicle stick (15cm), rubber band, laser module, hot glue or tape

```
Step 1: Take servo horn (the white cross-shaped piece included with servo).
        Attach popsicle stick along one arm of the horn using hot glue or tape.
        Stick must be firm — it will physically stop objects.

Step 2: Mount laser module beside the popsicle stick on the same servo horn.
        Use rubber band wrapped tightly. Laser face must point in same direction
        as the stick, horizontally forward.

Step 3: Attach horn back onto servo shaft.

Step 4: Position servo so that:
        At 90°  = stick and laser point parallel to inner tape (resting, not blocking)
        At 0°   = stick drops perpendicular ACROSS inner tape (blocking entry)
                  laser simultaneously sweeps to project across entry path

Step 5: Fix servo body to a small cardboard block or tape it firmly to a book
        beside the inner tape square edge. It must not shift during actuation.

Step 6: Test manually: rotate servo horn by hand through 0°–90° range.
        Confirm stick drops cleanly across tape at 0° without catching anything.
        Confirm laser points across tape boundary at 0°.
```

### Servo 2 — Green Clearance Flag

**Materials:** Servo 2, green paper rectangle (3×5cm), tape

```
Step 1: Cut green paper rectangle 3×5cm.
Step 2: Tape it firmly to one arm of the servo horn.
Step 3: Attach horn to servo shaft.
Step 4: Position servo so that:
        At 0°   = flag hangs down (not visible, resting)
        At 90°  = flag stands upright (clearly visible from camera angle)
Step 5: Fix servo body beside the outer tape square using tape or cardboard block.
Step 6: Test manually: rotate through range. Flag must stand clearly visible at 90°.
```

---

## 6. Pre-Build Verification Checklist

Complete every item before proceeding to software phases.
Do not skip. Every unchecked item is a potential demo failure.

### Power

- [ ] Buck converter output measured at 5.0V (±0.1V) with multimeter
- [ ] Switch cuts power cleanly — verified by multimeter dropping to 0V
- [ ] Arduino powers on from VIN + buck converter (green power LED on Arduino)
- [ ] No components connected to Arduino's 5V output pin

### Connections

- [ ] HC-05 on pins 10/11 ONLY — not pins 0/1
- [ ] HC-05 RXD voltage divider in place (1kΩ + 2kΩ)
- [ ] Both servo VCC from breadboard rail — not Arduino 5V
- [ ] All GNDs connected to common rail
- [ ] Laser wired to Pin 5 — test: `digitalWrite(5, HIGH)` turns laser on

### Mechanical

- [ ] Servo 1 at 90° = barrier parallel to tape (resting)
- [ ] Servo 1 at 0° = barrier drops across inner tape cleanly
- [ ] Laser on Servo 1 projects visible line across inner tape at 0°
- [ ] Servo 2 at 0° = flag down
- [ ] Servo 2 at 90° = flag visibly upright
- [ ] All servo bodies fixed firmly — no shifting during actuation

### Camera

- [ ] Phone mounted at 40–50cm height, facing straight down
- [ ] Entire outer tape square visible in camera frame with margin
- [ ] Inner tape square clearly visible and distinguishable
- [ ] Chess piece numbers readable from camera height
- [ ] Lighting even — no strong shadows obscuring either zone

### Bluetooth

- [ ] HC-05 paired with laptop
- [ ] COM port number noted (e.g. COM7)
- [ ] HC-05 LED blinks slowly (every 2s) = paired and ready