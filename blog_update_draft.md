# Orbigator Dev Log: From Simulation to Reality

It’s been a while since the last update, and the Orbigator has evolved from a collection of parts and Python scripts into a fully integrated, silent, and precise satellite tracking machine.

Here is the story of how we got here.

<img src="https://wyolum.com/wp-content/uploads/2026/01/setup_screen.jpg" alt="Setup with HUD" />

## 1. The Hardware Pivot: Steppers vs. Smart Servos
We started where most builds start: **Stepper Motors**. They are cheap and ubiquitous. But for a device meant to sit on a desk and track the ISS silently 24/7, they had drawbacks. They vibrate, they make noise ("singing"), and crucially, they are **open-loop**—if the arm gets bumped, the system loses its place and stays lost.

We pivoted to **Dynamixel XL330** smart servos.
*   **Silence**: They are virtually silent at tracking speeds.
*   **Closed-Loop**: They know their absolute position. If you push the arm, it fights back (torque!).
*   **Cabling**: They daisy-chain on a single bus, drastically reducing the rat's nest of wires.

## 2. The Brain Transplant: MicroPython on Pico 2W
We moved the logic from a desktop PC to the **Raspberry Pi Pico 2W**. This brought its own set of challenges, primarily **Floating Point Precision**.

Standard SGP4 libraries assume full 64-bit float precision. On a microcontroller payload, 32-bit floats aren't precise enough to handle Julian Dates (numbers like `2460678.12345`) while keeping second-level accuracy. Our initial tracks were off by thousands of kilometers!

**The Fix**: We refactored the satellite math to use **Integer Unix Timestamps** for the heavy lifting, only converting to small relative offsets when necessary. We verified this against NASA's own trackers, bringing our error down to a negligible **~50km** (on a global scale).

## 3. The Interface: Web & OLED
A tracker isn't fun if you don't know *what* it's tracking.
*   **OLED HUD**: We added a tiny 128x64 display on the base for immediate stats: Latitude, Longitude, and current satellite name.
*   **Web Dashboard**: Since the Pico 2W has WiFi, we built a hosted React dashboard. You can connect to the Orbigator from your phone to see a 3D visualization, change the tracked satellite (ISS, Hubble, Tiangong), and tweak settings live.

<img src="https://wyolum.com/wp-content/uploads/2026/01/render_iso.jpg" alt="Orbigator CAD Render" />

## 4. Tuning the Mechanics
Physics caught up with us. Adding the "Argument of Vehicle" (AoV) assembly—complete with magnets and pennies for counterweights—introduced a pendulum effect. The motor would "wobble" as it tried to hold position.

We wrote a custom auto-tuning script (`tune_wobble.py`) to cycle through PID profiles. We landed on a stiff-but-smooth profile (`P=600, D=0`) and capped the speed. Now, it glides.

<img src="https://wyolum.com/wp-content/uploads/2026/01/breadboard_top.jpg" alt="Mechanism Closeup" />

## 5. What's Next?
The mess of wires you see in the photos is "development aesthetic." It works, but it's fragile.

The next phase is purely hardware. I'm teaming up with **Anool** and **Kevin** to design a custom **Orbigator Control Board** that integrates the Pico, the RTC (Real Time Clock), and the motor drivers into a single, clean PCB.

The code is committed, the math is integer-perfect, and the motor is zeroed. Onward to proper PCBs!
