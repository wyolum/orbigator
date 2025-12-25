# Thank You Note for bkerler/sattracker

Hi @bkerler,

Thank you for creating and sharing the sattracker project! Your Plan13 implementation has been incredibly helpful for our Orbigator project.

## About Orbigator

We're building a physical orbital mechanics demonstrator using:
- Raspberry Pi Pico 2W (MicroPython)
- Two DYNAMIXEL XL330 servo motors
- OLED display + rotary encoder UI
- Real-time satellite tracking with your Plan13 algorithm

The device tracks satellites by moving a pointer around a globe, showing:
- Orbital mechanics (including elliptical orbits with Kepler's equation)
- Real-time position updates
- Support for both manual orbital parameters and TLE-based tracking

Your Plan13 implementation was perfect for MicroPython - much simpler and more memory-efficient than SGP4. We adapted it for the Pico 2W and it's working beautifully!

## Project Links

- GitHub: https://github.com/wyolum/orbigator
- Hardware: Pico 2W + DYNAMIXEL motors + 3D printed mounts

## Attribution

We've kept your original copyright and attribution in plan13.py. Thank you for making this available under an open license!

If you're interested, we'd love to collaborate or get your feedback on the project.

Best regards,
Justin (WyoLum)
