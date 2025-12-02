# Orbigator MicroPython Firmware

This directory contains the firmware for the Orbigator orbital mechanics simulator project running on a Raspberry Pi Pico 2.

## Main Firmware

### `orbigator.py`
The main application file. Implements a 4-state orbital simulator:

- **State 0: Set Altitude**
  - Adjust orbital altitude from 200km to 2000km (10km increments)
  - Displays computed orbital period
- **State 1: Set LAN (Longitude of Ascending Node)**
  - Adjust LAN angle (1° increments)
  - Motor moves to position (shortest path)
- **State 2: Set AOV (Argument of Vertex/True Anomaly)**
  - Adjust AOV angle (1° increments)
  - Motor moves to position (shortest path)
- **State 3: RUN Simulation**
  - Simulates orbital motion in real-time
  - **AOV Motor**: Rotates at orbital period rate (1 rev / period)
  - **LAN Motor**: Rotates at precession rate (J2 perturbation + Earth rotation)
  - Motors auto-power-off after 250ms idle to save power

**Controls:**
- **Encoder**: Adjust values / positions
- **Button**: Cycle through states (0 -> 1 -> 2 -> 3 -> 0)

## Test & Utility Files

- **`button_test.py`**: Tests the encoder rotation and button press. Useful for verifying wiring.
- **`confirm_back_test.py`**: Tests the dedicated CONFIRM (GP26) and BACK (GP27) buttons.
- **`lan_aov_toggle_integration_test.py`**: Earlier integration test with a 3-state system (LAN control, AOV control, Continuous run).

## Hardware Pinout

**Motors:**
- **LAN (DRV8834)**: STEP=GP14, DIR=GP15, nSLEEP=GP12, nENBL=GP13, M0=GP10, M1=GP11
- **AOV (ULN2003)**: IN1=GP2, IN2=GP3, IN3=GP22, IN4=GP26

**User Interface:**
- **Encoder**: A=GP6, B=GP7, SW=GP8 (all pull-ups)
- **OLED**: I2C0 SDA=GP4, SCL=GP5 (SH1106 or SSD1306)
