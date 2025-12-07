# DYNAMIXEL Wiring Verification Checklist

## Purpose
Use this checklist to verify your DYNAMIXEL XL330-M288-T wiring is correct before powering on the system.

---

## ✅ Pre-Flight Checklist

### 1. Power Connections

#### External 5V Power Supply
- [ ] 5V supply rated for at least 4-5A (3A minimum for 2 servos)
- [ ] 5V (+) connects to 5V Power Rail
- [ ] 5V (-) connects to Common Ground
- [ ] **VERIFY**: Measure 5V between supply (+) and (-) before connecting servos

#### 3.3V Power (from Pico)
- [ ] Pico 3.3V connects to 74HC126 Pin 14 (VCC)
- [ ] Pico 3.3V connects to OLED VCC
- [ ] Pico 3.3V connects to DS3231 VCC
- [ ] **DO NOT connect servos to 3.3V!**

### 2. Ground Connections (CRITICAL!)

**All grounds MUST be connected together:**
- [ ] Pico GND connects to Common Ground
- [ ] 74HC126 Pin 7 (GND) connects to Common Ground
- [ ] Servo #1 Pin 1 (Black wire) connects to Common Ground
- [ ] Servo #2 Pin 1 (Black wire) connects to Common Ground
- [ ] 5V Supply (-) connects to Common Ground
- [ ] OLED GND connects to Common Ground
- [ ] DS3231 GND connects to Common Ground
- [ ] Rotary Encoder GND connects to Common Ground

**⚠️ CRITICAL**: Without common ground, servos will NOT communicate!

### 3. SN74HC126N Tri-State Buffer Wiring

#### 74HC126 Power
- [ ] Pin 14 (VCC) → Pico 3.3V (RED wire)
- [ ] Pin 7 (GND) → Common Ground (BLACK wire)

#### 74HC126 Gate 1 Connections (TX path)
- [ ] Pin 1 (1OE) → Pico GP2 (Direction Control)
- [ ] Pin 2 (1A) → Pico GP0 (UART TX)
- [ ] Pin 3 (1Y) → DATA BUS

#### 74HC126 Unused Pins
- [ ] Pins 4-6, 8-13 are NOT connected (only Gate 1 is used)

**⚠️ CRITICAL**: GP0 should ONLY connect to 74HC126 Pin 2, NOT directly to DATA BUS or Ground!

### 4. DATA BUS Connections

The DATA BUS is a shared communication line connecting:
- [ ] 74HC126 Pin 3 (1Y) → DATA BUS
- [ ] Pico GP1 (RX) → DATA BUS
- [ ] Servo #1 Pin 3 (Yellow wire) → DATA BUS
- [ ] Servo #2 Pin 3 (Yellow wire) → DATA BUS
- [ ] 10kΩ resistor → DATA BUS (one end)
- [ ] 10kΩ resistor → 5V Rail (other end)

**⚠️ CRITICAL**: 10kΩ pull-up resistor to 5V is REQUIRED!

### 5. Pico GPIO Connections

#### UART (DYNAMIXEL Communication)
- [ ] GP0 → 74HC126 Pin 2 (1A) - TX path
- [ ] GP1 → DATA BUS - RX path
- [ ] GP2 → 74HC126 Pin 1 (1OE) - Direction Control

#### I2C Bus
- [ ] GP4 → I2C SDA Bus (OLED + DS3231)
- [ ] GP5 → I2C SCL Bus (OLED + DS3231)

#### Rotary Encoder
- [ ] GP6 → Encoder Pin A
- [ ] GP7 → Encoder Pin B
- [ ] GP8 → Encoder Button/Switch

### 6. DYNAMIXEL Servo Connections

#### Servo #1 (LAN Motor - ID should be 1)
- [ ] Pin 1 (Black - GND) → Common Ground
- [ ] Pin 2 (Red - VDD) → 5V Power Rail
- [ ] Pin 3 (Yellow - DATA) → DATA BUS

