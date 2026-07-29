# Wiring Guide

## Pin Assignment

| Component | Arduino Pin | Wire Color | Notes |
|---|---|---|---|
| HC-05 TX | Pin 10 (SoftSerial RX) | Yellow | Do NOT use pins 0/1 (reserved for USB) |
| HC-05 RX | Pin 11 (SoftSerial TX) | Orange | Use voltage divider: 1kΩ + 2kΩ to GND |
| Servo 1 signal | Pin 9 | White | Barrier arm + laser mount |
| Servo 2 signal | Pin 6 | White | Green clearance flag |
| Laser module | Pin 5 | Red | HIGH = on, LOW = off |
| Red LED (LilyPad) | Pin 4 | Red | Built-in resistor — no external needed |
| Buzzer | Pin 3 | Purple | 3-pin active buzzer |
| Green LED | A0 (as digital) | Green | Needs 220Ω resistor in series |
| HC-SR04 TRIG | Pin 7 | Blue | |
| HC-SR04 ECHO | Pin 8 | Green | |
| Switch | Pin 2 | Grey | INPUT_PULLUP — LOW = disarmed |

## Wiring Diagrams

### HC-05 Bluetooth Module

```
HC-05 VCC ──────────────── Arduino 5V
HC-05 GND ──────────────── Arduino GND
HC-05 TXD ──────────────── Arduino Pin 10 (SoftSerial RX)
HC-05 RXD ──── 1kΩ ───┬─── Arduino Pin 11 (SoftSerial TX)
                       └─── 2kΩ ──── GND

⚠️ The voltage divider on RXD protects HC-05 from Arduino's 5V logic.
   HC-05 expects 3.3V on its RX pin. Without this divider, the module
   can be permanently damaged on first data send.
```

### Servo 1 — Barrier + Laser

```
Servo 1 Signal (white) ──── Arduino Pin 9
Servo 1 VCC (red)     ──── Breadboard + rail (buck converter 5V)
Servo 1 GND (black)   ──── Breadboard - rail (common GND)

⚠️ Do NOT power servos from Arduino 5V pin.
   Arduino 5V pin maxes at ~200mA. Servos draw up to 500mA each.
   Power both servos from LM2596 buck converter output.
```

### Servo 2 — Green Flag

```
Servo 2 Signal (white) ──── Arduino Pin 6
Servo 2 VCC (red)     ──── Breadboard + rail (buck converter 5V)
Servo 2 GND (black)   ──── Breadboard - rail (common GND)
```

### Laser Module

```
3-pin module:
  VCC   ──── Arduino 5V (constant power)
  GND   ──── Arduino GND
  Signal ──── Arduino Pin 5 (HIGH = on, LOW = off)

2-pin module:
  Positive ──── Arduino Pin 5 (controls on/off directly)
  Negative ──── Arduino GND
```

### Red LED (LilyPad)

```
LilyPad + ──── Arduino Pin 4
LilyPad - ──── Arduino GND

Note: LilyPad has built-in current-limiting resistor.
No external resistor needed.
```

### Green LED

```
Green LED + ──── 220Ω resistor ──── Arduino Pin A0
Green LED - ──── Arduino GND

Note: Standard LED needs 220Ω resistor in series.
A0 is configured as digital output: pinMode(A0, OUTPUT)
```

### Active Buzzer

```
3-pin module:
  VCC (pin 1) ──── Arduino 5V (constant)
  GND (pin 2) ──── Arduino GND
  Signal (pin 3) ──── Arduino Pin 3

HIGH = buzzer on, LOW = off.
```

### HC-SR04 Ultrasonic Sensor

```
VCC  ──── Arduino 5V
GND  ──── Arduino GND
TRIG ──── Arduino Pin 7
ECHO ──── Arduino Pin 8

Placement: Mount at inner tape square edge, pointing horizontally
across the danger zone entrance. Detects fast objects (marble)
independently of camera.
```

### Switch (Hardware Override)

