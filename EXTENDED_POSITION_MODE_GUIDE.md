# Extended Position Mode - Best Practices Guide

## 🎯 Overview

Extended Position Control Mode (Mode 4) is the **recommended mode** for Orbigator's continuous orbital tracking. This guide covers the best practices for using it effectively.

---

## ✅ The Recommended Approach

### 1. **Set Mode 4 Once and Leave It**

Configure both motors for Extended Position Mode during initial setup and **never switch back**:

```python
from dynamixel_extended_utils import set_extended_mode

# One-time setup (or after factory reset)
set_extended_mode(1)  # EQX motor
set_extended_mode(2)  # AoV motor
```

**Why?** 
- No need to switch modes for different operations
- Simpler code and fewer potential errors
- Motors remember the mode setting even after power cycle

---

### 2. **Read Position on Every Boot**

**CRITICAL:** Before sending any Goal Position commands, read the current position:

```python
from dynamixel_extended_utils import orbigator_init

# On boot/startup
lan_position, aov_position = orbigator_init()

# Use these as your baseline for all subsequent movements
```

**Why?**
- Prevents motor from jumping to old position values
- Maintains continuity across power cycles
- Essential for accurate orbital tracking

**What happens if you skip this?**
If you power on and immediately send `Goal Position = 0`, the motor will rapidly spin back to position 0, potentially causing:
- Mechanical stress
- Loss of orbital tracking accuracy
- Unexpected behavior

---

### 3. **Don't Worry About Integer Overflow**

Extended Position Mode uses a **signed 32-bit integer**:
- Range: ±2,147,483,647 ticks
- At 1° every 10 seconds: **62+ years** to overflow
- For Orbigator: Effectively infinite

**Conclusion:** Ignore overflow concerns. Your motors will wear out long before the counter overflows.

---

### 4. **Optional: Clear Multi-Turn Command**

If you need to reset the position counter (e.g., after months of operation), use the **Clear Multi-Turn** command:

```python
from dynamixel_extended_utils import clear_multi_turn, read_present_position

# Read current position
old_pos = read_present_position(1)
print(f"Before clear: {old_pos}")

# Clear multi-turn (motor stays in place!)
clear_multi_turn(1)

# Read new position (will be 0-4095)
new_pos = read_present_position(1)
print(f"After clear: {new_pos}")
```

**How it works:**
- Motor shaft **does not move**
- Internal `Present Position` resets to equivalent value within 0-4095 range
- Based on current physical orientation

**When to use:**
- After extended operation (months/years)
- When you want a fresh baseline
- For maintenance/calibration

**When NOT to use:**
- During normal operation
- On every boot (use `read_present_position` instead)
- As a workaround for other issues

---

## 📋 Complete Initialization Checklist

### One-Time Setup (Initial Configuration)

```python
from dynamixel_extended_utils import set_extended_mode

# Configure both motors for Extended Position Mode
set_extended_mode(1)  # EQX motor
set_extended_mode(2)  # AoV motor

# Done! Motors will remember this setting.
```

### Every Boot Routine

```python
from dynamixel_extended_utils import orbigator_init, write_dword

# 1. Read current positions
lan_pos, aov_pos = orbigator_init()

# 2. Use these as your baseline for movements
# Example: Move EQX motor forward by 90° from current position
degrees_to_move = 90
ticks_per_degree = 4096 / 360.0
new_lan_pos = lan_pos + int(degrees_to_move * ticks_per_degree)

write_dword(1, 116, new_lan_pos)  # ADDR_GOAL_POSITION = 116
```

---

## 🚀 Orbigator Integration Example

```python
"""
Orbigator main control loop with Extended Position Mode
"""

from dynamixel_extended_utils import orbigator_init, write_dword
import time

# Initialize on boot
print("Initializing Orbigator motors...")
lan_position, aov_position = orbigator_init()

if lan_position is None or aov_position is None:
    print("ERROR: Failed to initialize motors!")
    exit()

# Orbital simulation parameters
TICKS_PER_DEGREE = 4096 / 360.0

def set_orbital_position(lan_degrees, aov_degrees):
    """
    Set orbital position in degrees.
    EQX: Equator crossing (orbital plane rotation)
    AoV: Argument of Vehicle (position along orbit)
    """
    global lan_position, aov_position
    
    # Calculate target positions
    lan_target = int(lan_degrees * TICKS_PER_DEGREE)
    aov_target = int(aov_degrees * TICKS_PER_DEGREE)
    
    # Send commands
    write_dword(1, 116, lan_target)
    write_dword(2, 116, aov_target)
    
    # Update tracking
    lan_position = lan_target
    aov_position = aov_target

# Example: Simulate one complete orbit
print("\nSimulating orbital motion...")
for aov_angle in range(0, 720, 1):  # Two complete orbits
    set_orbital_position(lan_degrees=45, aov_degrees=aov_angle)
    time.sleep(0.1)
    
    if aov_angle % 90 == 0:
        print(f"AoV: {aov_angle}° ({aov_angle/360:.1f} orbits)")

print("\n✓ Simulation complete!")
```

---

## 🔧 Troubleshooting

### Motor Jumps on Boot

**Problem:** Motor rapidly spins to unexpected position when powered on.

**Solution:** You forgot to read the present position before sending commands!

```python
# WRONG - Don't do this:
write_dword(1, 116, 0)  # Motor jumps to position 0!

# CORRECT - Do this:
current_pos = read_present_position(1)
write_dword(1, 116, current_pos)  # Motor stays in place
```

### Position Seems Wrong After Power Cycle

**Problem:** Position values don't match what you expect.

**Explanation:** Extended Position Mode maintains the cumulative position across power cycles. This is **correct behavior**.

**Solution:** Always read the present position on boot and use it as your baseline.

### Want to "Reset" Position Counter

**Problem:** Position values are very large after extended operation.

**Solution:** Use `clear_multi_turn()` command:

```python
from dynamixel_extended_utils import clear_multi_turn

clear_multi_turn(1)  # Resets position to 0-4095 range without moving
clear_multi_turn(2)
```

---

## 📚 Reference

### Key Functions

| Function | Purpose | When to Use |
|----------|---------|-------------|
| `set_extended_mode(id)` | Configure Mode 4 | One-time setup |
| `orbigator_init()` | Read positions on boot | Every boot |
| `read_present_position(id)` | Get current position | Anytime |
| `write_dword(id, 116, pos)` | Set goal position | Normal operation |
| `clear_multi_turn(id)` | Reset counter | Optional maintenance |

### Important Addresses

| Address | Name | Purpose |
|---------|------|---------|
| 11 | Operating Mode | Set to 4 for Extended Position |
| 64 | Torque Enable | 0=off, 1=on |
| 116 | Goal Position | Target position (32-bit) |
| 132 | Present Position | Current position (32-bit) |

---

## ✅ Summary Checklist for 2025

- [x] **Keep it in Mode 4:** Set once, leave permanently
- [x] **Ignore the Integer:** 62+ years to overflow at 1°/10sec
- [x] **Power-On Routine:** Read `Present Position` on every boot
- [x] **Use as Baseline:** Never assume position = 0 on boot
- [x] **Optional Reset:** Use `clear_multi_turn()` only if needed

---

**Your motors are now configured for continuous orbital tracking! 🛰️**
