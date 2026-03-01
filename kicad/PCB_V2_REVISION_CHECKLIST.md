# Orbigator PCB Revision 2 Checklist

This checklist outlines the changes required for the next hardware "spin" (Revision 2), focusing on SMD migration and a robust dual-power supply implementation.

## 1. SMD Component Migration
Replace existing through-hole (THT) and breakout modules with surface-mount (SMD) equivalents.

- [ ] **RTC (U3)**: Switch from the `Fermion DS3232` breakout to a standalone **DS3232MZ+** (SOIC-8) or **DS3232SN#** (SOIC-20).
    - *Note*: This integrates the crystal and provides ±2ppm accuracy.
- [ ] **74HC126 (Buffer)**: Switch from `DIP-14` to **SOIC-14** (e.g., 74HC126D).
- [ ] **Resistors (R1-R3)**: Switch from `Axial THT` to **0805** or **0603** SMD packages.
- [ ] **Battery (BAT1)**: Ensure a footprint for a small SMD coin cell holder (e.g., **CR1220** or **CR1225**) is included to replace the current off-board battery wiring.

## 2. Robust Dual-Power Supply (VBUS / External)
Implement the P-FET "ideal diode" circuit from the **Pico 2 Datasheet (Figure 9)** to manage power from both USB (VBUS) and the Barrel Jack (VEXT).

- [ ] **J1 (Barrel Jack)**: Retain the **5.5mm x 2.1mm Through-Hole** jack for mechanical strength.
- [ ] **P-FET (Q1)**: Add a **DMG2305UX** (SOT-23) P-channel MOSFET.
    - **Source**: Connected to the External 5V supply (from Barrel Jack).
    - **Drain**: Connected to the Pico **VSYS** pin.
    - **Gate**: Connected to Pico **VBUS** (Pin 40).
- [ ] **Schottky Diode (D1)**: Add a secondary Schottky diode (e.g., **B130**) in parallel with the P-FET (Source to Drain) to protect against slow VBUS transitions.
- [ ] **Protection**: Ensure VEXT doesn't exceed 5.5V to protect the Pico VSYS input.
