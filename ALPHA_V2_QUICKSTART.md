# Orbigator PCB V2: Alpha Tester Quick Start Guide

This guide covers bringing up a bare PCB V2 board and testing peripherals.

## 1. Hardware Connections
1. Connect the Pico 2 to the host via USB for data.
2. Connect a 5V power supply to the DC Barrel Jack (J1). The V2 power path isolates the motors from the USB 5V rail; UART Dynamixels will not respond over USB power alone.

## 2. Firmware Deployment
1. Format the Pico 2 flash using `mpremote`:
   ```bash
   mpremote exec "import os; [os.remove(f[0]) for f in os.ilistdir() if f[1] != 0x4000]"
   mpremote exec "import os; [os.rmdir(f[0]) for f in os.ilistdir() if f[1] == 0x4000]"
   ```

2. Clear the local sync checkpoint:
   ```bash
   rm .last_sync
   ```

3. Run the sync script:
   ```bash
   ./sync.sh
   ```

## 3. Hardware Diagnostics
Run the peripheral diagnostic script:

```bash
mpremote run micropython/utils/super_test.py
```

**Diagnostic Output Variables:**
1. **Row 1:** RTC Date (`YY-MM-DD`) and SRAM status (`SRAM:OK`). 
2. **Row 2:** Current phase of the active motor (`Mot: EQX 123dg`).
3. **Row 3:** RTC Time (`Time:12:30:15`).
4. **Row 4:** Encoder Value (`Enc:X`) and switch states `[X][B][C]` (Encoder Click, Back, Confirm).

**Validation Steps:**
1. Turn the rotary encoder. The active motor should advance 10 degrees per tick.
2. Press the `CONFIRM` button. The OLED will toggle to `Mot: AoV`. Turn the encoder to verify physical AoV response.

## 4. Run Main Application
Terminate `super_test.py` (Ctrl+C). Execute `orbigator.py`:

```bash
mpremote run micropython/orbigator.py
```

### Runtime Notes:
1. **Directional Deadband:** Boot alignment respects a forward-only (`direction=1`), 20-degree deadband. If the calculated target is slightly behind the current physical state, the motor will idle until the simulated target catches up.
2. **World Map:** The `sync.sh` payload includes the pre-compiled `world_mask.bin` asset. The map will render immediately upon entering Orbit Mode without invoking runtime generation routines.
