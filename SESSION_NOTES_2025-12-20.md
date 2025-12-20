# Orbigator Session Notes - December 20, 2025

## Major Accomplishments Today

### 1. Fixed I2C Display Glitching ✅
- **Root Cause:** Missing external pull-up resistors on shared I2C bus (OLED + RTC)
- **Solution:** Added 4.7kΩ resistors on SDA (GP4) and SCL (GP5) to 3.3V
- **Documentation:** Created `NOTE_FOR_ANOOL_I2C_PULLUPS.txt` with critical PCB design requirements
- **Circuit Diagram:** Updated `ORBIGATOR_CIRCUIT_DIAGRAM.txt` with R2 and R3 pull-ups
- **Performance:** Reduced display update to 1Hz to minimize I2C traffic

### 2. Fixed Motor Control Issues ✅
- **Problem 1:** Motors not moving (positions stuck at 0.0, 0.0)
  - Fixed: Rate initialization bug when starting in state 3
  - Added startup initialization after `load_state()`

- **Problem 2:** EQX motor spinning continuously beyond 360°
  - Implemented `get_new_pos(current_pos, command_pos)` function
  - Preserves turn count in Extended Position Mode
  - Only applies incremental changes from wrapped positions

- **Problem 3:** Catch-up mechanism commanding extreme positions (773448°!)
  - Fixed `load_state()` catch-up to use `get_new_pos()` with modulo-wrapped targets
  - Motors now move smoothly without multi-revolution jumps

### 3. Motor Rate Calculations Clarified ✅
- **EQX Rate:** 360°/sidereal day (Earth rotation) + J2 precession (~5°/day)
- **Reference Frame:** Almost-ECI (Earth-Centered Inertial)
- **Position Wrapping:** Both motors use `get_new_pos()` to preserve turn count
- **User confirmed:** Need Earth rotation 360°/sidereal day, with modulo wrapping

### 4. Documentation Updates ✅
- Added `schematics/74HC126_pinout_diagram.png` - visual DIP pinout
- Added `schematics/74HC126_PINOUT.txt` - detailed text reference
- Added `schematics/dynamixel_xl330_pinout.png` - 3-pin connector diagram
- Added `schematics/dc_power_jack_pj007_drawing.png` - PJ-007 mechanical drawing
- Added `schematics/orbigator_pcb_layout_labeled.png` - labeled PCB layout
- Updated `README_DYNAMIXEL_MOTORS.md` with M2×8 screw info (AoV arm 5.25mm bracket)

## Current State

### Hardware
- ✅ Motors moving correctly with Extended Position Mode
- ✅ Display stable with I2C pull-ups
- ✅ RTC communication reliable with error handling
- ✅ All components wired and tested on breadboard

### Software (`orbigator.py`)
- ✅ Motor rates initialized properly at startup
- ✅ `get_new_pos()` function for turn-preserving position updates
- ✅ Catch-up mechanism working correctly
- ✅ Display updates at 1Hz
- ⚠️ User modified catch-up to add `% 360` to ensure positive positions (line 592-593)

### Mechanical Design
- 🔄 **Waiting for Anool's PCB feedback before 3D printing**
- Design complete with:
  - AoV motor mount (coral/copper) at orbital inclination
  - Penny counterweight cylinders on AoV arm
  - EQX ring gear for globe rotation
  - Integrated electronics base

## Key Implementation Details

### Extended Position Mode Wrapping
```python
def get_new_pos(current_pos, command_pos):
    """Preserves turn count, applies incremental change"""
    turns, pos = divmod(current_pos, 360)
    change = command_pos - pos
    return turns * 360 + pos + change
```

**Usage:**
- Read current position from motor
- Calculate target position modulo 360
- Use `get_new_pos()` to preserve turn count
- Command the result

### I2C Pull-up Requirements
- **Critical for PCB:** 4.7kΩ from SDA to 3.3V, 4.7kΩ from SCL to 3.3V
- Required when multiple I2C devices share the bus
- Individual module pull-ups are NOT sufficient

### Power Distribution
- Single 5V supply for Dynamixel motors
- Pico 2 powered via VSYS (Pin 39) from same 5V supply
- Common ground for all components

## Pending Items

1. **Waiting for Anool:**
   - PCB design feedback
   - After approval: 3D print mechanical assembly

2. **Future Enhancements:**
   - Test full assembly with globe installed
   - Calibrate gear ratios and motion rates
   - Verify orbital mechanics accuracy

## Important Files to Reference

- `micropython/orbigator.py` - Main control code (motors working!)
- `NOTE_FOR_ANOOL_I2C_PULLUPS.txt` - Critical PCB requirements
- `ORBIGATOR_CIRCUIT_DIAGRAM.txt` - Complete wiring with pull-ups
- `README_DYNAMIXEL_MOTORS.md` - Motor setup and mounting hardware
- `schematics/` - All component diagrams and PCB layout

## Next Session TODO

- [ ] Review any feedback from Anool on PCB design
- [ ] Assist with 3D print preparation if needed
- [ ] Test any remaining motor control edge cases
- [ ] Document final assembly procedures

---
**Session Summary:** Major debugging session! Fixed I2C glitching with pull-ups, resolved motor position wrapping issues, and clarified EQX rate calculations. Hardware is stable, software is solid, waiting on PCB feedback before final assembly.
