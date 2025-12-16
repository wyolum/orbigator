# DYNAMIXEL XL330 Pin Assignment Guide

## 🔌 Connector Overview

The DYNAMIXEL XL330 has **TWO 3-pin JST connectors** on the back of the motor (one on each side). These are **daisy-chain ports** that are electrically connected in parallel.

**IMPORTANT:** The connectors are **PHYSICALLY MIRRORED** - Pin 1 is always on the outer edge!

```
    ┌─────────────────────┐
    │   DYNAMIXEL XL330   │
    │                     │
    │  [Port A]  [Port B] │  ← Connectors are MIRRORED
    │    |||       |||    │
    └────┴┴┴───────┴┴┴────┘
         123       321      ← Pin order reversed!
```

---

## 📍 Pin Assignment (MIRRORED Connectors!)

Looking at the connector **from the back of the motor**, with the locking tab on top:

**LEFT Connector:**
```
    ┌─────────────┐
    │  Locking    │
    │    Tab      │
    ├─────────────┤
    │  1   2   3  │  ← Pin numbers
    └──┬──┬──┬───┘
       │  │  │
      GND VDD DATA
    (outer) (inner)
```

**RIGHT Connector (MIRRORED!):**
```
    ┌─────────────┐
    │  Locking    │
    │    Tab      │
    ├─────────────┤
    │  3   2   1  │  ← Pin numbers REVERSED
    └──┬──┬──┬───┘
       │  │  │
     DATA VDD GND
    (inner) (outer)
```

### Key Point:
**Pin 1 (GND) is ALWAYS on the OUTER EDGE** of each connector!
- Left connector: Pin 1 on left side (outer)
- Right connector: Pin 1 on right side (outer)

### Pin Functions:

| Pin | Function | Official Color | Your Wire |
|-----|----------|----------------|-----------|
| 1   | GND      | Black          | ??? (measure with multimeter) |
| 2   | VDD (+5V)| Red            | ??? (measure with multimeter) |
| 3   | DATA     | Yellow         | ??? (measure with multimeter) |

---

## 🔍 How to Identify Pins (No Color Coding)

Since your wires aren't colored, use a **multimeter** to identify them:

### Method 1: Continuity Test (Motor Powered OFF)
1. Set multimeter to continuity/resistance mode
2. Touch one probe to motor's metal case/mounting holes (this is GND)
3. Touch other probe to each wire
4. The wire that beeps/shows 0Ω = **Pin 1 (GND)**

### Method 2: Voltage Test (Motor Powered ON - CAREFUL!)
1. Connect motor to 5V power supply
2. Set multimeter to DC voltage mode
3. Touch black probe to motor case (GND reference)
4. Touch red probe to each wire:
   - **~5V** = Pin 2 (VDD)
   - **~2.5V** (pulled up by 10kΩ resistor) = Pin 3 (DATA)
   - **0V** = Pin 1 (GND)

### Method 3: Visual Inspection
Look at the connector from the **wire side** (where wires enter):
```
Wire entry view (looking INTO connector):
    ┌─────────────┐
    │  Tab DOWN   │
    ├─────────────┤
    │  3   2   1  │  ← Pin numbers (reversed!)
    └──┬──┬──┬───┘
       │  │  │
     DATA VDD GND
```

---

## 🔗 Daisy-Chain Wiring

Both ports are **identical and parallel**. Use one port to connect to your Pico, and the other to connect to the second servo:

```
Pico 2 ←→ [Port A] Servo 1 [Port B] ←→ [Port A] Servo 2 [Port B] (unused)
```

**OR**

```
Pico 2 ←→ [Port B] Servo 1 [Port A] ←→ [Port B] Servo 2 [Port A] (unused)
```

Both configurations work identically!

---

## ⚡ Quick Pin Identification Procedure

1. **Find GND (Pin 1):**
   - Use continuity tester to motor case
   - Mark this wire with tape: "GND"

2. **Power up motor with 5V:**
   - Connect suspected GND to power supply GND
   - Connect another wire to power supply +5V
   - Motor LED should light up briefly

3. **Measure remaining wire:**
   - Should read ~2.5V (DATA line with pull-up)
   - Mark this wire: "DATA"

4. **Confirm VDD (Pin 2):**
   - The wire connected to +5V
   - Mark this wire: "VDD +5V"

---

## 🎨 Recommended: Label Your Wires

Once identified, use colored tape or heat shrink:
- **Pin 1 (GND):** Black tape
- **Pin 2 (VDD):** Red tape  
- **Pin 3 (DATA):** Yellow tape

This matches the official DYNAMIXEL color scheme and makes future work easier!

---

## 📸 Physical Connector Details

- **Connector Type:** JST EHR-03 (3-pin, 2.5mm pitch)
- **Mating Connector:** JST XH or EH series
- **Wire Gauge:** Typically 26-28 AWG
- **Current Rating:** 3A per pin (more than enough for 1.5A servo)

---

## ⚠️ Important Notes

1. **Both ports are identical** - no "input" vs "output" designation
2. **Don't reverse polarity** - measure carefully before connecting power!
3. **DATA line is bidirectional** - half-duplex communication
4. **Common ground required** - Pico GND must connect to servo GND
5. **5V power separate** - Don't power servos from Pico's 5V pin (not enough current)

---

**Once you've identified the pins, label them and proceed with the wiring in the dry lab guide!** 🔧
