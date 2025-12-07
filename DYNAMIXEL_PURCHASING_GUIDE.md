# DYNAMIXEL XC330-M288-T Purchasing Guide

## Selected Servo Model

**DYNAMIXEL XC330-M288-T** (Upgraded from XL330-M288-T)

### Why XC330 Instead of XL330?

**XL330-M288-T Status:** Backordered everywhere until Q1 2026

**XC330-M288-T Benefits:**
- ✅ **Metal gears** (XL330 has plastic) - Critical for longevity
- ✅ **Upgraded bearings** - Smoother operation
- ✅ **78% more torque** - 0.93 N·m vs 0.52 N·m @ 5V
- ✅ **Available NOW** - Ships in 3 business days
- ✅ **100% compatible** - Same protocol, wiring, and code as XL330
- ✅ **Better durability** - Will outlast plastic gears significantly

**Cost Difference:** ~$76 more per servo (~$152 total for 2)

---

## Where to Buy (USA)

### ⭐ RECOMMENDED: ROBOTIS US Official Store

**Price:** $103.39 per servo × 2 = **$206.78 total**

**Link:** https://www.robotis.us/dynamixel-xc330-m288-t/

**Advantages:**
- Official ROBOTIS distributor
- Full warranty support
- Ships within 3 business days (USA domestic)
- Guaranteed authentic product
- Technical support available

**How to Order:**
1. Visit https://www.robotis.us/dynamixel-xc330-m288-t/
2. Set quantity to **2**
3. Add to cart and checkout
4. Expected delivery: 5-7 business days

---

### Alternative: Amazon

**Link:** https://www.amazon.com/DYNAMIXEL-XC330-M288-T/dp/B0B33TLZ3L

**Advantages:**
- Fast shipping (2-day with Prime)
- Easy returns
- Check current price (may vary)

**Check before buying:**
- Verify seller is ROBOTIS or authorized
- Read recent reviews
- Compare price to ROBOTIS.us ($103.39)

---

### Alternative: RobotShop

**Link:** https://www.robotshop.com/products/robotis-dynamixel-xc330-m288-t-smart-servo-actuator

**Advantages:**
- Robotics specialty retailer
- Good customer service
- Check current availability

---

### Alternative: ThanksBuyer

**Link:** https://www.thanksbuyer.com/dynamixel-xc330-m288-t-0-930nm-coreless-servo-motor-w-metal-gear-for-leap-hand-and-machine-learning-92418

**Advantages:**
- Free shipping advertised
- Check delivery timeframe

---

## ❌ Where NOT to Buy

**eBay Sellers from China:**
- Prices: ~$194.50 + $30 shipping = $224.50 (more expensive!)
- Longer delivery times (2-4 weeks)
- Less reliable warranty support
- Risk of counterfeit products

**Recommendation:** Stick with official retailers above.

---

## Complete Parts Order

### Servos
- **2× DYNAMIXEL XC330-M288-T** - $206.78
- Verify X3P daisy-chain cables included (usually 1 per servo)

### Additional Components (if needed)

Most should already be on hand, but verify:

**SN74HC126N Tri-State Buffer:**
- **1× SN74HC126N IC** - ~$0.50 (DigiKey, Mouser, Amazon)

**Resistor:**
- **1× 10kΩ resistor** (1/4W) - ~$0.05

**Power Supply:**
- **1× 5V 4-5A power supply** - ~$10-15 (Amazon)
- Verify barrel jack or appropriate connector

**Decoupling Capacitors (recommended):**
- **2× 100µF electrolytic capacitor** - For servo power lines
- **1× 0.1µF ceramic capacitor** - For 74HC126 VCC

**Wiring:**
- Jumper wires (male-to-male, male-to-female)
- Breadboard or custom PCB

---

## Pre-Order Checklist

Before clicking "Buy Now," verify:

- [ ] Model: **XC330-M288-T** (NOT XC330-T288 or other variants!)
- [ ] Quantity: **2 servos**
- [ ] Voltage spec: 3.7-6V (5V recommended) ✅
- [ ] Protocol: DYNAMIXEL Protocol 2.0 ✅
- [ ] Your 5V power supply: 4-5A minimum capacity ✅
- [ ] SN74HC126N buffer IC on hand ✅
- [ ] 10kΩ pull-up resistor on hand ✅

---

## After Purchase

### When Servos Arrive:

1. **Verify Package Contents:**
   - 2× XC330-M288-T servos
   - 2× X3P daisy-chain cables (should be included)
   - Mounting hardware (screws, horns)
   - Manual/documentation

2. **Inspect for Damage:**
   - Check for shipping damage
   - Verify servo shafts rotate freely (power OFF)
   - Check connectors for bent pins

3. **Follow Setup Guide:**
   - See `README_DYNAMIXEL_MOTORS.md` for step-by-step instructions
   - Start with `DYNAMIXEL_WIRING_CHECKLIST.md` for wiring verification

---

## Specifications Reference

### DYNAMIXEL XC330-M288-T

| Specification | Value |
|---------------|-------|
| Model | XC330-M288-T |
| Voltage | 3.7V - 6V (5V recommended) |
| Stall Torque @ 5V | 0.93 N·m |
| No-Load Speed @ 5V | 81 RPM |
| Stall Current @ 5V | 1.8A |
| Weight | 23g |
| Dimensions | 20 × 34 × 26 mm |
| Resolution | 4096 steps (0.088° per step) |
| Protocol | DYNAMIXEL Protocol 2.0 |
| Communication | TTL Half-Duplex Serial |
| Baud Rate | 9,600 - 4.5 Mbps (57,600 default) |
| Gears | Metal (full metal gear) |
| Bearings | Upgraded (vs XL330) |
| Operating Modes | Position, Velocity, Current, PWM, Extended Position (360°) |
| ID Range | 0-252 (default: 1) |
| Connector | JST 3-pin (GND, VDD, DATA) |

---

## Total Project Cost (Servos Only)

| Item | Quantity | Unit Price | Total |
|------|----------|------------|-------|
| XC330-M288-T | 2 | $103.39 | **$206.78** |
| Shipping | - | Varies | ~$0-15 |
| **Grand Total** | | | **~$207-222** |

**Budget:** ~$210 for servos + shipping

---

## Compatibility Confirmation

✅ **Wiring:** All existing XL330 wiring documentation applies 100%
✅ **Code:** All existing `dynamixel_setup.py` code works without changes
✅ **Protocol:** Identical DYNAMIXEL Protocol 2.0
✅ **Voltage:** 5V operation (same as design)
✅ **Size:** Same physical dimensions (20×34×26mm)
✅ **Connector:** Same JST 3-pin (GND/VDD/DATA)
✅ **Control:** Same control table addresses

**No modifications needed to existing Orbigator design!**

---

## Questions Before Buying?

**Technical specs:** https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/

**ROBOTIS Support:** https://www.robotis.com/

**Forum:** https://forum.robotis.com/

---

**Document Created:** December 7, 2025
**Last Updated:** December 7, 2025
**Project:** Orbigator - DYNAMIXEL Integration
**Decision:** XC330-M288-T selected for metal gears and immediate availability
