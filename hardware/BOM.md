# Bill of Materials

## Core Electronics

| # | Component | Qty | Unit Cost (BDT) | Total (BDT) | Purpose |
|---|---|---|---|---|---|
| 1 | Arduino Uno R3 (clone) | 1 | ৳450 | ৳450 | System controller — executes all physical responses |
| 2 | HC-05 Bluetooth module | 1 | ৳350 | ৳350 | Wireless laptop ↔ Arduino serial link |
| 3 | MG90S micro servo | 2 | ৳180 | ৳360 | Servo 1: barrier arm + laser mount · Servo 2: green clearance flag |
| 4 | HC-SR04 ultrasonic sensor | 1 | ৳120 | ৳120 | Secondary speed/distance sensor |
| 5 | Laser module (650nm, 5mW) | 1 | ৳80 | ৳80 | Projects red line across inner tape on intercept |
| 6 | LilyPad red LED (built-in resistor) | 1 | ৳60 | ৳60 | Violation indicator |
| 7 | 5mm green LED | 1 | ৳5 | ৳5 | Compliance indicator |
| 8 | Active buzzer module (3-pin) | 1 | ৳60 | ৳60 | Audible alarm on intercept |
| 9 | LM2596 DC-DC buck converter | 1 | ৳150 | ৳150 | Regulates 7.4V battery → 5V stable power |
| 10 | 18650 Li-ion battery (3.7V) | 2 | ৳200 | ৳400 | Series = 7.4V field power pack |
| 11 | 18650 battery holder (2-cell series) | 1 | ৳40 | ৳40 | Holds batteries with series wiring |
| 12 | Breadboard (830 point) | 1 | ৳100 | ৳100 | All circuit connections |
| 13 | Jumper wires M-M (65-pack) | 1 | ৳80 | ৳80 | General connections |
| 14 | Jumper wires M-F (40-pack) | 1 | ৳70 | ৳70 | Arduino ↔ breadboard |
| 15 | SPST toggle switch | 1 | ৳30 | ৳30 | Master arm/disarm hardware override |
| 16 | Resistor 220Ω (for green LED) | 1 | ৳2 | ৳2 | Current limiting |
| 17 | Resistor 1kΩ (HC-05 voltage divider) | 1 | ৳2 | ৳2 | HC-05 RXD protection |
| 18 | Resistor 2kΩ (HC-05 voltage divider) | 1 | ৳2 | ৳2 | HC-05 RXD protection |

**Subtotal: ~৳2,360** (~$28 USD)

## Prototype Consumables (Zero Cost)

| Item | Qty | Simulates | Notes |
|---|---|---|---|
| Black electrical tape | 1 roll | Zone boundaries | Two squares on flat surface |
| Chess pieces | 5–6 | Construction workers | 3 plain + 3 with paper helmet circles |
| White paper (A4) | 1 sheet | Helmet circles | Cut 3cm circles, write numbers 1–5 |
| Thick black marker | 1 | Number writing | Numbers must be readable from 40cm |
| Popsicle stick | 1 | Barrier arm on Servo 1 | Tape to servo horn |
| Green paper (3×5cm) | 1 piece | Clearance flag on Servo 2 | Tape to servo horn |
| Marble | 1–2 | Fast rolling object | For Kalman prediction demo |
| Toy car or bottle | 1 | Crane/heavy machine | Place inside danger zone |
| Books or cardboard box | stack | Camera mount | 40–50cm height |
| Rubber band or zip tie | 1 | Laser mount | Hold laser to servo horn |

## Laptop Requirements

| Item | Spec |
|---|---|
| GPU | NVIDIA GTX 1080 or better (for real-time YOLOv8) |
| RAM | 8 GB minimum, 16 GB recommended |
| OS | Windows 10/11, Linux, or macOS |
| Bluetooth | Built-in or USB dongle (for HC-05 pairing) |
| Python | 3.11+ |

## Phone Requirements

| Item | Spec |
|---|---|
| OS | Android (IP Webcam app) or iOS (alternative camera app) |
| WiFi | Same network as laptop |
| Mount | Stable overhead position at 40–50cm height |

## Shopping Notes

- All components available at **RoboticsBD** (Dhaka) or equivalent local supplier
- Arduino Uno clone works identically to original for this project
- MG90S is metal-gear — stronger than plastic SG90; essential for barrier arm weight
- 18650 batteries should be protected (built-in over-discharge protection)
- LM2596 must be adjusted to exactly 5.0V output before connecting anything (see wiring.md)
- IP Webcam app: free on Google Play Store
