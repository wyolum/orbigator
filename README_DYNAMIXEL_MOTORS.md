# 🎉 DYNAMIXEL MOTORS - START HERE! 🎉

## ⚡ SERVO CHOICE: XC330-M288-T (Upgraded)

**Selected Model:** DYNAMIXEL XC330-M288-T
**Why:** XL330-M288-T backordered until Q1 2026. XC330 is the upgraded version with:
- ✅ Metal gears (vs plastic in XL330)
- ✅ Upgraded bearings
- ✅ 78% more torque (0.93 vs 0.52 N·m @ 5V)
- ✅ **100% compatible** with all XL330 documentation below
- ✅ Same Protocol 2.0, same wiring, same code
- ✅ Available immediately

**Note:** All documentation references to "XL330" apply equally to "XC330". No changes needed.

---

## Quick Start Guide for Orbigator DYNAMIXEL Integration

### 📋 **Step 1: Review Wiring Documentation**

**MAIN REFERENCE:** `ORBIGATOR_COMPLETE_WIRING.txt`
- Complete pin assignments for entire system
- All connections clearly documented
- Power distribution diagram
- No stepper motor connections (clean DYNAMIXEL design)

**Additional References:**
- `DYNAMIXEL_WIRING_DIAGRAM.txt` - ASCII circuit diagram
- `DYNAMIXEL_Connection_with_74HC126.md` - Detailed guide with code
- `DYNAMIXEL_Quick_Reference.md` - One-page cheat sheet

### 🔧 **Step 2: Configure Servo IDs**

**IMPORTANT:** Before wiring both servos together, set their IDs!

**Script Location:** `micropython/dynamixel_setup.py`

**Quick Setup Method:**
1. Upload `dynamixel_setup.py` to your Pico 2
2. Wire up **ONE servo at a time** with the 74HC126 circuit
3. Run the script and use the guided setup:
   ```python
   setup_orbigator_servos()
   ```
4. Follow prompts to set:
   - First servo → ID=1 (LAN Motor)
   - Second servo → ID=2 (AOV Motor)

**Alternative - Interactive Menu:**
```python
main()  # Then select option 3 to change IDs
```

### ⚡ **Step 3: Wire Everything**

Follow `ORBIGATOR_COMPLETE_WIRING.txt` exactly:

**Key Connections:**
- GP0 → 74HC126 Pin 2 (TX)
- GP1 → DATA BUS (RX)
- GP2 → 74HC126 Pin 1 (Direction Control)
- 10kΩ pull-up on DATA line to 5V
- Both servos share DATA BUS (daisy-chain)
- External 5V 4-5A power supply for servos

**Critical Notes:**
- ✅ Common ground for ALL components
- ✅ DO NOT power servos from Pico
- ✅ Each servo must have unique ID (1 and 2)

### 🧪 **Step 4: Test Communication**

Use `dynamixel_setup.py` to verify:
```python
# Scan for both servos
scan_servos()

# Should find ID 1 and 2
ping(1)  # LAN Motor
ping(2)  # AOV Motor

# Test movement
set_torque(1, True)
set_position(1, 2048)  # Center position
```

### 🚀 **Step 5: Integrate with Orbigator**

Update `orbigator.py` to use DYNAMIXEL instead of steppers:
- Replace `lan_move_steps()` with DYNAMIXEL position commands
- Replace `aov_move_steps()` with DYNAMIXEL position commands
- Use servo feedback for accurate position tracking

### 📦 **Parts Checklist**

Before you start, verify you have:
- ✅ 2× DYNAMIXEL XL330-M288-T servos
- ✅ 1× SN74HC126N IC
- ✅ 1× 10kΩ resistor
- ✅ 1× 5V 4-5A power supply
- ✅ Jumper wires
- ✅ Breadboard or PCB

### 🎯 **Servo Assignments**

| Servo ID | Motor Type | Function |
|----------|------------|----------|
| 1 | LAN Motor | Longitude of Ascending Node |
| 2 | AOV Motor | Argument of Perigee / True Anomaly |

### 📞 **Need Help?**

All documentation is in the `orbigator` directory:
- Wiring diagrams
- Setup scripts
- Code examples
- Troubleshooting guides

**Good luck with your DYNAMIXEL upgrade!** 🚀

---
*Created: December 7, 2025*
*When motors arrive, start with ORBIGATOR_COMPLETE_WIRING.txt*
