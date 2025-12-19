# Development Workflow - Orbigator Project

## CRITICAL: MicroPython File Updates

**When editing MicroPython library/utility files:**

⚠️ **ALWAYS remind the user to upload updated files to the Pico 2!**

Changes to library files do NOT take effect until uploaded to the device.

### Files That Require Upload

Library and utility `.py` files in the `micropython/` directory:
- `dynamixel_motor.py` - Motor abstraction layer ⚠️ **REQUIRES UPLOAD**
- `dynamixel_extended_utils.py` - Low-level motor control ⚠️ **REQUIRES UPLOAD**
- `dynamixel_setup.py` - Motor configuration utilities
- `ds3231.py` - RTC driver
- `ssd1306.py` / `sh1106.py` - OLED drivers

### Files That Do NOT Require Upload

- `orbigator.py` - Main control code (runs from laptop, not Pico)

### Upload Methods

**Option 1: Using Thonny**
1. Connect Pico 2 via USB
2. Open Thonny IDE
3. Open the file on your computer
4. File → Save As → Raspberry Pi Pico
5. Save to the root directory

**Option 2: Using mpremote**
```bash
mpremote cp micropython/orbigator.py :orbigator.py
mpremote cp micropython/dynamixel_motor.py :dynamixel_motor.py
```

### Reminder Template

When editing MicroPython files, use this reminder:

```
📤 REMINDER: Upload Updated Files to Pico 2

I've made changes to the following MicroPython files:
- ✅ micropython/[filename].py - [brief description of changes]

To update your Pico 2:
1. Connect Pico 2 via USB
2. Use Thonny or mpremote to upload:
   - micropython/[filename].py

Changes won't take effect until you upload the updated files!
```

## AI Assistant Instructions

**For Claude and future AI assistants:**

When you edit any `.py` file in the `micropython/` directory:
1. Complete your edits
2. ALWAYS include the upload reminder in your response
3. List all modified MicroPython files
4. Provide clear upload instructions

This is critical because the user is working with embedded hardware where code changes require manual file transfer.
