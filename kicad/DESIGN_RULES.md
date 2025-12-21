# Design Rules Configuration for Orbigator PCB

This file documents the design rules used for the Orbigator PCB.
These are already configured in `orbigator.kicad_pro` but documented here for reference.

## Trace Widths

| Net Class | Minimum Width | Recommended Width | Notes |
|-----------|---------------|-------------------|-------|
| Default | 0.25mm | 0.25mm | Signal traces |
| Power (+5V, GND) | 1.0mm | 1.5mm | Motor current (up to 2A) |
| +3.3V | 0.5mm | 0.5mm | Low current rail |

## Clearances

| Type | Minimum | Recommended | Notes |
|------|---------|-------------|-------|
| Trace to trace | 0.2mm | 0.3mm | Standard clearance |
| Trace to pad | 0.2mm | 0.25mm | |
| Pad to pad | 0.2mm | 0.25mm | |
| Copper to edge | 0.5mm | 1.0mm | Keep copper away from board edge |

## Vias

| Parameter | Value | Notes |
|-----------|-------|-------|
| Diameter | 0.8mm | Standard via |
| Drill | 0.4mm | Standard drill |
| Annular ring | 0.2mm minimum | (Diameter - Drill) / 2 |

**Via Usage:**
- Use multiple vias for ground connections
- Use thermal relief for ground pads on ground pour
- Avoid vias in pads unless necessary

## Holes

| Type | Diameter | Notes |
|------|----------|-------|
| Mounting holes | 3.2mm | M3 screws, non-plated |
| Through-hole pads | Varies | Per component datasheet |

## Copper Pours

| Layer | Net | Priority | Notes |
|-------|-----|----------|-------|
| Bottom (B.Cu) | GND | High | Fill entire layer |
| Top (F.Cu) | None | - | Route signals only |

**Ground Pour Settings:**
- Clearance: 0.5mm
- Minimum width: 0.5mm
- Thermal relief: 4 spokes, 0.5mm width
- Remove isolated islands: Yes

## Text & Silkscreen

| Element | Size | Thickness | Notes |
|---------|------|-----------|-------|
| Reference designators | 1.0mm | 0.15mm | Must be readable |
| Values | 1.0mm | 0.15mm | Optional on silkscreen |
| Board text | 1.5mm | 0.3mm | Title, version |
| Company name | 1.2mm | 0.25mm | WyoLum |

**Silkscreen Rules:**
- Minimum line width: 0.12mm
- Minimum text height: 0.8mm
- Keep 0.2mm clearance from pads
- No silkscreen on pads or vias

## Solder Mask

| Parameter | Value | Notes |
|-----------|-------|-------|
| Clearance | 0.0mm | Use manufacturer default |
| Minimum width | 0.0mm | Use manufacturer default |

## Manufacturing Constraints

Based on standard PCB manufacturers (JLCPCB, PCBWay, etc.):

| Parameter | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| Trace width | 0.15mm | 0.25mm | We use 0.25mm |
| Trace spacing | 0.15mm | 0.2mm | We use 0.2mm |
| Via drill | 0.3mm | 0.4mm | We use 0.4mm |
| Via diameter | 0.5mm | 0.8mm | We use 0.8mm |
| Hole to hole | 0.25mm | 0.5mm | |
| Board outline | 0.1mm | 0.1mm | Edge.Cuts layer |

## Net Classes

### Default
- Track width: 0.25mm
- Via diameter: 0.8mm
- Via drill: 0.4mm
- Clearance: 0.2mm
- Applies to: All signal nets

### Power
- Track width: 1.0mm
- Via diameter: 0.8mm
- Via drill: 0.4mm
- Clearance: 0.2mm
- Applies to: +5V, +3V3, GND

## Special Considerations

### I2C Bus (SDA, SCL)
- Keep traces short (< 50mm preferred)
- Route together with matched lengths
- Avoid routing near noisy signals
- Pull-ups must be close to master (Pico)

### DYNAMIXEL DATA Bus
- Single trace, keep short
- 10kΩ pull-up to +5V required
- Avoid stubs or branches

### Power Distribution
- Star topology from power input
- Wide traces for motor power
- Multiple vias for ground connections
- Decoupling caps close to ICs

### High-Speed Signals
- None in this design (all signals < 1MHz)
- Standard routing practices sufficient

## Layer Stack

```
┌─────────────────────┐
│   F.SilkS (White)   │  Silkscreen
├─────────────────────┤
│   F.Mask (Green)    │  Solder mask
├─────────────────────┤
│   F.Cu (Copper)     │  Top copper layer (signals)
├═════════════════════┤
│   Core (FR4)        │  1.6mm substrate
├═════════════════════┤
│   B.Cu (Copper)     │  Bottom copper layer (ground pour)
├─────────────────────┤
│   B.Mask (Green)    │  Solder mask
├─────────────────────┤
│   B.SilkS (White)   │  Silkscreen
└─────────────────────┘
```

## DRC Settings

All design rule checks are configured in `orbigator.kicad_pro` under:
- `board.design_settings.rules`
- `board.design_settings.rule_severities`

**Critical Checks:**
- Unconnected items: Error
- Clearance violations: Error
- Track width violations: Error
- Hole clearance: Error
- Copper edge clearance: Error

## References

- KiCad Documentation: https://docs.kicad.org/
- IPC-2221: Generic Standard on Printed Board Design
- IPC-2222: Sectional Design Standard for Rigid Organic Printed Boards
