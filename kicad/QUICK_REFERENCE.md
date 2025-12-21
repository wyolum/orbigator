# Quick Reference Card - Orbigator PCB

## Critical Components (Don't Forget!)

### I2C Pull-ups ⚠️ CRITICAL
```
R2: 4.7kΩ from SDA (GP4) to +3.3V
R3: 4.7kΩ from SCL (GP5) to +3.3V
```
**Without these, OLED will glitch and RTC will fail!**

### DYNAMIXEL Pull-up ⚠️ CRITICAL
```
R1: 10kΩ from DATA bus to +5V (NOT +3.3V!)
```

### RTC Backup Power
```
R4: 47Ω from +3.3V to supercap
C1: 0.47F supercap to GND (watch polarity!)
```

## Pin Connections Quick Reference

### Raspberry Pi Pico 2 (U1)
| Pin | GPIO | Function | Connects To |
|-----|------|----------|-------------|
| 1 | GP0 | UART TX | 74HC126 Pin 2 |
| 2 | GP1 | UART RX | DATA_BUS |
| 4 | GP2 | DIR | 74HC126 Pin 1 |
| 6 | GP4 | I2C SDA | OLED, RTC, R2 |
| 7 | GP5 | I2C SCL | OLED, RTC, R3 |
| 9 | GP6 | ENC A | Encoder A |
| 10 | GP7 | ENC B | Encoder B |
| 11 | GP8 | ENC SW | Encoder Switch |
| 36 | 3V3_OUT | Power | All 3.3V devices |
| 3, 38 | GND | Ground | Common ground |

### 74HC126 Buffer (U2)
| Pin | Function | Connects To |
|-----|----------|-------------|
| 1 | 1OE | Pico GP2 |
| 2 | 1A | Pico GP0 |
| 3 | 1Y | DATA_BUS |
| 7 | GND | Ground |
| 14 | VCC | +3.3V |

### Power Distribution
```
+5V:  J1 → M1, M2, R1
+3.3V: Pico Pin 36 → U2, DISP1, RTC1, ENC1, R2, R3, R4
GND: Common to all
```

## Board Dimensions
- **Size**: 55mm × 70mm (rotated 90° on A4 sheet)
- **Mounting Holes**: 4× M3 (3.2mm diameter)
- **Hole Positions**: 
  - (75.5, 134), (75.5, 163)
  - (134.5, 134), (134.5, 163)

## Trace Width Guide
| Net | Width | Notes |
|-----|-------|-------|
| +5V | 1.0mm+ | Motor power |
| +3.3V | 0.5mm | Low current |
| GND | Pour | Bottom layer |
| Signals | 0.25mm | Default |

## Component Placement Tips
1. **Pico in center** - everything radiates from here
2. **I2C devices grouped** - near GP4/GP5
3. **Buffer near Pico** - short UART traces
4. **Connectors on edges** - easy cable access
5. **Decoupling caps close** - within 5mm of ICs

## Common Mistakes to Avoid
- ❌ I2C pull-ups to +5V (should be +3.3V!)
- ❌ DYNAMIXEL pull-up to +3.3V (should be +5V!)
- ❌ Supercap polarity reversed
- ❌ Forgetting decoupling capacitors
- ❌ Traces too thin for motor power
- ❌ I2C traces too long

## Testing Checklist
1. ✓ Visual inspection
2. ✓ Continuity: +5V, +3.3V, GND
3. ✓ No shorts between power rails
4. ✓ Measure voltages before connecting devices
5. ✓ I2C scan (should find 0x3C and 0x68)
6. ✓ Motor communication test

## Emergency Contacts
- **Schematic**: `kicad/SCHEMATIC_GUIDE.md`
- **BOM**: `kicad/bom/BOM.md`
- **Netlist**: `kicad/NETLIST.md`
- **Critical Notes**: `NOTE_FOR_ANOOL_I2C_PULLUPS.txt`

---
**Remember**: When in doubt, check the documentation! 📚
