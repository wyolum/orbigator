# Dynamixel XL330 Interface Circuit for Raspberry Pi Pico 2

## Circuit Overview

This document describes the half-duplex UART interface circuit required to connect a Raspberry Pi Pico 2 to Dynamixel XL330 servos.

---

## Complete Circuit Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI PICO 2                                │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Pin 1  (GP0)  UART0 TX ─────────────────┐                 │     │
│  │  Pin 2  (GP1)  UART0 RX ──────────┐      │                 │     │
│  │  Pin 4  (GP2)  Direction Control ─┼──┐   │                 │     │
│  │                                    │  │   │                 │     │
│  │  Pin 36 (3V3 OUT) ────────────────┼──┼───┼────────┐        │     │
│  │  Pin 38 (GND)     ────────────────┼──┼───┼────┐   │        │     │
│  └────────────────────────────────────┼──┼───┼────┼───┼────────┘     │
└───────────────────────────────────────┼──┼───┼────┼───┼──────────────┘
                                        │  │   │    │   │
                                        │  │   │    │   │
┌───────────────────────────────────────┼──┼───┼────┼───┼──────────────┐
│                  74HC04 HEX INVERTER                                  │
│                   (DIP-14 Package)                                    │
│                                                                       │
│     Pin 14 (VCC) ──────────────────────────────────────┼─────────────┤
│     Pin 7  (GND) ──────────────────────────────────────┼────────┐    │
│                                                         │        │    │
│     Pin 1  (1A - Input)  ─────────────────────────────┼┐       │    │
│     Pin 2  (1Y - Output) ──────────────────┐          ││       │    │
└────────────────────────────────────────────┼──────────┼┼───────┼────┘
                                             │          ││       │
                                             │          ││       │
┌────────────────────────────────────────────┼──────────┼┼───────┼────┐
│              74HC126 QUAD TRI-STATE BUFFER                            │
│                   (DIP-14 Package)                                    │
│                                                                       │
│     Pin 14 (VCC) ──────────────────────────────────────────────────┼─┤
│     Pin 7  (GND) ──────────────────────────────────────────────────┼─┤
│                                                                     │ │
│     ┌─────────────  Buffer 1 (TX Path)  ───────────────┐          │ │
│     │  Pin 1  (1A)   Input  ────────────────────────────┼──────────┘ │
│     │  Pin 2  (1OE)  Enable ────────────────────────────┼────────────┤
│     │  Pin 3  (1Y)   Output ───────────────────┐        │            │
│     └──────────────────────────────────────────┼────────┼────────────┤
│                                                 │        │            │
│     ┌─────────────  Buffer 2 (RX Path)  ───────┼────────┼────────────┤
│     │  Pin 4  (2A)   Input  ───────────────────┼────────┼────────┐   │
│     │  Pin 5  (2OE)  Enable ────────────────────────────┼────┐   │   │
│     │  Pin 6  (2Y)   Output ───────────────────┼────────┘    │   │   │
│     └──────────────────────────────────────────┼─────────────┼───┼───┤
│                                                 │             │   │   │
└─────────────────────────────────────────────────┼─────────────┼───┼───┘
                                                  │             │   │
                                                  │             │   │
                        ┌─────────────────────────┴─────────────┴───┴───┐
                        │        DYNAMIXEL DATA LINE (Half-Duplex)      │
                        │              JST 3-Pin Connector               │
                        │                                                │
                        │  Pin 1 (GND)  ────────────────────────────────┼─── GND
                        │  Pin 2 (VDD)  ────────────────────────────────┼─── 5V
                        │  Pin 3 (DATA) ─────────────────────────────────── DATA
                        │                                                │
                        └────────────────────────────────────────────────┘
                                      │
                              ┌───────┴────────┐
                              │  DYNAMIXEL     │
                              │  XL330-M288-T  │
                              │                │
                              │  5V @ 600mA    │
                              └────────────────┘