#### Servo #2 (AOV Motor - ID should be 2)
- [ ] Pin 1 (Black - GND) → Common Ground
- [ ] Pin 2 (Red - VDD) → 5V Power Rail
- [ ] Pin 3 (Yellow - DATA) → DATA BUS

**⚠️ NOTE**: Both servos share the same DATA line (daisy-chain configuration)

### 7. Critical Component Checks

#### Pull-up Resistor
- [ ] 10kΩ resistor connected between DATA BUS and 5V rail
- [ ] **Measure**: ~10kΩ resistance between DATA line and 5V (with power OFF)

#### IC Power
- [ ] 74HC126 Pin 14 measures 3.3V relative to Pin 7 (with Pico powered)

#### Servo Power
- [ ] Servo VDD pins (Red wires) measure 5V relative to GND (with 5V supply ON)
- [ ] **DO NOT** power servos from Pico VBUS

---

## 🔍 Continuity Tests (Power OFF!)

Use a multimeter in continuity mode:

### Ground Continuity
- [ ] Pico GND ↔ 74HC126 Pin 7: Continuity
- [ ] Pico GND ↔ Servo #1 Pin 1: Continuity
- [ ] Pico GND ↔ Servo #2 Pin 1: Continuity
- [ ] Pico GND ↔ 5V Supply (-): Continuity

### DATA BUS Continuity
- [ ] GP1 ↔ Servo #1 Pin 3: Continuity
- [ ] GP1 ↔ Servo #2 Pin 3: Continuity
- [ ] GP1 ↔ 74HC126 Pin 3: Continuity
- [ ] GP1 ↔ 10kΩ resistor (one end): Continuity

### No Unwanted Connections
- [ ] GP0 ↔ GND: NO continuity (GP0 should NOT be grounded!)
- [ ] GP0 ↔ DATA BUS: NO continuity (GP0 only connects to 74HC126 Pin 2)
- [ ] 5V Rail ↔ 3.3V Rail: NO continuity (separate power rails!)

---

## ⚡ Voltage Tests (Power ON, Servos Disconnected)

### With Pico Powered (via USB)
- [ ] Pico 3.3V → GND: 3.2-3.4V
- [ ] 74HC126 Pin 14 → Pin 7: 3.2-3.4V

### With 5V External Supply ON
- [ ] 5V Rail → Common Ground: 4.8-5.2V
- [ ] DATA BUS → Common Ground: ~5V (due to pull-up resistor)

### With Both Powered
- [ ] Confirm 3.3V rail stable
- [ ] Confirm 5V rail stable
- [ ] No short circuits detected

---

## 🎯 Servo Configuration Verification

### Before Daisy-Chaining Both Servos

#### Servo #1 Setup (LAN Motor)
1. [ ] Connect ONLY Servo #1 to circuit
2. [ ] Upload `micropython/dynamixel_setup.py` to Pico
3. [ ] Run scan: `scan_servos()` - Should find exactly 1 servo
4. [ ] If found at ID ≠ 1: Run `change_id(current_id, 1)`
5. [ ] Verify: `ping(1)` succeeds

#### Servo #2 Setup (AOV Motor)
1. [ ] Disconnect Servo #1
2. [ ] Connect ONLY Servo #2 to circuit
3. [ ] Run scan: `scan_servos()` - Should find exactly 1 servo
4. [ ] If found at ID ≠ 2: Run `change_id(current_id, 2)`
5. [ ] Verify: `ping(2)` succeeds

#### Both Servos Together
1. [ ] Connect both servos in daisy-chain
2. [ ] Run scan: `scan_servos()` - Should find 2 servos
3. [ ] `ping(1)` succeeds
4. [ ] `ping(2)` succeeds

---

## 🔧 Functional Tests

### Direction Control Test
- [ ] GP2 = HIGH: Pico can transmit (74HC126 output enabled)
- [ ] GP2 = LOW: Pico can receive (74HC126 output tri-stated)

