# DYNAMIXEL XL330-M288-T Connection Guide Using SN74HC126N
## For Raspberry Pi Pico 2 - Orbigator Project

## Overview
This guide shows how to properly connect **2 DYNAMIXEL XL330-M288-T servos** to the Raspberry Pi Pico 2 using the **SN74HC126N** tri-state buffer for reliable half-duplex UART communication.

## Why Use the SN74HC126N?

The **SN74HC126N** is a quad tri-state buffer that provides proper half-duplex communication control:
- **Direction Control**: Uses a GPIO pin to switch between TX and RX modes
- **Signal Integrity**: Prevents bus contention and signal conflicts
- **Professional Solution**: Industry-standard approach for DYNAMIXEL communication
- **Better than resistor method**: More reliable and robust

## Parts List (For 2 Motors)

### Required Components
| Quantity | Part | Notes |
|----------|------|-------|
| 2 | DYNAMIXEL XL330-M288-T | Servo motors |
| 1 | Raspberry Pi Pico 2 | Microcontroller |
| 1 | SN74HC126N | Quad tri-state buffer (14-pin DIP) |
| 1 | 74HC04 (or 74HC14) | Hex inverter (optional, see note below) |
| 1 | 10kΩ resistor | Pull-up for DATA line |
| 1 | 5V Power Supply | 4-5A minimum for 2 servos |
| 1 | Breadboard or PCB | For prototyping |
| - | Jumper wires | Various lengths |
| 1-2 | X3P Robot Cable | Usually included with servos |
| - | 0.1µF ceramic capacitors | Decoupling (recommended) |

**Note on Inverter**: Some designs use a 74HC04 inverter, but you can manage the logic in software instead. See the software section for details.

## SN74HC126N Pinout Reference

```
        SN74HC126N (Top View)
        ┌─────┬─────┐
   1OE  │1   ┴   14│ VCC (3.3V)
   1A   │2       13│ 4OE
   1Y   │3       12│ 4A
   2OE  │4       11│ 4Y
   2A   │5       10│ 3OE
   2Y   │6        9│ 3A
   GND  │7        8│ 3Y
        └───────────┘
```

**Pin Functions:**
- **nOE** (Output Enable): When LOW, output is high-impedance (tri-state). When HIGH, output follows input.
- **nA** (Input): Signal input
- **nY** (Output): Signal output (tri-state capable)

## Circuit Connections

### Power Connections
```
Pico 3.3V → SN74HC126 Pin 14 (VCC)
Pico GND → SN74HC126 Pin 7 (GND)
Pico GND → Common Ground Rail
External 5V (+) → DYNAMIXEL VDD (Pin 2, Red wire)
External 5V (-) → Common Ground Rail
```

### UART and Control Connections

#### Using Gate 1 for TX (Pico → DYNAMIXEL)
```
Pico GP0 (UART0 TX) → SN74HC126 Pin 2 (1A)
Pico GP2 (Direction) → SN74HC126 Pin 1 (1OE)
SN74HC126 Pin 3 (1Y) → DYNAMIXEL DATA line
```

#### RX Connection (DYNAMIXEL → Pico)
```
DYNAMIXEL DATA line → Pico GP1 (UART0 RX) [Direct connection]
```

#### DATA Line Pull-up
```
DYNAMIXEL DATA line → 10kΩ resistor → 5V
```

### Complete Pin Assignment for Pico 2

| Pico Pin | Function | Connection |
|----------|----------|------------|
| GP0 | UART0 TX | SN74HC126 Pin 2 (1A) |
| GP1 | UART0 RX | DYNAMIXEL DATA + 10kΩ pull-up to 5V |
| GP2 | Direction Control | SN74HC126 Pin 1 (1OE) |
| 3.3V | Power | SN74HC126 Pin 14 |
| GND | Ground | Common ground |

### DYNAMIXEL Connections (Daisy-Chain for 2 Motors)

```
Pico UART ←→ Servo 1 (ID=1) ←→ Servo 2 (ID=2)
              [LAN Motor]        [AOV Motor]
```

Both servos share:
- Same DATA line (daisy-chained via X3P cables)
- Same 5V power supply
- Common ground

