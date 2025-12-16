# DYNAMIXEL XL330 Gear Adapter Specifications

## Overview

3D-printable adapter to connect DYNAMIXEL XL330-M288-T servo output shaft to a 32-pitch, 11-tooth gear with 5mm bore. Designed for the Orbigator LAN motor gear drive system.

## Design Files

- **CAD Model**: [dynamixel_xl330_gear_adapter.scad](file:///home/justin/code/orbigator/fabricate/dynamixel_xl330_gear_adapter.scad)
- **STL File**: [dynamixel_xl330_gear_adapter.stl](file:///home/justin/code/orbigator/fabricate/dynamixel_xl330_gear_adapter.stl)

## Specifications

### Dimensions

| Component | Dimension | Notes |
|-----------|-----------|-------|
| Gear Hub Diameter | 5.0mm | Fits 5mm bore with -0.1mm tolerance |
| Gear Hub Height | 8.0mm | Extends above flange |
| Set Screw Flat Depth | 0.5mm | For M3 set screw retention |
| Shaft Socket Diameter | 6.0mm | Fits XL330 output shaft |
| Shaft Socket Depth | 6.0mm | Press-fit depth |
| Spline Count | 8 | Radial splines for torque transfer |
| Spline Depth | 0.4mm | Cut into socket |
| Flange Diameter | 16.0mm | Mounting/bearing surface |
| Flange Thickness | 3.0mm | Structural support |
| **Total Height** | **17.0mm** | Socket + flange + hub |

### Material Properties

**Recommended Materials:**
- **PETG** (preferred) - Good strength, wear resistance, easy to print
- **Nylon** - Excellent strength and flexibility, more challenging to print
- **ABS** - Acceptable, but may be brittle under shock loads

**NOT Recommended:**
- PLA - Too brittle for mechanical loads

## 3D Printing Instructions

### Print Settings

```
Material:        PETG or Nylon
Layer Height:    0.15mm (or finer for best accuracy)
Infill:          100% (solid)
Wall Lines:      4+ (for strength)
Top/Bottom:      5+ layers
Print Speed:     40-50 mm/s (slower for better accuracy)
Temperature:     PETG: 230-250°C / Nylon: 240-260°C
Bed Temp:        PETG: 70-80°C / Nylon: 80-90°C
Supports:        None required
Brim/Raft:       Optional (helps with bed adhesion)
```

### Print Orientation

**Print with gear hub pointing UP** (splined socket on build plate)

```
     ↑ Gear Hub (5mm shaft)
     |
  ═══════  Flange
     |
     ↓ Splined Socket (on build plate)
```

**Why this orientation:**
- Socket base provides stable platform
- Hub prints vertically for best dimensional accuracy
- No overhangs requiring support
- Layer lines run perpendicular to torque loads

## Assembly Instructions

### 1. Test Fit Components

Before final assembly:
- **Test XL330 shaft fit**: Socket should be snug but not require excessive force
- **Test gear bore fit**: 5mm hub should slide in with minimal play
- **Check set screw alignment**: Flat should be accessible

### 2. Adjust Tolerances (if needed)

If fit is incorrect, edit `dynamixel_xl330_gear_adapter.scad`:

```openscad
// Too tight on motor shaft? Increase this:
shaft_socket_tolerance = 0.2;  // Try 0.3 or 0.4

// Hub too loose in gear? Decrease this:
hub_tolerance = -0.1;  // Try -0.15 or -0.2
```

Regenerate STL:
```bash
openscad -o fabricate/dynamixel_xl330_gear_adapter.stl \
         fabricate/dynamixel_xl330_gear_adapter.scad
```

### 3. Install Adapter on Motor

1. **Align splines** - Rotate adapter to match XL330 output shaft splines
2. **Press fit** - Push adapter onto shaft with firm, even pressure
3. **Seat fully** - Socket should bottom out on motor face
4. **Check alignment** - Adapter should be perpendicular to motor face

> [!TIP]
> If adapter is very tight, gently tap with rubber mallet. DO NOT force or hammer hard - plastic may crack.

### 4. Mount Gear

1. **Slide gear** onto 5mm hub
2. **Rotate to align** set screw hole with flat on hub
3. **Insert M3 set screw** into gear
4. **Tighten set screw** against flat (snug, not over-tight)

> [!WARNING]
> **Do not over-tighten set screw!** Plastic will deform. Tighten until snug, then 1/4 turn more.

### 5. Test Operation

1. **Hand rotation** - Turn gear by hand, should rotate smoothly
2. **Check wobble** - Minimal radial play
3. **Power test** - Run servo at 25% torque limit, verify no slipping
4. **Full load test** - Gradually increase torque, monitor for slippage

## Torque Limits

| Material | Estimated Max Torque | Notes |
|----------|---------------------|-------|
| PETG | ~2.0 N⋅m | 55% of XL330 max (3.6 N⋅m) |
| Nylon | ~2.5 N⋅m | 70% of XL330 max |
| ABS | ~1.5 N⋅m | 40% of XL330 max |

> [!CAUTION]
> These are **estimates**. Start with low torque limits in software and test incrementally. Monitor for:
> - Slipping between adapter and shaft
> - Gear slipping on hub
> - Plastic deformation or cracking

## Maintenance

- **Inspect regularly** for wear, especially on splines and set screw flat
- **Re-tighten set screw** if gear develops play
- **Replace adapter** if splines show significant wear or cracking
- **Keep spare** - print extras while printer is set up

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Adapter won't fit on shaft | Tolerance too tight | Increase `shaft_socket_tolerance` |
| Adapter slips on shaft | Tolerance too loose | Decrease tolerance, add set screw to adapter |
| Gear wobbles on hub | Hub too small | Decrease `hub_tolerance` (more negative) |
| Gear won't slide on hub | Hub too large | Increase `hub_tolerance` (less negative) |
| Set screw damages hub | Over-tightening | Tighten less, consider metal insert |
| Adapter cracks during install | Material too brittle | Use PETG or Nylon, not PLA/ABS |

## Future Improvements

If this design works well, consider:
- **Metal version** - Machine from aluminum for higher torque capacity
- **Dual set screws** - Add second set screw 90° from first
- **Locking compound** - Use threadlocker on set screw
- **Bearing surface** - Add thrust bearing between flange and motor

---

**Design Date**: December 10, 2025  
**Project**: Orbigator DYNAMIXEL Integration  
**Motor**: DYNAMIXEL XL330-M288-T (LAN axis)
