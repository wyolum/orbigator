# Orbigator – An Analog Orbit Propagator

![3D model of Orbigator on a globe](images/2025-07-10_18-57.png)

## About This Project

Orbigator is a small, open‑source device that physically demonstrates how a satellite orbits the Earth. It is inspired by traditional [orreries](https://en.wikipedia.org/wiki/Orrery), the clockwork models that use gears and arms to show the relative motion of the planets. Like an orrery, Orbigator is a mechanical model, but instead of showing the entire solar system it focuses on a single Earth‑orbiting object. It uses a microcontroller and precision servo motors to move a pointer around a real globe, so you can watch the ground track of your favorite satellite in real time.

The system computes orbital mechanics using Kepler's laws and J2 perturbation effects to determine the satellite's instantaneous position. By controlling two motors—one for the Equator crossing (LAN) and one for the Argument of Vehicle (AoV)—Orbigator accurately tracks orbital motion including precession effects.

## Recent Milestone (Dec 2025): Persistence & Catch-up

The project has recently been upgraded with robust state management to ensure it stays in sync with real-time orbits even across power cycles.

- **Revolution-Based Persistence**: To protect the Pico 2 flash from wear, the system now saves its orbital state exactly once per full motor revolution (360° or 4096 ticks).
- **Shortest-Path Catch-up**: On boot, the system checks the DS3231 RTC. If a gap is detected, it calculates the "lost" orbital distance and performs a "chase" move.
  - **Optimization**: The chase always takes the shortest path (max 180° move) to snap to the current target phase.
  - **Hardware Re-Anchoring**: Automatic reconstruction of absolute turn counts from raw motor readings (0-4095 range) on startup.
- **Dynamic Orbital Inclination**: The orbital plane precession (J2 effect) now accounts for user-settable inclination (0.1° precision), allowing accurate tracking of ISS, Polar, or Sun-Sync orbits.
- **Hardware Safety & UI Refinements**: 
  - All motors are strictly capped at a **Safety Maximum speed of 10**.
  - Time is represented in **Zulu format** (e.g., `13:24:11Z`).
  - Consistent dial logic (Clockwise = Navigate Down / Increase Value).
  - Safety buttons: "Confirm" is disabled during tracking to prevent accidental mode exits.

## How It Works

At its core, Orbigator combines open hardware and open software:

- **Microcontroller and firmware** – A Raspberry Pi Pico 2 running MicroPython executes orbital mechanics calculations based on altitude and inclination parameters. The main control code is in `micropython/orbigator.py` and implements Kepler's third law plus J2 precession to compute motor rotation rates.

- **Mechanical actuation** – Two DYNAMIXEL XL330-M288-T servo motors provide precise positioning:
  - **EQX Motor (ID 1)**: Rotates the orbital plane via an 11-tooth drive gear to 120-tooth ring gear (10.909:1 ratio)
  - **AoV Motor (ID 2)**: Direct-drive positioning of the satellite pointer along the orbital path
  
  These motors use Extended Position Control Mode (Mode 4) for continuous multi-revolution tracking without rewinding.

- **Electrical interface** – The circuit uses a 74HC126 tri-state buffer for half-duplex UART communication with the DYNAMIXEL motors. Complete wiring diagrams are in `ORBIGATOR_PIN_ASSIGNMENTS.txt` and `ORBIGATOR_CIRCUIT_DIAGRAM.txt`. A KiCad-compatible netlist is provided in `orbigator_kicad_netlist.py`.

- **User interface** – An OLED display (SH1106) and rotary encoder allow interactive parameter adjustment via a mode-based menu system. A DS3231 RTC maintains accurate timekeeping for orbital propagation.

### Example Assembly

![Oblique view of Orbigator with satellite pointer](images/2025-07-10_18-57.png)

*Oblique view of the assembled device.* The pointer arm holds a small model satellite at its tip and is mounted on a yellow base ring that sits on top of the globe.

![Side view showing the articulated arm and base ring gear](images/2025-07-11_18-12.png)

*Side view showing the curved arm, motor housing and the large ring gear that allows the device to rotate around the globe's axis.*

![Detailed drawing of the globe mount](images/2025-07-28_08-08.png)

*Fabrication drawing of the mount used to attach Orbigator to a globe. Dimensions are provided for reference when milling or 3D‑printing your own mount.*

## Repository Structure

| Directory | Contents |
|-----------|----------|
| `micropython/` | MicroPython firmware including `orbigator.py` (main), `modes.py` (UI), `orb_utils.py` (logic), `dynamixel_motor.py` (driver) |
| `fabricate/` | OpenSCAD source files for 3D printing mechanical components, including full assembly and individual parts |
| `schematics/` | SVG drawings of gears, motor mounts and the equatorial base used for fabrication |
| `images/` | Renderings and fabrication drawings used in this README |

## Key Documentation Files

- **`ORBIGATOR_PIN_ASSIGNMENTS.txt`** - Complete GPIO pin assignments for Pico 2
- **`ORBIGATOR_CIRCUIT_DIAGRAM.txt`** - ASCII circuit diagram showing all connections
- **`orbigator_kicad_netlist.py`** - KiCad-compatible netlist for schematic creation
- **`DYNAMIXEL_DRYLAB_SETUP.md`** - Comprehensive guide to motor configuration and wiring
- **`EXTENDED_POSITION_MODE_GUIDE.md`** - Best practices for continuous rotation
- **`SPEED_LIMIT_QUICKREF.md`** - Critical safety guidelines for motor speeds

## Getting Started

1. **Review the wiring** - Start with `ORBIGATOR_PIN_ASSIGNMENTS.txt`
2. **Configure motor IDs** - Set unique IDs (1 for EQX, 2 for AoV)
3. **Upload firmware** - Copy the `micropython/` directory to your Pico 2
4. **Sync Time** - Use `mpremote setrtc` to initialize the onboard clock
5. **Calibrate** - Run `orbigator.py` and set your preferred altitude and period via the menu

## Why Analog?

Learning about orbital mechanics can be abstract when done purely on a screen. Seeing a physical pointer sweep over a globe makes the concept tangible. By physically rotating around the Earth and adjusting position in real time, Orbigator offers an intuitive way to visualize how a satellite's orbit crosses different latitudes and longitudes. Traditional [orreries](https://en.wikipedia.org/wiki/Orrery) used gears and arms to show planetary motion; Orbigator applies the same mechanical principles to modern satellite tracking.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests to improve the design, firmware or documentation.

## License

This project is released under the MIT License. See LICENSE in the repository for details.
