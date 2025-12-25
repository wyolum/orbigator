# Orbigator MicroPython Firmware

This directory contains the firmware for the Orbigator orbital mechanics simulator project running on a Raspberry Pi Pico 2.

## Main Firmware Architecture

The firmware uses a mode-based architecture for clean UI state management and precise orbital tracking.

### Core Modules
- **`orbigator.py`**: The main entry point. Initializes hardware (motors, display, RTC, encoder) and runs the main event loop.
- **`modes.py`**: Defines the UI states (Orbit, Menu, Setting Editors).
- **`orb_utils.py`**: Core logic for orbital mechanics (Kepler's Laws, J2 Precession), persistence, and motor position reconstruction.
- **`orb_globals.py`**: Central hub for shared state to break circular dependencies.
- **`dynamixel_motor.py`**: Abstraction layer for DYNAMIXEL XL330-M288-T motors.

## Key Features

### 1. Robust State Persistence
The system saves its orbital state (altitude, inclination, absolute motor positions, and timestamp) to `orbigator_config.json`.
- **Flash Protection**: To prevent flash wear, saves only occur when a motor completes a full 360° revolution.
- **Absolute Reconstruction**: On boot, the system reads the raw 0-4095 position from the DYNAMIXEL motors and reconstructs their multi-turn absolute position based on the last saved state.

### 2. Intelligent Catch-up
On startup, the system:
1. Calculates the time elapsed since the last save using the DS3231 RTC.
2. Determines the new target orbital positions.
3. Performs a **shortest-path catch-up move** (max 180°) at a safe speed limit to snap the system into the current real-time state.

### 3. Hardware Safety
- **Speed Caps**: All motors are strictly capped at a **Safety Maximum speed of 10** (Profile Velocity) to prevent mechanical damage or magnets flying off.
- **Soft Limits**: The UI ensures parameters stay within realistic bounds (e.g., altitude 200km - 2000km).

## User Interface (UI)
- **Time Display**: Zulu/UTC format (e.g., `13:24:11Z`).
- **Rotary Encoder**: 
  - **Clockwise**: Navigate Down / Increase Value / Nudge Forward.
  - **Counter-Clockwise**: Navigate Up / Decrease Value / Nudge Backward.
- **Button**: Use the encoder press to toggle targets (AoV vs EQX) or confirm selections.
- **Safety**: The 'Confirm' button is disabled during Orbiting mode to prevent accidental interruptions.

## Hardware Configuration
- **DYNAMIXEL EQX (ID 1)**: Rotates the orbital plane (10.909:1 gear ratio).
- **DYNAMIXEL AoV (ID 2)**: Direct-drive for satellite position.
- **Buffer**: 74HC126 for half-duplex UART communication.
- **RTC**: DS3231 for accurate timekeeping.

## Uploading Firmware
Use `mpremote` or Thonny to upload the entire contents of this directory to your Pico 2.
```bash
mpremote fs cp orb_globals.py orb_utils.py modes.py dynamixel_motor.py orbigator.py :
```
