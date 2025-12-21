# Orbigator Schematic Creation Guide for KiCad 8.x

This guide will help Anool quickly create the Orbigator schematic in KiCad.

## Prerequisites

- KiCad 8.x installed
- All reference documentation reviewed:
  - `ORBIGATOR_CIRCUIT_DIAGRAM.txt`
  - `ORBIGATOR_PIN_ASSIGNMENTS.txt`
  - `NOTE_FOR_ANOOL_I2C_PULLUPS.txt`
  - `bom/BOM.md`
  - `NETLIST.md`

## Step 1: Open the Project

1. Open KiCad
2. File → Open Project
3. Select `orbigator.kicad_pro`

## Step 2: Create the Schematic

1. Click "Schematic Editor" button
2. The schematic will be blank - we'll build it from scratch

## Step 3: Place Components

### Power Symbols
1. Press `P` to place power symbols
2. Add the following:
   - `+5V` (external supply)
   - `+3V3` (from Pico)
   - `GND` (common ground)

### Main Components

Place each component using `A` (Add Symbol):

#### U1 - Raspberry Pi Pico 2
- Library: `MCU_Module`
- Symbol: `Raspberry_Pi_Pico_2`
- Reference: `U1`
- Value: `Pico 2`

#### U2 - 74HC126
- Library: `74xx`
- Symbol: `74HC126`
- Reference: `U2`
- Value: `74HC126`

#### DISP1 - OLED Display
- Library: `Display`
- Symbol: `OLED_128x64_I2C`
- Reference: `DISP1`
- Value: `SSD1306`

#### RTC1 - DS3231
- Library: `Timer_RTC`
- Symbol: `DS3231M`
- Reference: `RTC1`
- Value: `DS3231`

#### M1, M2 - DYNAMIXEL Motors
- Library: `Connector`
- Symbol: `Conn_01x03`
- References: `M1`, `M2`
- Values: `DYNAMIXEL_1`, `DYNAMIXEL_2`
- Note: Add labels for GND, VDD, DATA

#### ENC1 - Rotary Encoder
- Library: `Device`
- Symbol: `Rotary_Encoder_Switch`
- Reference: `ENC1`
- Value: `Encoder`

### Passive Components

#### Resistors (Press `A`, Library: `Device`, Symbol: `R`)
- `R1`: 10kΩ (DATA bus pull-up)
- `R2`: 4.7kΩ (I2C SDA pull-up)
- `R3`: 4.7kΩ (I2C SCL pull-up)
- `R4`: 47Ω (Supercap charging)

#### Capacitors (Press `A`, Library: `Device`)
- `C1`: Symbol `CP`, Value `0.47F 5.5V` (Supercapacitor)
- `C2`: Symbol `C`, Value `100nF` (74HC126 decoupling)
- `C3`: Symbol `C`, Value `100nF` (Pico decoupling)

### Connectors

#### J1 - Power Input
- Library: `Connector`
- Symbol: `Barrel_Jack`
- Reference: `J1`
- Value: `5V_IN`

#### J2 - DYNAMIXEL Connector
- Library: `Connector`
- Symbol: `Conn_01x03`
- Reference: `J2`
- Value: `DYNAMIXEL_BUS`

#### J3 - Encoder Connector
- Library: `Connector`
- Symbol: `Conn_01x05`
- Reference: `J3`
- Value: `ENCODER`

## Step 4: Wire the Schematic

Use `W` (Wire tool) to connect components according to `NETLIST.md`.

### Critical Connections

#### Power Distribution
1. Connect J1 Pin 1 (+) to `+5V` net
2. Connect J1 Pin 2 (-) to `GND` net
3. Connect Pico Pin 36 (3V3_OUT) to `+3V3` net
4. Connect all GND pins together

#### UART & Buffer (Half-Duplex)
1. Pico GP0 (Pin 1) → 74HC126 Pin 2 (1A)
2. 74HC126 Pin 3 (1Y) → DATA_BUS net
3. Pico GP1 (Pin 2) → DATA_BUS net
4. Pico GP2 (Pin 4) → 74HC126 Pin 1 (1OE)
5. DATA_BUS → M1 Pin 3, M2 Pin 3, J2 Pin 3
6. R1 Pin 1 → +5V, R1 Pin 2 → DATA_BUS

#### I2C Bus (CRITICAL - Needs Pull-ups!)
1. Pico GP4 (Pin 6) → I2C_SDA net
2. Pico GP5 (Pin 7) → I2C_SCL net
3. I2C_SDA → DISP1 SDA, RTC1 SDA
4. I2C_SCL → DISP1 SCL, RTC1 SCL
5. R2 Pin 1 → +3V3, R2 Pin 2 → I2C_SDA
6. R3 Pin 1 → +3V3, R3 Pin 2 → I2C_SCL

