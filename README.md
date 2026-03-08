# 🌍 Orbigator: The Analog Orbit Propagator

[![Platform: Pico 2](https://img.shields.io/badge/Platform-Raspberry%20Pi%20Pico%202-blue.svg)](https://www.raspberrypi.com/products/raspberry-pi-pico-2/)
[![Language: MicroPython](https://img.shields.io/badge/Language-MicroPython-orange.svg)](https://micropython.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![As seen on Hackaday](https://img.shields.io/badge/As%20seen%20on-Hackaday-black.svg)](https://hackaday.com/2026/03/08/the-orbigator-satellite-tracking-with-style/)

**The Orbigator** is an open-source, physical satellite tracker that turns complex orbital mechanics into a desk-side companion. Powered by the **Raspberry Pi Pico 2** and precision **DYNAMIXEL servos**, it physically points to the ISS (or any satellite) in real-time with zero drift.

---

## 🚀 Why the Orbigator?

Inspired by [Will’s Builds ISS tracker](https://hackaday.com/2025/07/08/touch-lamp-tracks-iss-with-style/), the Orbigator introduces several key technical innovations to the DIY tracker space:

### 🔄 Continuous, Uninterrupted Motion
Unlike traditional trackers that use static globes (requiring wire unwinding every orbit), the Orbigator features a **rotating globe**. This allows for smooth, continuous tracking across multiple revolutions without ever needing to reset or "unwind."

### 🎯 LVLH Attitude Control
The orbital mechanics are implemented directly in the hardware geometry (inclination angle). This ensures the satellite pointer maintains a true **LVLH (Local Vertical, Local Horizontal)** attitude throughout the entire pass—exactly how real satellites orient themselves.

### 🧩 Zero-Drift absolute Positioning
Leveraging the 32-bit absolute resolvers in DYNAMIXEL XL330-M288-T motors, the system recovers its orientation instantly after power cycles. No homing, no limits, and no drift—just persistent, mathematical accuracy.

---

## 🛠️ Technical Deep Dive

### High-Performance Propagator
The heart of the Orbigator is a custom **SGP4 implementation** running natively on the Pico 2's RISC-V cores. It handles real-time TLE propagation, J2 perturbation effects, and coordinate transformations entirely in MicroPython.

### Split-Screen Radar UI
A custom **SH1106 OLED driver** provides a powerful command center:
*   **Live Radar Plot**: A dynamic "Sky Plot" of the current satellite pass.
*   **Localized World Map**: High-speed bitmask rendering provides a 90° ground track view centered on your observer location.

### Smart Persistence
The system monitors its own state and saves to Flash/SRAM only during ideal intervals (e.g., at equator crossings) to maximize flash lifespan while ensuring a perfect "instant-on" recovery.

---

## 📦 Repository Structure

| Path | Description |
|------|-------------|
| [**micropython/**](micropython/) | Firmware: SGP4 propagator, UI stacks, and motor drivers. |
| [**fabricate/**](fabricate/) | Mechanical design: OpenSCAD files for 3D printing and assembly. |
| [**kicad/**](kicad/) | Electronics: PCB designs and schematics. |
| [**web/**](micropython/web/) | Dashboard: Real-time control and configuration via web interface. |

---

## ⚡ Quick Start

1.  **3D Print & Assemble**: Check the [fabricate/](fabricate/) folder for the latest parts.
2.  **Flash MicroPython**: Install the Pico 2 firmware.
3.  **Upload Code**: use Thonny or `mpremote` to copy the `micropython/` files to the board.
4.  **Track!**: Power up and select your satellite from the "SGP4" menu.

---

## 📸 Media

![Hero Shot](images/photo_2026-01-03_17-28-34.jpg)
*The Orbigator tracking the ISS through the night.*

> "A beautiful mix of technical precision and mechanical elegance."

---

## ⚖️ License

Distributed under the MIT License.

---

**Developed with ❤️ by wyojustin**
[GitHub](https://github.com/wyolum/orbigator) | [Hackaday.io](https://hackaday.io/project/orbigator)
