# PCB Design Checklist for Orbigator

Use this checklist to ensure all critical design elements are included.

## Pre-Layout

- [ ] Review schematic for errors
- [ ] Run ERC (Electrical Rules Check) - must pass with 0 errors
- [ ] Verify all footprints assigned
- [ ] Check component values match BOM
- [ ] Verify I2C pull-ups (R2, R3) are 4.7kΩ to +3.3V
- [ ] Verify DYNAMIXEL pull-up (R1) is 10kΩ to +5V
- [ ] Verify supercap circuit (C1, R4) is correct

## Component Placement

### Power Components
- [ ] Place Pico 2 (U1) in center of board
- [ ] Place 74HC126 (U2) near Pico GP0/GP1/GP2
- [ ] Place decoupling caps (C2, C3) within 5mm of ICs
- [ ] Place power input (J1) on edge

### I2C Devices
- [ ] Group OLED (DISP1) and RTC (RTC1) near Pico GP4/GP5
- [ ] Place I2C pull-ups (R2, R3) near Pico
- [ ] Keep I2C traces < 50mm if possible

### Connectors
- [ ] Place motor connectors (M1, M2, J2) on accessible edge
- [ ] Place encoder connector (J3) on accessible edge
- [ ] Ensure all connectors face outward for easy cable access

### Special Components
- [ ] Place supercap (C1) near RTC
- [ ] Place charging resistor (R4) between +3.3V and C1
- [ ] Ensure polarity marking on C1 is visible

## Routing

### Power Traces (Priority 1)
- [ ] Route +5V with 1.0mm traces (motor current)
- [ ] Route +3.3V with 0.5mm traces
- [ ] Create ground pour on bottom layer
- [ ] Add multiple vias for ground connections
- [ ] Verify power traces have no bottlenecks

### Critical Signals (Priority 2)
- [ ] Route I2C_SDA and I2C_SCL together, keep short
- [ ] Route UART_TX, UART_RX, DIR_PIN with 0.25mm traces
- [ ] Route DATA_BUS with 0.25mm trace
- [ ] Keep UART and DATA_BUS traces < 100mm

### Other Signals (Priority 3)
- [ ] Route encoder signals (ENC_A, ENC_B, ENC_SW)
- [ ] Route RTC_BAT to supercap

### Design Rules
- [ ] All traces meet minimum width (0.25mm)
- [ ] All clearances meet minimum (0.2mm)
- [ ] No acute angles in traces (use 45° or curved)
- [ ] No vias in pads (unless intentional thermal vias)

## Silkscreen

- [ ] All component references visible and readable
- [ ] Polarity markings on C1 (supercap)
- [ ] Pin 1 indicators on ICs
- [ ] Connector pin labels (especially J2, J3)
- [ ] Board name and version visible
- [ ] Company name (WyoLum) visible
- [ ] Critical warnings (e.g., "5V ONLY" near J1)

## Design Rule Check (DRC)

- [ ] Run DRC - must pass with 0 errors
- [ ] Check for unconnected nets
- [ ] Check for overlapping components
- [ ] Check for traces too close to board edge
- [ ] Check for missing copper in power nets

## Final Checks

- [ ] Board outline is correct (70mm × 55mm after rotation)
- [ ] Mounting holes are correct (M3, centered pattern)
- [ ] All components within board outline
- [ ] No silkscreen over pads
- [ ] No silkscreen on Edge.Cuts layer
- [ ] Ground pour has no isolated islands
- [ ] Test points added for debugging (optional but recommended)

## Pre-Fabrication

- [ ] Generate Gerber files
- [ ] Generate drill files
- [ ] Verify Gerber files in viewer
- [ ] Export BOM (CSV format)
- [ ] Export pick-and-place file (if using assembly service)
- [ ] Create assembly drawing (PDF)
- [ ] Zip all manufacturing files

## Manufacturing Notes

**PCB Specifications:**
- 2-layer board
- 1.6mm thickness
- 1oz copper
- HASL or ENIG finish
- Green solder mask (or your preference)
- White silkscreen

**Recommended Manufacturers:**
- JLCPCB (cheap, fast)
- PCBWay (good quality)
- OSH Park (USA, purple boards)

**Typical Lead Time:** 5-10 days + shipping

## Assembly Notes

**Assembly Order:**
1. Solder SMD components first (if any)
2. Solder through-hole resistors and capacitors
3. Solder ICs (74HC126)
4. Solder connectors
5. Solder Pico 2 (use headers or direct solder)
6. Install supercap (C1) - watch polarity!
7. Test continuity before applying power

**Testing:**
1. Visual inspection
2. Continuity test (power rails, ground)
3. Power-on test (measure voltages)
4. I2C bus test (scan for devices)
5. Motor communication test
6. Full system test

---

**Questions?** Refer to:
- `SCHEMATIC_GUIDE.md` - Schematic creation steps
- `bom/BOM.md` - Component specifications
- `NETLIST.md` - Connection details
- `NOTE_FOR_ANOOL_I2C_PULLUPS.txt` - Critical design notes
