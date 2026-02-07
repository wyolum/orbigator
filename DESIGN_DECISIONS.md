# Orbigator Design Decisions

This document captures the authoritative design decisions for the Orbigator motor control system. 
**This is the source of truth. Do not deviate from these specifications.**

---

## EQX Motor Recovery at Boot

### Goal
Recover the motor's absolute position from saved state, then slew to the correct orbital target.

### Algorithm (Bounded-Delta Recovery)

```python
CPR = 4096  # Counts per revolution

saved_mod = saved_ext % CPR
hw_mod = raw_ticks % CPR
d_mod = (hw_mod - saved_mod) % CPR  # Always 0..4095

# ALWAYS use shortest path
delta = d_mod if d_mod <= (CPR // 2) else d_mod - CPR

ext_now = saved_ext + delta
```

### Why Shortest Path?
- State is saved at least once per motor revolution
- Therefore `|delta| < half revolution` is always correct
- `d_mod = 4095` means `-1`, not `+4095`

### Boot Sequence
1. **Recover** - Read encoder, apply bounded-delta to get absolute position
2. **Compute** - Calculate orbital target from propagator (where satellite IS)
3. **Slew** - Command motors to target position (catch-up is expected and correct)

---

## Calibration Offset (`offset_degrees`)

### What It Is
A persistent calibration value that maps encoder ticks to real-world degrees.

Example: The physical ring's "0° EQX" mark is at encoder position 527. 
Therefore `offset_degrees = 527 * (360/4096) / gear_ratio`.

### Where It Lives
- Stored in `orbigator_config.json` under `motors.eqx.offset_deg`
- Applied in `DynamixelMotor.get_angle_degrees()`:
  ```python
  output_degrees = (abs_ticks * deg_per_tick / gear_ratio) - offset_degrees
  ```

### How To Calibrate
Use EQXCalibrationMode: set the displayed angle to match the physical position, then save.

---

## Motor Control Philosophy

### Hardware is Truth
- The encoder reading is the ground truth for position
- Software state (SRAM) is used only to recover multi-turn count

### Orbital Model is Target
- The propagator calculates where the satellite IS in real-time
- Motors slew to match the orbital target
- "Catch-up" slewing on boot is expected when position != target

### Direction Constraints
- **AoV Motor**: Forward-only during tracking (cable safety), bidirectional for nudging
- **EQX Motor**: Shortest path always

---

## State Persistence

### When State is Saved
- On revolution crossing (turn change callback)
- On mode exit (transition to Menu)
- On clean shutdown (Ctrl+C handler)
- On settings changes

### What is Saved
- Motor absolute tick counts (`aov_abs_ticks`, `eqx_abs_ticks`)
- Current positions (`aov_deg`, `eqx_deg`)
- Mode ID and satellite name
- Revolution count

### Storage Priority
1. RTC SRAM (instant, no flash wear)
2. Flash fallback (`state.json`)

---

## Terminology

| Term | Meaning |
|------|---------|
| `offset_degrees` | Calibration offset - maps encoder to real-world angle |
| `delta` | Bounded signed difference between saved and current position |
| `abs_ticks` | Extended position count (multi-turn capable) |
| `output_degrees` | Final angle after gear ratio and calibration offset |
| `hw_mod` | Current encoder reading modulo 4096 |
| `saved_mod` | Saved position modulo 4096 |

---

## Anti-Patterns (What NOT To Do)

❌ **Do NOT** add runtime phase offsets to "shift the sky"  
❌ **Do NOT** command motors from `mode.enter()` during boot sequence  
❌ **Do NOT** use direction constraints for boot recovery (always shortest path)  
❌ **Do NOT** interpret `d_mod = 4095` as `+4095` (it means `-1`)  

---

*Last Updated: 2026-02-07*