**Important**: Each servo must have a unique ID (set ID=1 for LAN, ID=2 for AOV)

## Detailed Wiring Diagram

### Method 1: Without Inverter (Recommended for simplicity)

```
                    ┌─────────────┐
                    │  Pico 2     │
                    │             │
         GP0 (TX) ──┤             │
         GP1 (RX) ──┤             │
         GP2 (DIR)──┤             │
         3.3V ──────┤             │
         GND ───────┤             │
                    └─────────────┘
                          │ │ │ │ │
                          │ │ │ │ └─────────────┐
                          │ │ │ └───────────┐   │
                          │ │ └─────────┐   │   │
                          │ └───────┐   │   │   │
                          └─────┐   │   │   │   │
                                │   │   │   │   │
                    ┌───────────┴───┴───┴───┴───┴─┐
                    │      SN74HC126N              │
                    │  Pin2(1A)  Pin1(1OE)  Pin14  │ Pin7
                    │     │         │        │     │  │
                    │  Pin3(1Y)                    │  │
                    └─────┬────────────────────────┴──┴──┐
                          │                           │  │
                          │                          3.3V GND
                          │
                          │        10kΩ
                          ├─────────/\/\/\──────┐
                          │                     │
                          │                    5V
                          │
                          ├─────────────────────┐ (to GP1)
                          │                     │
                          │                     │
                    ┌─────┴─────┐         ┌─────┴─────┐
                    │ Servo 1   │         │ Servo 2   │
                    │ (ID=1)    │◄───────►│ (ID=2)    │
                    │ LAN Motor │         │ AOV Motor │
                    └───────────┘         └───────────┘
                      GND VDD DATA         GND VDD DATA
                       │   │   │            │   │   │
                       │   │   └────────────┴───┘   │
                       │   │                        │
                       │   └────────────────────────┘
                       │                      │
                       └──────────────────────┴─── Common GND
                                              │
                                         5V Supply
                                         (4-5A)
```

### Direction Control Logic (Software-Managed)

When **GP2 = HIGH**: 
- SN74HC126 output is **enabled**
- Pico TX drives the DATA line
- **Transmit mode**

When **GP2 = LOW**:
- SN74HC126 output is **tri-state** (high-impedance)
- DATA line is free for DYNAMIXEL to respond
- Pico RX receives data
- **Receive mode**

## Software Implementation (MicroPython)

### Pin Setup
```python
from machine import UART, Pin
import time

# UART pins
uart = UART(0, baudrate=57600, bits=8, parity=None, stop=1)
uart.init(tx=Pin(0), rx=Pin(1))

# Direction control pin
dir_pin = Pin(2, Pin.OUT)
dir_pin.value(0)  # Start in receive mode

# Direction control functions
def set_tx_mode():
    """Enable transmit mode"""
    dir_pin.value(1)
    time.sleep_us(10)  # Small delay for buffer to enable

def set_rx_mode():
    """Enable receive mode"""
    dir_pin.value(0)
    time.sleep_us(10)  # Small delay for buffer to tri-state
```

### Basic Communication Pattern
```python
def send_packet(packet_bytes):
    """Send a packet to DYNAMIXEL"""
    set_tx_mode()
    uart.write(packet_bytes)
    uart.flush()  # Wait for transmission to complete
    set_rx_mode()

def receive_response(timeout_ms=100):
    """Receive response from DYNAMIXEL"""
    set_rx_mode()  # Ensure we're in receive mode
    start = time.ticks_ms()
    response = bytearray()
    
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        if uart.any():
            response.extend(uart.read())
            # Check if we have a complete packet
            if len(response) >= 11:  # Minimum packet size
                break
    
    return bytes(response)

def communicate(tx_packet):
    """Send packet and receive response"""
    send_packet(tx_packet)
    return receive_response()
```

### DYNAMIXEL Protocol 2.0 Helper Functions