```

---

## Detailed Pin Connections

### Raspberry Pi Pico 2 Connections

| Pico Pin | GPIO | Function | Connects To |
|----------|------|----------|-------------|
| Pin 1 | GP0 | UART0 TX | 74HC126 Pin 1 (1A) |
| Pin 2 | GP1 | UART0 RX | 74HC126 Pin 6 (2Y) |
| Pin 4 | GP2 | Direction Control | 74HC04 Pin 1 (1A) |
| Pin 36 | 3V3(OUT) | 3.3V Power | 74HC126 VCC, 74HC04 VCC |
| Pin 38 | GND | Ground | 74HC126 GND, 74HC04 GND, XL330 GND |

### 74HC04 Hex Inverter Connections

| IC Pin | Function | Connects To |
|--------|----------|-------------|
| Pin 1 | 1A (Input) | Pico GP2 |
| Pin 2 | 1Y (Output) | 74HC126 Pin 2 (1OE) |
| Pin 7 | GND | Common Ground |
| Pin 14 | VCC | 3.3V |

### 74HC126 Quad Tri-State Buffer Connections

| IC Pin | Function | Connects To |
|--------|----------|-------------|
| Pin 1 | 1A (Buffer 1 Input) | Pico GP0 (TX) |
| Pin 2 | 1OE (Buffer 1 Enable) | 74HC04 Pin 2 (inverted GP2) |
| Pin 3 | 1Y (Buffer 1 Output) | XL330 Data + 74HC126 Pin 4 |
| Pin 4 | 2A (Buffer 2 Input) | XL330 Data |
| Pin 5 | 2OE (Buffer 2 Enable) | Pico GP2 (direct) |
| Pin 6 | 2Y (Buffer 2 Output) | Pico GP1 (RX) |
| Pin 7 | GND | Common Ground |
| Pin 14 | VCC | 3.3V |

### Dynamixel XL330 JST Connector

| Pin | Wire Color | Function | Connects To |
|-----|------------|----------|-------------|
| 1 | Black | GND | Common Ground |
| 2 | Red | VDD (5V) | External 5V Supply |
| 3 | Yellow/White | DATA | 74HC126 Pins 3 & 4 |

---

## How It Works

### Transmission (Pico → Servo)
1. Pico sets GP2 HIGH (transmit mode)
2. GP2 HIGH enables Buffer 1 (via inverter, makes 1OE LOW)
3. GP2 HIGH disables Buffer 2 (2OE HIGH)
4. Data flows: Pico TX (GP0) → Buffer 1 → Servo Data Line

### Reception (Servo → Pico)
1. Pico sets GP2 LOW (receive mode)
2. GP2 LOW disables Buffer 1 (via inverter, makes 1OE HIGH)
3. GP2 LOW enables Buffer 2 (2OE LOW)
4. Data flows: Servo Data Line → Buffer 2 → Pico RX (GP1)

---

## Power Supply Recommendations

### Option 1: Shared 5V Supply (Simple)
```
USB 5V Power Supply (1-2A)
    │
    ├──→ Pico VSYS (Pin 39)
    │
    └──→ XL330 VDD (Pin 2)

Common GND: Pico Pin 38 ↔ XL330 Pin 1
```

### Option 2: Separate Supplies (Safer)
```
USB Power → Pico USB Port (5V for Pico)

Wall Adapter (5V, 1-2A) → XL330 VDD

