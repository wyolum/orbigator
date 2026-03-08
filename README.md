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

![Technical View](images/blog_2026_01_03/render_iso.jpg)
*Mathematical precision translated into mechanical motion.*

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

1.  **3D Print**: High-quality production STLs are located in [**fabricate/stls/Production/**](fabricate/stls/Production/).
2.  **Assemble**: Follow the assembly logic in the [fabricate/](fabricate/) folder.
3.  **Flash MicroPython**: Install the Pico 2 firmware.
4.  **Upload Code**: Use Thonny or `mpremote` to copy the `micropython/` files to the board.
5.  **Track!**: Power up and select your satellite from the "SGP4" menu.

---

## 🧾 Bill of Materials (BOM)

### Electronics
*   **Controller**: [Raspberry Pi Pico 2](https://www.raspberrypi.com/products/raspberry-pi-pico-2/)
*   **Motors**: 2x [DYNAMIXEL XL330-M288-T](https://www.robotis.us/dynamixel-xl330-m288-t/)
*   **Display**: 128x64 SH1106 OLED (I2C)
*   **RTC**: DS3231/DS3232 (ChronoDot recommended)
*   **Logic**: 1x SN74HC126N Quad Tri-State Buffer (for half-duplex UART)
*   **UI**: 1x Rotary Encoder (with Push Switch), 2x Momentary Push Buttons
*   **Passives**: 1x 10kΩ resistor, 2x 4.7kΩ resistors
*   **Power**: 5V 4-5A External Power Supply

### Hardware & Mechanical
*   **Globe**: Standard desktop globe (approx. 10-12")
*   **Bearings**: 3x 13mm OD Bearings (e.g., 624ZZ or similar 13x5x4)
*   **Fasteners**: Self-tapping screws (included with XL330 motors)
*   **3D Parts**: Printed from the `Production/` folder (PLA or PETG)

---

## 📐 3D Printing (Production Parts)

The following parts are required for the full assembly and can be found in `fabricate/stls/Production/`. **The leading number in the filename indicates the required print quantity.**

*   `1_drive_gear.stl` - Main EQX drive
*   `1_flex_aov_arm.stl` - Satellite pointer arm
*   `1_globe_interface.stl` - Secure mount for the globe
*   `1_inclination_aov_mount.stl` - Hardware-implemented inclination bracket
*   `1_sled_3.stl` - Electronic housing and base
*   `1_full_assembly.stl` - Reference model (not for printing)
*   `3_swingarm.stl` - Differential assembly components
*   `3_shim.stl` - Insert for the skate bearings (see `misc.scad` for 13mm dims)
*   `3_washer.stl` - Vertical stop for the ring gear

---

## 📸 Media: As Seen on [WyoLum Blog](https://wyolum.com/orbigator-real-time-satellite-tracker-with-overhead-alert-radar/)

| [**Earthrise Shot**](docs/images/orbigator_lunar_display.jpg) | [**World Map Tracking**](docs/images/orbigator_worldmap_tracking.png) | [**Full Assembly**](docs/images/orbigator_full_assembly.jpg) |
|:---:|:---:|:---:|
| ![Earthrise](docs/images/orbigator_lunar_display.jpg) | ![World Map](docs/images/orbigator_worldmap_tracking.png) | ![Full Assembly](docs/images/orbigator_full_assembly.jpg) |
| *ISS Tracking with Lunar Projection.* | *Real-time World Map Context.* | *Complete Mechanical Assembly.* |

### System Details
| UI & Setup | Electronics | Mechanical Assembly |
|:---:|:---:|:---:|
| ![Setup](images/blog_2026_01_03/setup_screen.jpg) | ![Circuit](images/blog_2026_01_03/breadboard_top.jpg) | ![Globe](images/blog_2026_01_03/globe_cutout.jpg) |
| *Real-time status* | *Pico 2 & Buffers* | *Internal Hardware* |

> "A beautiful mix of technical precision and mechanical elegance."

---

## ⚖️ License

Distributed under the MIT License.

---

**Developed with ❤️ by wyojustin**
[GitHub](https://github.com/wyolum/orbigator) | [Hackaday.io](https://hackaday.io/project/orbigator)
