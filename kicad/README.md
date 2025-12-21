# Orbigator KiCad Project

This directory contains the KiCad PCB design files for the Orbigator orbital mechanics simulator.

## Project Structure

```
kicad/
├── orbigator.kicad_pro      # KiCad 8.x project file
├── orbigator.kicad_sch      # Main schematic file
├── orbigator.kicad_pcb      # PCB layout file
├── sym-lib-table            # Symbol library table
├── fp-lib-table             # Footprint library table
├── orbigator.pretty/        # Custom footprints
├── bom/                     # Bill of Materials exports
├── gerber/                  # Gerber files for manufacturing
├── pdf/                     # PDF exports of schematics
├── renders/                 # PCB renders
├── 3D_models/               # Custom 3D models
└── orbigator-backups/       # Automatic backups
```

## Quick Start

1. Open `orbigator.kicad_pro` in KiCad 8.x
2. Review the schematic in the Schematic Editor
3. Use the reference documentation in the parent directory:
   - `ORBIGATOR_CIRCUIT_DIAGRAM.txt` - ASCII circuit diagram
   - `ORBIGATOR_PIN_ASSIGNMENTS.txt` - Pin assignments
   - `NOTE_FOR_ANOOL_I2C_PULLUPS.txt` - Critical design notes
   - `BOM.md` - Detailed component specifications

## Key Design Requirements

### Critical Components
- **I2C Pull-ups**: 4.7kΩ resistors on SDA and SCL (REQUIRED for multi-device bus)
- **RTC Backup**: 0.47F supercapacitor with 47Ω charging resistor (recommended)
- **DATA Bus Pull-up**: 10kΩ resistor to +5V for DYNAMIXEL communication

### Power Requirements
- **3.3V Rail**: Pico 2, 74HC126, OLED, RTC (low current)
- **5V Rail**: DYNAMIXEL motors (4-5A external supply required)

### Connectors
- **DYNAMIXEL**: 3-pin JST connectors (daisy-chained)
- **Encoder**: 5-pin header (A, B, SW, VCC, GND)
- **Power**: Barrel jack or terminal block for 5V input

## Design Notes

This PCB is designed to be a single-board controller for the Orbigator display.
All components should be easily hand-solderable (through-hole or large SMD).

The design prioritizes:
- Reliability (proper pull-ups, decoupling)
- Serviceability (labeled connectors, test points)
- Compactness (suitable for display base mounting)

## Manufacturing

Standard 2-layer PCB:
- Thickness: 1.6mm
- Copper: 1oz
- Finish: HASL or ENIG
- Minimum trace: 0.2mm
- Minimum clearance: 0.2mm

## Author

Design by Anool Mahidharia (WyoLum)
Based on specifications by Justin Shaw