```python
def calculate_crc(data):
    """Calculate CRC for Protocol 2.0"""
    crc_table = [
        0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
        # ... (full CRC table - see DYNAMIXEL documentation)
    ]
    crc = 0
    for byte in data:
        i = ((crc >> 8) ^ byte) & 0xFF
        crc = ((crc << 8) ^ crc_table[i]) & 0xFFFF
    return crc

def make_packet(servo_id, instruction, params=[]):
    """Build a DYNAMIXEL Protocol 2.0 packet"""
    # Header
    packet = bytearray([0xFF, 0xFF, 0xFD, 0x00])
    # ID
    packet.append(servo_id)
    # Length (params + 3)
    length = len(params) + 3
    packet.extend([length & 0xFF, (length >> 8) & 0xFF])
    # Instruction
    packet.append(instruction)
    # Parameters
    packet.extend(params)
    # CRC
    crc = calculate_crc(packet)
    packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    
    return bytes(packet)

# Instruction set
INST_PING = 0x01
INST_READ = 0x02
INST_WRITE = 0x03
INST_REG_WRITE = 0x04
INST_ACTION = 0x05
INST_SYNC_WRITE = 0x83

# Common addresses for XL330
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
```

### Example: Ping Servo
```python
def ping_servo(servo_id):
    """Ping a servo to check if it's connected"""
    packet = make_packet(servo_id, INST_PING, [])
    response = communicate(packet)
    
    if len(response) > 0:
        print(f"Servo {servo_id} responded!")
        return True
    else:
        print(f"Servo {servo_id} no response")
        return False

# Test both servos
ping_servo(1)  # LAN motor
ping_servo(2)  # AOV motor
```

### Example: Set Position
```python
def set_goal_position(servo_id, position):
    """Set goal position (0-4095)"""
    # Goal Position is 4 bytes (32-bit)
    params = [
        ADDR_GOAL_POSITION & 0xFF,
        (ADDR_GOAL_POSITION >> 8) & 0xFF,
        position & 0xFF,
        (position >> 8) & 0xFF,
        (position >> 16) & 0xFF,
        (position >> 24) & 0xFF
    ]
    packet = make_packet(servo_id, INST_WRITE, params)
    communicate(packet)

# Example: Move LAN motor to 90 degrees
# 4096 steps per revolution, so 90° = 1024
set_goal_position(1, 1024)
```

### Example: Enable Torque
```python
def enable_torque(servo_id, enable=True):
    """Enable or disable torque"""
    params = [
        ADDR_TORQUE_ENABLE & 0xFF,
        (ADDR_TORQUE_ENABLE >> 8) & 0xFF,
        1 if enable else 0
    ]
    packet = make_packet(servo_id, INST_WRITE, params)
    communicate(packet)

# Enable both motors
enable_torque(1, True)  # LAN
enable_torque(2, True)  # AOV
```

## Integration with Orbigator

### Current Pin Usage
Your current `orbigator.py` uses:
- **GP0, GP1**: Available ✓ (Perfect for UART0)
- **GP2**: Available ✓ (Perfect for direction control)
- **GP4, GP5**: I2C (OLED/RTC)
- **GP6, GP7, GP8**: Encoder
- **GP10-GP15**: LAN stepper (will be replaced)
- **GP2, GP3, GP22, GP26**: AOV stepper (will be replaced)

### Migration Steps

1. **Remove old motor code** (DRV8834 and ULN2003 sections)
2. **Add DYNAMIXEL communication** (direction control + UART)
3. **Replace motor functions**:
   - `lan_move_steps()` → `set_goal_position(1, position)`
   - `aov_move_steps()` → `set_goal_position(2, position)`
4. **Update position tracking** (use DYNAMIXEL feedback)

### Example Replacement Functions

```python
# Replace in orbigator.py

def lan_move_to_angle(angle_deg):
    """Move LAN motor to specific angle"""
    # Convert angle to DYNAMIXEL position (0-4095)
    position = int((angle_deg / 360.0) * 4095)
    position = max(0, min(4095, position))
    set_goal_position(1, position)

def aov_move_to_angle(angle_deg):
    """Move AOV motor to specific angle"""
    position = int((angle_deg / 360.0) * 4095)
    position = max(0, min(4095, position))
    set_goal_position(2, position)

def read_lan_position():
    """Read current LAN position"""
    # Read present position from servo 1
    # Returns angle in degrees
    # (Implementation requires READ instruction)
    pass

def read_aov_position():
    """Read current AOV position"""
    # Read present position from servo 2
    pass
```

