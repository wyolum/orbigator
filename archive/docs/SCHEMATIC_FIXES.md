# Required Schematic Fixes

Based on review of `kicad/orbigator.net` vs `ORBIGATOR_CIRCUIT_DIAGRAM.txt` (updated).

## 1. Buffer Pull-Up Voltage Logic (CONFIRMED)
User has tested and confirmed that the Data Bus pull-up (R1) should be to **3.3V**, not 5V.
- **Old Schematic**: R1 connected to +5V.
- **Action**: Connect `R1` (10kΩ) to **+3.3V** rail instead of +5V.
    - This protects the 3.3V-powered buffer (74HC126) from seeing 5V on its output/feedback path.
    - **Verify**: R1 should connect `DATA_BUS` to `+3V3`.

## 2. Review I2C Pull-ups
- Schematic seems correct (R2, R3 to 3.3V). Just re-confirm. 