```
Switch terminal 1 ──── Arduino Pin 2
Switch terminal 2 ──── Arduino GND

Configured as INPUT_PULLUP in firmware:
  Switch open  (HIGH) = system armed  (normal operation)
  Switch closed (LOW) = system disarmed (all outputs off)
```

## Power Supply

### Battery Pack Assembly

```
Battery 1 (+) ────┐
                   ├──── Buck converter VIN+
Battery 2 (-) ────┘

Battery 1 (-) ────┐
                   ├──── Buck converter VIN-
Battery 2 (+) ────┘

Switch inserted between battery pack (+) and Buck VIN+:
  Battery Pack (+) ──── Switch ──── Buck VIN+
  Battery Pack (-) ─────────────── Buck VIN-
```

### Buck Converter Calibration (CRITICAL)

```
1. Connect batteries through switch. Switch OFF.
2. Turn switch ON.
3. Set multimeter to DC voltage, 20V range.
4. Probe buck converter output terminals.
5. Adjust trim potentiometer on LM2596 slowly.
6. Stop when multimeter reads exactly 5.0V (±0.1V).
7. Turn switch OFF.
8. Now connect buck converter output to breadboard rails.

⚠️ 7.4V directly to Arduino or servos = permanent damage.
   5.2V+ to servos = overheating and erratic behaviour.
   4.8V- = servos and Arduino behave unreliably.
   Never skip this calibration step.
```

### Power Distribution

```
Buck converter 5V output ──── Breadboard + rail
                          ──── Arduino VIN pin (powers Arduino)
Buck converter GND       ──── Breadboard - rail
                          ──── Arduino GND

Servo 1 VCC ──── Breadboard + rail
Servo 2 VCC ──── Breadboard + rail
Both servo GNDs ──── Breadboard - rail

⚠️ Do NOT connect Arduino's 5V pin to the breadboard rail.
   Arduino's 5V pin is OUTPUT only (from its onboard regulator).
   Power Arduino through VIN pin from buck converter.
   This keeps everything on one clean 5V source.
```

## Breadboard Layout (Schematic)

```
                    ┌──────────────────────────────┐
      Buck 5V (+) ──┤(+)  Breadboard Power Rail    │
                    ├──────────────────────────────┤
      Buck GND   ───┤(-)  Breadboard Ground Rail   │
                    └──────────────────────────────┘

Arduino connections to breadboard:
  VIN ───── (+) rail
  GND ───── (-) rail
  Pin 10 ─── HC-05 TX (yellow wire)
  Pin 11 ─── 1kΩ → HC-05 RX (orange wire)
            2kΩ → GND
  Pin 9 ──── Servo 1 signal (white)
  Pin 6 ──── Servo 2 signal (white)
  Pin 5 ──── Laser signal (red)
  Pin 4 ──── Red LED + (red)
  Pin 3 ──── Buzzer signal (purple)
  Pin A0 ─── 220Ω → Green LED + (green)
  Pin 7 ──── HC-SR04 TRIG (blue)
  Pin 8 ──── HC-SR04 ECHO (green)
  Pin 2 ──── Switch (grey)

All GNDs → (-) rail
All 5V components (not servos) → (+) rail
Servo VCC → (+) rail (not Arduino 5V)
```

## Pre-Power Checklist

- [ ] Buck converter output measured at 5.0V (±0.1V)
- [ ] Switch cuts power cleanly
- [ ] No components connected to Arduino's 5V output pin
- [ ] HC-05 on pins 10/11 ONLY — not pins 0/1
- [ ] HC-05 RXD voltage divider in place (1kΩ + 2kΩ)
- [ ] Both servo VCC from breadboard rail — not Arduino 5V
- [ ] All GNDs connected to common rail
- [ ] Switch wiring: Pin 2 + GND with INPUT_PULLUP
- [ ] Green LED has 220Ω resistor in series
- [ ] All connections seated firmly; no loose jumper wires