## Testing Procedure

### Step 1: Hardware Setup
1. ✓ Wire SN74HC126 to Pico as shown
2. ✓ Connect 10kΩ pull-up resistor to DATA line
3. ✓ Connect first servo (ID=1) to circuit
4. ✓ Connect 5V power supply (ensure common ground)
5. ✓ Add decoupling capacitors near IC and servos

### Step 2: Single Servo Test
```python
# Test script
from machine import UART, Pin
import time

# Setup
uart = UART(0, baudrate=57600, tx=Pin(0), rx=Pin(1))
dir_pin = Pin(2, Pin.OUT, value=0)

# Ping test
print("Testing servo communication...")
ping_servo(1)

# Enable torque
enable_torque(1, True)
time.sleep(0.5)

# Move to center
set_goal_position(1, 2048)
time.sleep(2)

# Move to 90°
set_goal_position(1, 1024)
time.sleep(2)

# Move to 270°
set_goal_position(1, 3072)
```

### Step 3: Daisy-Chain Test
1. Connect second servo in daisy-chain
2. Set second servo to ID=2 (use DYNAMIXEL Wizard or write command)
3. Test both servos independently
4. Verify no communication conflicts

### Step 4: Full Integration
1. Update `orbigator.py` with DYNAMIXEL functions
2. Test orbital motion calculations
3. Verify smooth operation
4. Test state save/restore

## Troubleshooting

### No Communication
- ✓ Check direction control logic (GP2 high for TX, low for RX)
- ✓ Verify SN74HC126 power (3.3V on pin 14)
- ✓ Check common ground between all components
- ✓ Verify UART baud rate (57600 default)
- ✓ Test with logic analyzer if available

### Servo Not Responding
- ✓ Check 5V power supply (must be 4.5V-6V)
- ✓ Verify servo ID matches command
- ✓ Check 10kΩ pull-up resistor is connected
- ✓ Ensure torque is enabled before moving

### Erratic Behavior
- ✓ Add 0.1µF capacitor between SN74HC126 VCC and GND
- ✓ Add 100µF capacitor near servo power pins
- ✓ Shorten wire lengths if possible
- ✓ Check for loose connections

### Direction Control Issues
- ✓ Verify GP2 toggles correctly (use oscilloscope/logic analyzer)
- ✓ Ensure delays after switching modes (10µs minimum)
- ✓ Check that uart.flush() completes before switching to RX

## Advanced: Using 74HC04 Inverter (Optional)

If you want to use separate enable pins for TX and RX buffers:

```
GP2 → 74HC04 → SN74HC126 Pin 1 (1OE) [TX enable]
GP2 → SN74HC126 Pin 4 (2OE) [RX enable, inverted]
```

This way:
- When GP2=HIGH: TX enabled, RX disabled
- When GP2=LOW: TX disabled, RX enabled

But this is optional - the simple method works fine!

## Bill of Materials Summary

| Item | Qty | Est. Cost | Notes |
|------|-----|-----------|-------|
| DYNAMIXEL XL330-M288-T | 2 | ~$50 ea | Servo motors |
| SN74HC126N | 1 | ~$0.50 | Tri-state buffer |
| 10kΩ resistor | 1 | ~$0.05 | Pull-up |
| 5V 5A power supply | 1 | ~$10 | For servos |
| 0.1µF capacitors | 3-4 | ~$0.10 ea | Decoupling |
| Breadboard/PCB | 1 | ~$5 | Prototyping |
| Jumper wires | Set | ~$5 | Connections |

**Total estimated cost:** ~$120-130

## References

- [DYNAMIXEL XL330 e-Manual](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/)
- [Protocol 2.0 Specification](https://emanual.robotis.com/docs/en/dxl/protocol2/)
- [SN74HC126 Datasheet](https://www.ti.com/product/SN74HC126)
- [ROBOTIS Support](https://www.robotis.com/)

---

**Prepared for:** Anool  
**Project:** Orbigator - DYNAMIXEL Integration  
**Date:** December 7, 2025  
**Author:** Justin