#### Encoder
1. Pico GP6 (Pin 9) → ENC1 Pin A
2. Pico GP7 (Pin 10) → ENC1 Pin B
3. Pico GP8 (Pin 11) → ENC1 Pin SW
4. ENC1 VCC → +3V3
5. ENC1 GND → GND

#### RTC Backup Power
1. +3V3 → R4 Pin 1
2. R4 Pin 2 → C1 Pin 1 (positive)
3. R4 Pin 2 → RTC1 BAT pin
4. C1 Pin 2 (negative) → GND

#### Motor Power
1. +5V → M1 Pin 2 (VDD), M2 Pin 2 (VDD), J2 Pin 2
2. GND → M1 Pin 1, M2 Pin 1, J2 Pin 1

#### Decoupling Capacitors
1. C2 Pin 1 → +3V3, C2 Pin 2 → GND (near 74HC126)
2. C3 Pin 1 → +3V3, C3 Pin 2 → GND (near Pico)

## Step 5: Add Labels and Annotations

1. Use `L` (Label tool) to add net labels:
   - `+5V`, `+3V3`, `GND`
   - `DATA_BUS`
   - `I2C_SDA`, `I2C_SCL`
   - `UART_TX`, `UART_RX`, `DIR_PIN`
   - `ENC_A`, `ENC_B`, `ENC_SW`

2. Add text notes (Press `T`):
   - "CRITICAL: I2C pull-ups required!" near R2/R3
   - "10kΩ to +5V" near R1
   - "Supercap backup (recommended)" near C1

## Step 6: Assign Footprints

1. Tools → Assign Footprints
2. Use the footprints from `bom/BOM.md`
3. Key footprints:
   - U1: `Module:Raspberry_Pi_Pico_SMD`
   - U2: `Package_DIP:DIP-14_W7.62mm`
   - R1-R4: `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal`
   - C1: `Capacitor_THT:CP_Radial_D10.0mm_P5.00mm`
   - C2-C3: `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm`

## Step 7: Run Electrical Rules Check (ERC)

1. Inspect → Electrical Rules Checker
2. Click "Run ERC"
3. Fix any errors (should be clean if wired correctly)

## Step 8: Generate Netlist

1. File → Export → Netlist
2. Save as `orbigator.net`
3. This will be used for PCB layout

## Step 9: Create PCB Layout

1. Click "PCB Editor" button
2. Tools → Update PCB from Schematic
3. Click "Update PCB"
4. All components will appear - ready for placement and routing

## Layout Tips

### Component Placement
- Place Pico in center
- Group I2C devices (OLED, RTC) near Pico GP4/GP5
- Place 74HC126 near Pico GP0/GP1/GP2
- Place motor connectors on edge for cable access
- Place encoder connector on accessible edge

### Routing Priority
1. Power traces first (+5V, +3V3, GND)
   - Use 1.0mm for +5V (motor current)
   - Use 0.5mm for +3V3
   - Use ground pour on bottom layer
2. I2C traces (keep short!)
3. UART/DATA_BUS
4. Encoder signals

### Design Rules
- Minimum trace: 0.25mm
- Minimum clearance: 0.2mm
- Power traces: 1.0mm
- Via: 0.8mm diameter, 0.4mm drill

## Step 10: Generate Gerbers

1. File → Plot
2. Output directory: `gerber/`
3. Layers to plot:
   - F.Cu, B.Cu
   - F.SilkS, B.SilkS
   - F.Mask, B.Mask
   - Edge.Cuts
4. Click "Plot"
5. Click "Generate Drill Files"

## Step 11: Export BOM

1. Tools → Generate BOM
2. Select CSV format
3. Save to `bom/` directory

## Step 12: Create PDF Schematic

1. File → Plot
2. Select "PDF" format
3. Output to `pdf/` directory

## Verification Checklist

- [ ] All components placed
- [ ] All nets connected (no airwires)
- [ ] I2C pull-ups (R2, R3) present and correct
- [ ] DATA bus pull-up (R1) to +5V
- [ ] Supercap charging circuit (R4, C1) correct
- [ ] Decoupling caps near ICs
- [ ] ERC passes with no errors
- [ ] Footprints assigned
- [ ] PCB layout complete
- [ ] DRC passes
- [ ] Gerbers generated

## Common Issues

### I2C Not Working
- Check R2, R3 are 4.7kΩ to +3.3V (NOT +5V!)
- Verify SDA/SCL connections to GP4/GP5

### DYNAMIXEL Not Responding
- Check R1 is 10kΩ to +5V (NOT +3.3V!)
- Verify 74HC126 direction control (GP2 → 1OE)

### RTC Losing Time
- Check supercap polarity (C1)
- Verify R4 (47Ω) is in series
- Check BAT pin connection

## Need Help?

Refer to:
- `ORBIGATOR_CIRCUIT_DIAGRAM.txt` - ASCII circuit diagram
- `NETLIST.md` - Complete connection list
- `bom/BOM.md` - Component specifications

Good luck! The schematic should take 1-2 hours to complete.
