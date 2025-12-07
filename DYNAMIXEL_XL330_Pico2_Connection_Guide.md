# DYNAMIXEL XL330-M288-T to Raspberry Pi Pico 2 Connection Guide

## Overview
This guide provides detailed instructions for connecting DYNAMIXEL XL330-M288-T servo motors to the Raspberry Pi Pico 2 for the Orbigator project.

## DYNAMIXEL XL330-M288-T Specifications

### Key Specifications
- **Dimensions:** 20 × 34 × 25 mm
- **Weight:** 18 g
- **Input Voltage:** 3.7V to 6V (5V recommended)
- **Stall Torque (at 5V):** 0.52 N·m
- **Stall Current (at 5V):** 1.5 A per servo
- **No-load Speed (at 5V):** 104 rpm
- **Communication Protocol:** Half-Duplex TTL (3.3V logic, 5V compatible)
- **Baud Rate:** 9,600 bps to 4.5 Mbps (Default: 57,600 bps)
- **Default ID:** 1
- **Gear Reduction Ratio:** 288.4:1
- **Resolution:** 0.088° (4096 steps)
- **Protocol:** DYNAMIXEL Protocol 2.0

### Connector Pinout (JST EHR-03)
The DYNAMIXEL XL330-M288-T uses a 3-pin JST connector:

1. **Pin 1 (GND)** - Ground (Black wire)
2. **Pin 2 (VDD)** - Power Supply 5V (Red wire)
3. **Pin 3 (DATA)** - Half-Duplex TTL Serial Data (Yellow/White wire)

**Note:** The PCB header is JST B3B-EH-A

## Wiring Connections

### Required Components
1. Raspberry Pi Pico 2
2. DYNAMIXEL XL330-M288-T servo(s)
3. External 5V power supply (2A minimum per servo)
4. 4.7kΩ resistor (for half-duplex conversion)
5. Connecting wires
6. Common ground connection

### Pin Connections

#### Power Connections
- **Servo VDD (Pin 2, Red)** → External 5V Power Supply (+)
- **Servo GND (Pin 1, Black)** → Common Ground
- **Pico GND** → Common Ground
- **External 5V Power Supply (-)** → Common Ground

**IMPORTANT:** Do NOT power the servos from the Pico's VBUS or 3V3 pins. Each servo can draw up to 1.5A at stall, which exceeds the Pico's capabilities. Use a dedicated 5V power supply rated for at least 2A per servo.

#### Communication Connections (Half-Duplex UART)
The DYNAMIXEL uses half-duplex communication (single data line for both TX and RX), while the Pico's UART is full-duplex (separate TX and RX lines). We need to combine them:

**Method 1: Resistor-Based (Recommended)**
- **Pico GP1 (UART0 RX)** → **Servo DATA (Pin 3, Yellow)**
- **Pico GP0 (UART0 TX)** → **4.7kΩ Resistor** → **Servo DATA (Pin 3, Yellow)**

**Method 2: Direct Connection (Simpler, but less robust)**
- **Pico GP0 (UART0 TX)** → **Servo DATA (Pin 3, Yellow)**
- **Pico GP1 (UART0 RX)** → **Servo DATA (Pin 3, Yellow)**

The resistor method is more robust and prevents potential conflicts when both the Pico and servo try to drive the line simultaneously.

### Alternative UART Pins
If UART0 (GP0/GP1) is already in use, you can use UART1:
- **UART1 Option A:** GP4 (TX), GP5 (RX)
- **UART1 Option B:** GP8 (TX), GP9 (RX)

**Note:** For Orbigator, GP4/GP5 are currently used for I2C (OLED), so use UART0 or consider GP8/GP9 for UART1.

## Daisy-Chain Configuration (Multiple Servos)

DYNAMIXEL servos support daisy-chaining, allowing multiple servos to share the same communication line:

```
Pico UART ←→ Servo 1 ←→ Servo 2 ←→ Servo 3 ...
```

### Daisy-Chain Wiring
1. Connect the first servo to the Pico as described above
2. Connect subsequent servos in series using X3P cables
3. Each servo must have a unique ID (1, 2, 3, etc.)
4. All servos share the same power supply and data line

### Power Considerations for Multiple Servos
- Calculate total current: Number of servos × 1.5A (stall current)
- Use a power supply rated for total current + 20% margin
- Example: 3 servos = 3 × 1.5A = 4.5A → Use 5-6A power supply

## Software Configuration (MicroPython)

### Basic UART Setup
```python
from machine import UART, Pin
import time

# Initialize UART for DYNAMIXEL communication
# Using UART0: TX=GP0, RX=GP1
uart = UART(0, baudrate=57600, bits=8, parity=None, stop=1)
uart.init(baudrate=57600, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))

# For UART1 (if needed):
# uart = UART(1, baudrate=57600, bits=8, parity=None, stop=1)
# uart.init(baudrate=57600, bits=8, parity=None, stop=1, tx=Pin(8), rx=Pin(9))
```