Common GND: Connect all grounds together
```

**Important:** XL330 can draw up to 600mA under load. Ensure your power supply can handle this!

---

## Bill of Materials

| Component | Specification | Quantity | Approx. Cost | Source |
|-----------|--------------|----------|--------------|--------|
| 74HC126N | Quad Tri-State Buffer (DIP-14) | 1 | $0.60-9.00 | DigiKey, Mouser, Amazon |
| 74HC04N | Hex Inverter (DIP-14) | 1 | $0.50-8.00 | DigiKey, Mouser, Amazon |
| Jumper Wires | Male-Male, 22-24 AWG | 10+ | Included | - |
| Breadboard | Standard 830 tie-point | 1 | Included | - |
| 5V Power Supply | 1-2A minimum | 1 | $5-10 | Any |
| XL330-M288-T | Dynamixel Servo | 1-2 | $27.49 ea | ROBOTIS, Tribotix |

**Total Circuit Cost:** ~$2-20 (depending on source)

---

## Assembly Instructions

### Step 1: Insert ICs into Breadboard
1. Place 74HC04 on breadboard
2. Place 74HC126 nearby on same breadboard
3. Ensure proper orientation (notch at top)

### Step 2: Power Connections
1. Connect Pin 14 of both ICs to 3.3V rail
2. Connect Pin 7 of both ICs to GND rail
3. Connect Pico 3.3V (Pin 36) to 3.3V rail
4. Connect Pico GND (Pin 38) to GND rail

### Step 3: Signal Connections
1. **GP0 (TX)** → 74HC126 Pin 1
2. **GP1 (RX)** → 74HC126 Pin 6
3. **GP2** → 74HC04 Pin 1
4. **GP2** → 74HC126 Pin 5
5. 74HC04 Pin 2 → 74HC126 Pin 2
6. 74HC126 Pin 3 → XL330 Data (Pin 3)
7. 74HC126 Pin 4 → XL330 Data (Pin 3)

### Step 4: Servo Connections
1. XL330 Pin 1 (GND) → Common GND
2. XL330 Pin 2 (VDD) → 5V Supply
3. XL330 Pin 3 (DATA) → 74HC126 data line

### Step 5: Verify
1. Check all power connections
2. Verify no short circuits
3. Power on and test with MicroPython code

---

## Alternative: Simple 3-Resistor Circuit

For quick testing (less reliable):

```
         PICO 2
           │
GP0 (TX) ──[1kΩ]──┬──→ XL330 Data (Pin 3)
                   │
GP1 (RX) ──────────┤
                   │
              [1kΩ]
                   │
                  GND

Note: This method is simpler but less reliable for
      high-speed communication. Use for testing only.
```

---

## MicroPython Code Example

```python
from machine import Pin, UART
import time

# Initialize UART and direction control
uart = UART(0, baudrate=57600, tx=Pin(0), rx=Pin(1))
direction_pin = Pin(2, Pin.OUT)

def send_packet(data):
    """Send data to Dynamixel"""
    direction_pin.value(1)  # TX mode
    time.sleep_us(10)
    uart.write(data)
    uart.flush()
    time.sleep_us(10)
    direction_pin.value(0)  # RX mode

def read_response():
    """Read response from Dynamixel"""
    direction_pin.value(0)  # RX mode
    time.sleep_ms(10)
    if uart.any():
        return uart.read()
    return None

# Example: Ping servo at ID 1
ping_packet = bytes([0xFF, 0xFF, 0xFD, 0x00, 0x01, 0x03, 0x00, 0x01, 0x19, 0x4E])
send_packet(ping_packet)
response = read_response()
print("Response:", response)
```

---

## Troubleshooting

### No Response from Servo
- Check power supply (needs 5V, not 3.3V!)
- Verify all ground connections are common
- Check servo ID matches in code
- Measure voltage at servo VDD pin (should be 5V)

### Garbled Data
- Verify baud rate (default 57600 for XL330)
- Check all signal connections
- Ensure direction control timing is correct
- Add delays between TX and RX switching

### Intermittent Communication
- Check breadboard contacts
- Verify IC orientation
- Ensure 3.3V supply is stable
- Try lowering baud rate

---

## Safety Notes

⚠️ **Important Safety Information:**

1. **Never exceed 6V** on XL330 VDD pin
2. **Check polarity** before connecting power
3. **Use common ground** for all components
4. **Don't hot-plug** servo while powered
5. **Limit current** to protect servo and Pico

---

## References

- [XL330-M288-T Manual](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/)
- [74HC126 Datasheet](https://www.ti.com/product/SN74HC126)
- [74HC04 Datasheet](https://www.ti.com/product/SN74HC04)
- [Raspberry Pi Pico 2 Pinout](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf)

---

**Document Version:** 1.0
**Date:** December 2024
**Project:** Orbigator - Orbital Mechanics Simulator
