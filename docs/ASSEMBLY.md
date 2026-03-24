# Orbigator Assembly Instructions

This guide provides step-by-step instructions for assembling the Orbigator hardware and electronics based on the provided 3D printed parts and bill of materials.

## Prerequisites

Before starting, ensure you have all the parts listed in the [BOM](../README.md#bill-of-materials-bom), including:
*   3D Printed Parts (from `fabricate/stls/Production/`)
*   Electronics (Pico 2W, DYNAMIXEL motors, display, custom PCB/proto-board)
*   Hardware (1010 extruded aluminum stock, screws, M3 magnets, spring arms, globe)

---

## 1. Preparation

1.  **Assign Motor IDs**: Configure and assign the correct IDs to the Angle of View (AoV) and Equatorial (EQX) DYNAMIXEL motors using Dynamixel Wizard or the [appropriate setup script](../software/setup_motors.py).
2.  **3D Printing**: Print all required components from the `fabricate/stls/Production/` directory. Pay attention to the filename prefixes for the required quantities (e.g., `3_swingarm.stl` means print 3 copies).

## 2. Upper Mechanism (AoV)

3.  **Mount AoV Motor**: Attach the AoV motor to the 3D-printed `inclination_aov_mount`.
4.  **Attach Aluminum Stock**: Secure the 1010 extruded aluminum stock to the `inclination_aov_mount` at your target orbital inclination. Since the mount uses 5-degree increments, for the ISS, set this to **50 degrees**.
5.  **Test Fit Height**: Insert the 1010 aluminum stock into the `full_assembly` to verify the fit. You will set the final **73mm clearance** between the `full_assembly` and the inclination mount during the final assembly stage.

## 3. Lower Mechanism (EQX)

6.  **Mount EQX Drive Elements**: Attach the drive shaft and drive gear to the EQX motor.
7.  **Secure EQX Motor**: Fasten the EQX motor to the `full_assembly` using two standard mounting screws.
8.  **Engage Ring Gear**: Engage the EQX ring gear with the drive gear. Fasten the assembly together using the 3x printed spring arms and 3D printed washers to ensure proper tension and alignment.

## 4. Electronics Assembly

9.  **Prepare the Board**: Solder female headers onto the main board to socket the Raspberry Pi Pico 2W, the OLED display/encoder, and the motor connections.
10. **Mount Electronics**: Attach the completed electronics assembly unit using 4x screws to its designated housing or base `sled_3`.
11. **Route Cables**: 
    *   Thread the EQX motor cable through the center hole. *(Note: You may need to temporarily remove the 1010 aluminum stock to do this. If removed, reinsert it and verify the 73mm spacing is maintained).*
    *   Attach the AoV motor cable to the EQX motor pass-through to daisy-chain the data and power.

## 5. Final Assembly & Calibration

12. **Assemble the Pointer**: Embed the M3 magnets into the AoV arm, then attach the AoV arm directly to the AoV motor.
13. **Program the Pico 2W**: Flash the MicroPython firmware and upload the project code to the Pico 2W.
14. **System Test**: Run initial tests (e.g., `tests/motion_test.py` and `tests/test_motors.py`) to verify motor communication, movement, and display functionality.
15. **Globe Installation**: Run the homing sequence to move the motors to their zero positions. Once homed, carefully add the globe and the globe interface mount to complete the build!
