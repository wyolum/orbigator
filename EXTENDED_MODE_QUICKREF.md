# Extended Position Mode - Quick Reference

## 🚀 Quick Start

### One-Time Setup
```python
from dynamixel_extended_utils import set_extended_mode

set_extended_mode(1)  # EQX motor
set_extended_mode(2)  # AoV motor
```

### Every Boot
```python
from dynamixel_extended_utils import orbigator_init, write_dword

# Read current positions (CRITICAL!)
lan_pos, aov_pos = orbigator_init()

# Now safe to move motors
write_dword(1, 116, lan_pos + 1000)  # Move EQX forward
write_dword(2, 116, aov_pos + 2000)  # Move AoV forward
```

## 📋 Key Points

✅ **Set Mode 4 once** - Never switch back  
✅ **Read position on boot** - Prevents jumps  
✅ **Ignore overflow** - 62+ years at 1°/10sec  
✅ **Optional reset** - Use `clear_multi_turn()` if needed  

## 🔧 Common Functions

| Function | Purpose |
|----------|---------|
| `set_extended_mode(id)` | One-time Mode 4 setup |
| `orbigator_init()` | Boot routine - read positions |
| `read_present_position(id)` | Get current position |
| `write_dword(id, 116, pos)` | Set goal position |
| `clear_multi_turn(id)` | Reset counter (optional) |

## ⚠️ Critical Rule

**NEVER** send a goal position without reading the current position first on boot!

```python
# ❌ WRONG - Motor will jump!
write_dword(1, 116, 0)

# ✅ CORRECT - Motor stays smooth
current = read_present_position(1)
write_dword(1, 116, current + offset)
```

## 📚 Full Documentation

See [`EXTENDED_POSITION_MODE_GUIDE.md`](file:///home/justin/code/orbigator/EXTENDED_POSITION_MODE_GUIDE.md) for complete details.
