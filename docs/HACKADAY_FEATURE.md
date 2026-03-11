# 📰 Hackaday Feature: The Orbigator

The Orbigator was officially featured on Hackaday on March 8, 2026. This document preserves the article and key community discussion for the project's historical record.

---

## Article: "The Orbigator: Satellite Tracking With Style"
**Published**: March 8, 2026  
**Source**: [Hackaday](https://hackaday.com/2026/03/08/the-orbigator-satellite-tracking-with-style/)

> What hardware hacker doesn’t have a soft spot for transparent cases? While they may have fallen out of mainstream favor, they have an undeniable appeal to anyone with an interest in electronic or mechanical devices. Which is why the Orbigator built by **[wyojustin]** stands out among similar desktop orbital trackers we’ve seen.
>
> Conceptually, it’s very similar to the International Space Station tracking lamp that [Will Dana] built in 2025. In fact, [wyojustin] cites it specifically as one of the inspirations for this project. But unlike that build, which saw a small model of the ISS moving across the surface of the globe, a transparent globe is rotated around the internal mechanism. This not only looks gorgeous, but solves a key problem in [Will]’s design — that is, there’s no trailing servo wiring that needs to be kept track of.
>
> For anyone who wants an Orbigator of their own, [wyojustin] has done a fantastic job of documenting the hardware and software aspects of the build, and all the relevant files are available in the project’s GitHub repository.
>
> The 3D printable components have been created with OpenSCAD, the firmware responsible for calculating the current position of the ISS on the Raspberry Pi Pico 2 is written in MicroPython, and the PCB was designed in KiCad. Incidentally, we noticed that Hackaday alum [Anool Mahidharia] appears to have been lending a hand with the board design.
>
> As much as we love these polished orbital trackers, we’ve seen far more approachable builds if you don’t need something so elaborate. If you’re more interested in keeping an eye out for planes and can get your hands on a pan-and-tilt security camera, it’s even easier.

---

## 💬 Community Highlights: The Propagator Debate

A notable discussion emerged regarding the implementation of the orbital propagator:

**Andrew (March 9, 2026 at 1:12 pm):**
> Hopefully he ported the “predict” program to Micropython and didn’t just roll his own…

**JUSTIN J SHAW (March 9, 2026 at 2:58 pm):**
> I generally agree—leveraging proven code is usually the way to go. However, for this specific application, a full port is less crucial than it might seem. Because Low Earth Orbits (LEO) must be nearly circular to avoid serious Earth drag, the two main motions—Argument of Vehicle (AoV) and Equator Crossing (EQX)—operate at nearly constant rates.
>
> Solving Kepler’s equation numerically handles the primary deviations in the AoV rate, and we can ignore the negligible EQX variations since Earth's rotation is the dominant factor there. For a physical pointer with mechanical tolerances, this lightweight approach provides a perfectly accurate visual without the overhead of a legacy library.

### Technical Context
The result of this discussion was a refinement of the project documentation to emphasize the "Hardware-Optimized" nature of the custom SGP4 implementation. Rather than using a heavy, generalized port, the Orbigator uses a custom MicroPython engine tuned specifically for real-time physical tracking, where mechanical and visual tolerances allow for a much leaner mathematical model.