### Communication Test
```python
# Enable torque on Servo 1
set_torque(1, True)

# Move servo to center position
set_position(1, 2048)

# Servo should move smoothly
```

- [ ] Servo #1 responds to commands
- [ ] Servo #2 responds to commands
- [ ] No communication errors

### Motion Test
```python
# Test both servos independently
set_torque(1, True)
set_torque(2, True)

# Move LAN motor (Servo 1)
set_position(1, 1024)  # 90 degrees
time.sleep(2)
set_position(1, 3072)  # 270 degrees

# Move AOV motor (Servo 2)
set_position(2, 1024)  # 90 degrees
time.sleep(2)
set_position(2, 3072)  # 270 degrees
```

- [ ] Both servos move smoothly
- [ ] No stuttering or unexpected stops
- [ ] Position tracking is accurate

---

## ❌ Common Wiring Mistakes to Avoid

### 🚫 DON'T:
- [ ] Connect GP0 directly to DATA BUS (must go through 74HC126!)
- [ ] Connect GP0 to GND (common mistake!)
- [ ] Power servos from Pico VBUS or 3.3V (insufficient current!)
- [ ] Forget common ground (most common cause of communication failure!)
- [ ] Forget 10kΩ pull-up resistor (required for proper communication!)
- [ ] Use same ID for both servos (must be unique: 1 and 2!)
- [ ] Mix up 74HC126 pin numbering (verify with datasheet!)

### ✅ DO:
- [ ] Use external 5V power supply (4-5A rated)
- [ ] Connect all grounds together (common ground)
- [ ] Add 10kΩ pull-up from DATA to 5V
- [ ] Route GP0 through 74HC126 buffer
- [ ] Set unique IDs (1 and 2) before daisy-chaining
- [ ] Test each servo individually first
- [ ] Verify voltage levels before connecting servos

---

## 📊 Signal Flow Verification

### Transmit Mode (GP2 = HIGH)
```
Pico GP0 (TX) → 74HC126 Pin 2 → [Buffer ENABLED] → Pin 3 → DATA BUS → Both Servos
```
- [ ] GP2 reads HIGH
- [ ] 74HC126 Pin 1 (1OE) reads HIGH
- [ ] Data appears on DATA BUS when transmitting

### Receive Mode (GP2 = LOW)
```
Servo responds → DATA BUS → Pico GP1 (RX)
                          ↓
                 74HC126 Pin 3 [TRI-STATE/DISABLED]
```
- [ ] GP2 reads LOW
- [ ] 74HC126 Pin 1 (1OE) reads LOW
- [ ] 74HC126 Pin 3 is high-impedance (tri-stated)
- [ ] Pico GP1 receives data from servos

---

## 🎓 Reference Documents

For detailed wiring information, refer to:
1. `ORBIGATOR_COMPLETE_WIRING.txt` - Complete pin assignment table
2. `DYNAMIXEL_WIRING_DIAGRAM.txt` - ASCII circuit diagram
3. `DYNAMIXEL_Connection_with_74HC126.md` - Detailed guide with code examples
4. `DYNAMIXEL_Quick_Reference.md` - One-page cheat sheet

---

## ✅ Final Verification

Before declaring wiring complete:

- [ ] All power connections verified
- [ ] All ground connections verified
- [ ] All signal connections verified
- [ ] No short circuits detected
- [ ] Voltage levels correct (3.3V and 5V)
- [ ] 10kΩ pull-up resistor in place
- [ ] Both servos have unique IDs (1 and 2)
- [ ] Communication test passed
- [ ] Motion test passed
- [ ] Ready for integration with Orbigator!

---

**Date Checked**: _________________
**Checked By**: _________________
**Notes**:

_______________________________________________________________________

_______________________________________________________________________

_______________________________________________________________________

---

*Document Version: 1.0*
*Created: December 7, 2025*
*For Orbigator DYNAMIXEL Integration*
