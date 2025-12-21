# Getting Started Guide for Anool

## Your First Steps

### 1. Open the Project ✅ (Ready to go!)

```bash
cd kicad/
# Open orbigator.kicad_pro in KiCad
```

The project is already set up with:
- ✅ Board outline (55×70mm, rotated and centered)
- ✅ Mounting holes (4× M3, correctly positioned)
- ✅ Design rules configured
- ✅ Empty schematic ready for components

### 2. Create the Schematic (Start Here!)

Open the Schematic Editor and follow `SCHEMATIC_GUIDE.md`:

**Quick Start:**
1. Press `A` to add symbols
2. Start with power symbols: `+5V`, `+3V3`, `GND`
3. Add main components (see component list below)
4. Wire according to `NETLIST.md`
5. Run ERC (Inspect → Electrical Rules Checker)

**Component List (in order):**
```
U1: Raspberry_Pi_Pico_2 (MCU_Module)
U2: 74HC126 (74xx)
DISP1: OLED_128x64_I2C (Display)
RTC1: DS3231M (Timer_RTC)
M1, M2: Conn_01x03 (Connector) - DYNAMIXEL motors
ENC1: Rotary_Encoder_Switch (Device)
R1-R4: R (Device) - Resistors
C1: CP (Device) - Supercapacitor
C2-C3: C (Device) - Capacitors
J1: Barrel_Jack (Connector)
J2: Conn_01x03 (Connector) - DYNAMIXEL bus
J3: Conn_01x05 (Connector) - Encoder
```

### 3. Assign Footprints

After schematic is complete:
1. Tools → Assign Footprints
2. Use footprints from `bom/BOM.md`
3. Critical footprints:
   - U1: `Module:Raspberry_Pi_Pico_SMD`
   - U2: `Package_DIP:DIP-14_W7.62mm`
   - C1: `Capacitor_THT:CP_Radial_D10.0mm_P5.00mm`

### 4. Update PCB from Schematic

1. Open PCB Editor
2. Tools → Update PCB from Schematic (F8)
3. Click "Update PCB"
4. All components will appear - ready for placement!

### 5. Place Components

Follow the placement guidelines in `PCB_CHECKLIST.md`:
- Pico in center
- I2C devices near GP4/GP5
- Buffer near GP0/GP1/GP2
- Connectors on edges

### 6. Route the Board

Priority order:
1. Power traces (+5V, +3.3V, GND)
2. I2C bus (keep short!)
3. UART/DATA_BUS
4. Encoder signals

Use `QUICK_REFERENCE.md` for trace widths.

### 7. Run DRC

1. Inspect → Design Rules Checker
2. Fix all errors (must be 0 errors)
3. Review warnings

### 8. Generate Manufacturing Files

1. File → Plot
2. Select Gerber format
3. Output to `gerber/` directory
4. Generate drill files
5. Zip everything for manufacturer

---

## Estimated Time

- Schematic: 1-2 hours
- Component placement: 30 minutes
- Routing: 2-3 hours
- DRC and fixes: 30 minutes
- **Total: 4-6 hours**

## Need Help?

**Documentation:**
- `SCHEMATIC_GUIDE.md` - Step-by-step schematic creation
- `PCB_CHECKLIST.md` - Complete design checklist
- `QUICK_REFERENCE.md` - Critical info at a glance
- `DESIGN_RULES.md` - All design constraints
- `bom/BOM.md` - Component specifications
- `NETLIST.md` - Connection details

**Critical Notes:**
- `../NOTE_FOR_ANOOL_I2C_PULLUPS.txt` - I2C pull-up requirements
- `../ORBIGATOR_CIRCUIT_DIAGRAM.txt` - ASCII circuit diagram
- `../ORBIGATOR_PIN_ASSIGNMENTS.txt` - Pin assignments

## Common First-Time Issues

### "I can't find a component in the library"
- Make sure you're searching the right library (shown in parentheses)
- Try searching without the full part number
- Example: Search "Pico" not "Raspberry_Pi_Pico_2"

### "Footprint assignment failed"
- Check that the footprint library is installed
- Use the exact footprint names from `bom/BOM.md`
- Update footprint libraries if needed

### "ERC shows errors"
- Most common: Missing power connections
- Check that all power pins are connected
- Verify pull-ups are connected correctly

### "Components won't update to PCB"
- Make sure schematic has no ERC errors
- Save schematic before updating PCB
- Try "Update PCB from Schematic" again

## Pro Tips

1. **Save often!** KiCad auto-saves but manual saves are safer
2. **Use net labels** - Makes schematic cleaner and easier to read
3. **Group related components** - Easier to route later
4. **Check footprints early** - Easier to fix in schematic than PCB
5. **Use the checklist** - Don't skip steps!

## Ready to Start?

1. Open `orbigator.kicad_pro`
2. Click "Schematic Editor"
3. Follow `SCHEMATIC_GUIDE.md`
4. Reference `QUICK_REFERENCE.md` for critical values

**Good luck! You've got this! 🚀**

---

Questions? Check the documentation or reach out to Justin.