### DYNAMIXEL Protocol 2.0 Library
There are MicroPython libraries available for DYNAMIXEL control:
- GitHub: `micropython-dynamixel` (supports XL330 series)
- Implements Protocol 2.0 packet structure
- Handles half-duplex communication timing

### Basic Communication Example
```python
# Example: Read present position from servo ID 1
def read_position(servo_id=1):
    # Build Protocol 2.0 packet
    # [0xFF, 0xFF, 0xFD, 0x00, ID, LEN_L, LEN_H, INST, PARAM..., CRC_L, CRC_H]
    # This is simplified - use a proper library for production code
    pass

# Example: Set goal position
def set_position(servo_id=1, position=2048):
    # Build Protocol 2.0 packet to write goal position
    # Address for Goal Position: 116 (0x0074)
    pass
```

## Orbigator Integration Notes

### Current Pin Usage (from orbigator.py)
- **LAN Motor (DRV8834):** GP10-GP15
- **AOV Motor (ULN2003):** GP2, GP3, GP22, GP26
- **Encoder:** GP6, GP7, GP8
- **I2C (OLED/RTC):** GP4, GP5

### Recommended UART Pins for DYNAMIXEL
Since GP0 and GP1 are currently unused in the Orbigator code, use **UART0**:
- **GP0 (TX)** - Available
- **GP1 (RX)** - Available

### Migration Strategy
When replacing stepper motors with DYNAMIXEL servos:

1. **LAN Motor Replacement:**
   - Remove DRV8834 connections (GP10-GP15)
   - Connect LAN DYNAMIXEL to UART0 (GP0/GP1) with ID=1
   - Update code to use DYNAMIXEL position control instead of step pulses

2. **AOV Motor Replacement:**
   - Remove ULN2003 connections (GP2, GP3, GP22, GP26)
   - Connect AOV DYNAMIXEL to same UART (daisy-chain) with ID=2
   - Update code to use DYNAMIXEL position control

3. **Code Changes:**
   - Replace `lan_move_steps()` with DYNAMIXEL position commands
   - Replace `aov_move_steps()` with DYNAMIXEL position commands
   - Use DYNAMIXEL's built-in position feedback for accurate tracking
   - Leverage DYNAMIXEL's velocity and acceleration profiles

## Testing Procedure

### Step 1: Single Servo Test
1. Connect one servo (ID=1) to Pico as described
2. Power on external 5V supply
3. Send ping command to verify communication
4. Read present position
5. Command small position change
6. Verify servo moves correctly

### Step 2: Daisy-Chain Test (if using multiple servos)
1. Connect second servo in daisy-chain
2. Set second servo to ID=2 (use DYNAMIXEL Wizard if needed)
3. Ping both servos individually
4. Command each servo independently
5. Verify no communication conflicts

### Step 3: Integration Test
1. Replace motor control functions in orbigator.py
2. Test altitude-based motion calculations
3. Verify smooth orbital motion
4. Test state persistence and catch-up on restart

## Troubleshooting

### No Communication
- Check baud rate (default: 57600)
- Verify common ground connection
- Check DATA line connections
- Try direct connection method instead of resistor method
- Use logic analyzer to verify UART signals

### Servo Not Moving
- Check power supply voltage (should be 5V)
- Verify sufficient current capacity (1.5A per servo)
- Check if torque is enabled (DYNAMIXEL register)
- Verify goal position is within valid range (0-4095)

### Erratic Behavior
- Check for loose connections
- Verify power supply stability
- Add decoupling capacitors near servo power pins (100µF + 0.1µF)
- Reduce baud rate if communication errors occur

### Multiple Servos Conflict
- Ensure each servo has unique ID
- Check that all servos are properly daisy-chained
- Verify power supply can handle total current draw

## Additional Resources

- **DYNAMIXEL e-Manual:** https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/
- **Protocol 2.0 Specification:** https://emanual.robotis.com/docs/en/dxl/protocol2/
- **ROBOTIS Support:** https://www.robotis.com/
- **MicroPython DYNAMIXEL Library:** Search GitHub for "micropython dynamixel xl330"

## Bill of Materials

| Item | Quantity | Notes |
|------|----------|-------|
| DYNAMIXEL XL330-M288-T | 2 | One for LAN, one for AOV |
| Raspberry Pi Pico 2 | 1 | Already in use |
| 5V Power Supply | 1 | 4-5A recommended for 2 servos |
| 4.7kΩ Resistor | 1 | For half-duplex conversion |
| X3P Robot Cable (180mm) | 1-2 | Usually included with servos |
| Jumper Wires | Several | For Pico connections |
| JST Connector Adapter | Optional | If needed for prototyping |

## Safety Notes

1. **Never hot-plug servos** - Always power off before connecting/disconnecting
2. **Check polarity** - Reversed power can damage servos
3. **Current limiting** - Use appropriate power supply with overcurrent protection
4. **Heat management** - Servos can get warm under continuous load
5. **Mechanical stops** - Ensure servo horn won't hit physical obstacles

---

**Document prepared for:** Anool  
**Project:** Orbigator - Orbital Mechanics Simulator  
**Date:** December 7, 2025  
**Prepared by:** Justin (with Antigravity AI assistance)
