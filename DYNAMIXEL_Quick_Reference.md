# DYNAMIXEL XL330 Quick Reference - Orbigator

## Quick Connection Summary (Using SN74HC126N)

### Parts Needed (2 Motors)
- 2× DYNAMIXEL XL330-M288-T servos
- 1× SN74HC126N tri-state buffer IC
- 1× 10kΩ resistor
- 1× 5V 4-5A power supply
- Jumper wires

### Pin Connections

**Pico 2 → SN74HC126:**
- GP0 (TX) → Pin 2 (1A)
- GP2 (DIR) → Pin 1 (1OE)
- 3.3V → Pin 14 (VCC)
- GND → Pin 7 (GND)

**SN74HC126 → DYNAMIXEL:**
- Pin 3 (1Y) → DATA line

**Direct Connections:**
- GP1 (RX) → DATA line
- DATA line → 10kΩ → 5V
- 5V Supply → Servo VDD (Pin 2, Red)
- GND → Servo GND (Pin 1, Black)

### Servo IDs
| Servo ID | Motor Type | Function |
|----------|------------|----------|
| 1 | LAN Motor | Longitude of Ascending Node (0-360°) |
| 2 | AoV Motor | Argument of Vehicle (orbital position: 0°=equator↑, 90°=max lat, 180°=equator↓, 270°=min lat) |

### Direction Control Logic
- **GP2 = HIGH**: Transmit mode (Pico sends data)
- **GP2 = LOW**: Receive mode (Servo responds)

### Basic Code Template

```python
from machine import UART, Pin

# Setup
uart = UART(0, baudrate=57600, tx=Pin(0), rx=Pin(1))
dir_pin = Pin(2, Pin.OUT, value=0)

def set_tx_mode():
    dir_pin.value(1)

def set_rx_mode():
    dir_pin.value(0)

# Send command
set_tx_mode()
uart.write(packet)
uart.flush()
set_rx_mode()

# Receive response
response = uart.read()
```

### Key Specifications
- Voltage: 5V (range: 3.7-6V)
- Current: 1.5A per servo (stall)
- Resolution: 4096 steps/rev (0.088°)
- Baud: 57600 bps (default)
- Protocol: DYNAMIXEL 2.0
- Connector: JST EHR-03

### Important Addresses (Protocol 2.0)
- Torque Enable: 64
- Goal Position: 116
- Present Position: 132

### Daisy-Chain Setup
Both servos connect to same DATA line. Each needs unique ID.

```
Pico ←→ Servo 1 (ID=1) ←→ Servo 2 (ID=2)
```

## See Full Documentation
- `DYNAMIXEL_Connection_with_74HC126.md` - Complete guide
- `DYNAMIXEL_XL330_Pico2_Connection_Guide.md` - Alternative methods
