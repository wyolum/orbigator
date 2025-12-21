# Orbigator Netlist

This netlist describes all electrical connections in the Orbigator circuit.

## Power Nets

### +5V (External Supply)
- J1 (Barrel Jack) Pin 1
- M1 (DYNAMIXEL 1) Pin 2 (VDD)
- M2 (DYNAMIXEL 2) Pin 2 (VDD)
- R1 (10kΩ) Pin 1

### +3.3V (from Pico)
- U1 (Pico 2) Pin 36 (3V3_OUT)
- U2 (74HC126) Pin 14 (VCC)
- DISP1 (OLED) VCC
- RTC1 (DS3231) VCC
- ENC1 (Encoder) VCC
- R2 (4.7kΩ) Pin 1
- R3 (4.7kΩ) Pin 1
- R4 (47Ω) Pin 1

### GND (Common Ground)
- J1 (Barrel Jack) Pin 2
- U1 (Pico 2) Pins 3, 38
- U2 (74HC126) Pin 7
- M1 (DYNAMIXEL 1) Pin 1
- M2 (DYNAMIXEL 2) Pin 1
- DISP1 (OLED) GND
- RTC1 (DS3231) GND
- ENC1 (Encoder) GND
- C1 (Supercap) Pin 2
- C2 (100nF) Pin 2
- C3 (100nF) Pin 2

## Signal Nets

### UART_TX (Pico → Buffer → Motors)
- U1 (Pico 2) Pin 1 (GP0)
- U2 (74HC126) Pin 2 (1A)

### UART_RX (Motors → Pico)
- U1 (Pico 2) Pin 2 (GP1)
- DATA_BUS (direct connection)

### DIR_PIN (Buffer Control)
- U1 (Pico 2) Pin 4 (GP2)
- U2 (74HC126) Pin 1 (1OE)

### DATA_BUS (Half-Duplex DYNAMIXEL)
- U2 (74HC126) Pin 3 (1Y)
- M1 (DYNAMIXEL 1) Pin 3 (DATA)
- M2 (DYNAMIXEL 2) Pin 3 (DATA)
- R1 (10kΩ) Pin 2 (pull-up to +5V)
- J2 (DYNAMIXEL Connector) Pin 3

### I2C_SDA (Shared Bus)
- U1 (Pico 2) Pin 6 (GP4)
- DISP1 (OLED) SDA
- RTC1 (DS3231) SDA
- R2 (4.7kΩ) Pin 2 (pull-up to +3.3V)

### I2C_SCL (Shared Bus)
- U1 (Pico 2) Pin 7 (GP5)
- DISP1 (OLED) SCL
- RTC1 (DS3231) SCL
- R3 (4.7kΩ) Pin 2 (pull-up to +3.3V)

### ENC_A (Encoder Channel A)
- U1 (Pico 2) Pin 9 (GP6)
- ENC1 (Encoder) Pin A
- J3 (Encoder Connector) Pin 1

### ENC_B (Encoder Channel B)
- U1 (Pico 2) Pin 10 (GP7)
- ENC1 (Encoder) Pin B
- J3 (Encoder Connector) Pin 2

### ENC_SW (Encoder Switch)
- U1 (Pico 2) Pin 11 (GP8)
- ENC1 (Encoder) Pin SW
- J3 (Encoder Connector) Pin 3

### RTC_BAT (Backup Power)
- RTC1 (DS3231) BAT pin
- R4 (47Ω) Pin 2
- C1 (Supercap) Pin 1

## Net Summary

| Net Name | Connection Count | Notes |
|----------|------------------|-------|
| +5V | 5 | External supply, 4-5A required |
| +3.3V | 9 | From Pico, low current |
| GND | 13 | Common ground |
| DATA_BUS | 5 | Half-duplex, needs 10kΩ pull-up |
| I2C_SDA | 4 | Multi-device bus, needs 4.7kΩ pull-up |
| I2C_SCL | 4 | Multi-device bus, needs 4.7kΩ pull-up |
| UART_TX | 2 | Pico to buffer |
| UART_RX | 2 | Motors to Pico |
| DIR_PIN | 2 | Buffer direction control |
| ENC_A | 3 | Encoder channel A |
| ENC_B | 3 | Encoder channel B |
| ENC_SW | 3 | Encoder button |
| RTC_BAT | 3 | Supercap backup circuit |

## Design Rules

### Trace Widths
- Power (+5V, GND): 1.0mm minimum (motor current)
- +3.3V: 0.5mm minimum
- Signal traces: 0.25mm minimum
- I2C, UART: 0.25mm (short traces, low speed)

### Clearances
- Minimum clearance: 0.2mm
- Power to signal: 0.3mm recommended

### Via Specifications
- Standard via: 0.8mm diameter, 0.4mm drill
- Power vias: Multiple vias for high current paths

## Layout Recommendations

1. **Keep I2C traces short** - Minimize capacitance
2. **Place pull-up resistors near devices** - R2/R3 near Pico, R1 near motors
3. **Separate power planes** - Keep 5V and 3.3V domains clear
4. **Decoupling capacitors** - Place C2 near 74HC126, C3 near Pico
5. **Motor connector placement** - Easy cable routing to motors
6. **Encoder connector** - Accessible for user interaction

## Testing Points

Recommended test points for debugging:
- TP1: +5V
- TP2: +3.3V
- TP3: GND
- TP4: DATA_BUS
- TP5: I2C_SDA
- TP6: I2C_SCL
- TP7: UART_TX
- TP8: UART_RX
