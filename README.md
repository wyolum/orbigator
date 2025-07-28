Orbigator – an analog orbit propagator

3D model of Orbigator on a globe
About this project

Orbigator is a small, open‑source device that physically demonstrates how a satellite orbits the Earth. It is inspired by traditional orreries, the clockwork models that use gears and arms to show the relative motion of the planets
en.wikipedia.org
. Like an orrery, Orbigator is a mechanical model, but instead of showing the entire solar system it focuses on a single Earth‑orbiting object. It uses a microcontroller, servos and stepper motors to move a pointer around a real globe, so you can watch the ground track of your favourite satellite in real time.

The system takes advantage of publicly available two‑line element (TLE) sets to compute the current position of a satellite. A TLE encodes the orbital elements of an Earth‑orbiting object at a specific epoch; using an appropriate prediction model (such as SGP4) the position and velocity of the object at any other time can be determined
en.wikipedia.org
. TLEs are widely used for space situational awareness and collision‑avoidance analyses
en.wikipedia.org
, and they provide all the information Orbigator needs to keep its pointer aligned with a satellite.
How it works

At its core, Orbigator combines open hardware and open software:

    Microcontroller and firmware – An Arduino‑compatible board runs a simplified orbit propagator based on the SGP4 algorithm, parsing TLE data to determine the satellite’s instantaneous azimuth and elevation. The code lives in the arduino/orbigator directory and can be compiled with the Arduino IDE.

    Mechanical actuation – A stepper motor at the base rotates the pointer ring around the globe to set the orbital plane, while a second motor elevates a carriage to match the satellite’s inclination and altitude. These parts are rendered and assembled from OpenSCAD files in the fabricate/ folder. The design uses 3D‑printed gears and bearings to provide smooth motion. The mount for attaching the mechanism to a globe is shown in the fabrication drawing below.

    Electrical interface – The schematics/ directory contains SVG drawings for the ring gear, azimuth dial and motor mounts. These illustrate hole patterns, gear tooth counts and mounting dimensions. You will also find an eqx_base.svg for the equatorial base that clamps around a standard globe.

Example assembly

Here are some renderings of the design to give an idea of how the parts fit together. All of these images live in this repository’s images/ folder.

A three‑quarter view of the assembled device. The pointer arm holds a small model satellite at its tip and is mounted on a yellow base ring that sits on top of the globe.

Side view showing the curved arm, stepper motor housing and the large ring gear that allows the device to rotate around the globe’s axis.

Fabrication drawing of the mount used to attach Orbigator to a globe. Dimensions are provided for reference when milling or 3D‑printing your own mount.
Repository overview

This repository is organised into several directories:
Directory	Contents
arduino/orbigator	Arduino sketch (orbigator.ino) implementing orbit propagation (using SGP4) and controlling servos.
fabricate/	OpenSCAD source files for 3D printing the mechanical components, including the full assembly (full_assembly.scad) and individual parts.
schematics/	SVG drawings of gears, motor mounts and the equatorial base used for fabrication.
images/	Renderings and fabrication drawings used in this README.
Why analog?

Learning about orbital mechanics can be abstract when done purely on a screen. Seeing a physical pointer sweep over a globe makes the concept tangible. By physically rotating around the Earth and adjusting elevation in real time, Orbigator offers an intuitive way to visualise how a satellite’s orbit crosses different latitudes and longitudes. Traditional orreries used gears and arms to show planetary motion
en.wikipedia.org
; Orbigator applies the same mechanical principles to modern satellite tracking.
Contributing

Contributions are welcome! Feel free to open issues or pull requests to improve the design, firmware or documentation. Ideas for supporting multiple satellites or automating TLE updates would be especially appreciated.
License

This project is released under the MIT License. See LICENSE in the repository for details.


