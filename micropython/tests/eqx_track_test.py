"""
EQX Gear Tracking Test
=======================
Rotates EQX gear one full revolution (360°).
Displays EQX position after each motor revolution.

EQX gear ratio: 120/14 ≈ 8.57:1
One EQX revolution = ~8.57 motor revolutions

Run: import tests.eqx_track_test as t; t.run_test()
"""

from machine import Pin, I2C
import time
import json

from oled_display import OledDisplay
from dynamixel_extended_utils import (
    read_present_position, write_dword, write_byte, set_extended_mode
)

# Hardware
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
display = OledDisplay(i2c)

# Load config
try:
    with open("orbigator_config.json", "r") as f:
        config = json.load(f)
    EQX_ID = config["motors"]["eqx"]["id"]
    GEAR_NUM = config["motors"]["eqx"]["gear_ratio_num"]
    GEAR_DEN = config["motors"]["eqx"]["gear_ratio_den"]
    SPEED = config["motors"]["eqx"]["speed_limit"]
except Exception as e:
    print(f"Config error: {e}, using defaults")
    EQX_ID = 1
    GEAR_NUM = 120.0
    GEAR_DEN = 14.0
    SPEED = 50

GEAR_RATIO = GEAR_NUM / GEAR_DEN  # ~8.57
TICKS_PER_REV = 4096


def ticks_to_motor_degrees(ticks):
    """Convert motor ticks to motor degrees."""
    return (ticks / TICKS_PER_REV) * 360.0


def ticks_to_eqx_degrees(ticks):
    """Convert motor ticks to EQX output degrees."""
    return ticks_to_motor_degrees(ticks) / GEAR_RATIO


def run_test():
    """Track EQX through one full revolution, displaying at each motor revolution."""
    print("\n" + "="*50)
    print("EQX GEAR TRACKING TEST")
    print(f"Gear ratio: {GEAR_RATIO:.2f}:1")
    print(f"EQX 360° = {GEAR_RATIO:.2f} motor revolutions")
    print("="*50)
    
    # Initialize motor
    print("\nInitializing EQX motor...")
    set_extended_mode(EQX_ID)
    write_byte(EQX_ID, 64, 1)  # Enable torque
    write_dword(EQX_ID, 112, SPEED)  # Set speed
    
    # Read starting position
    start_ticks = read_present_position(EQX_ID)
    if start_ticks is None:
        print("ERROR: Cannot read motor position!")
        return
    
    start_eqx = ticks_to_eqx_degrees(start_ticks)
    print(f"Start: {start_ticks} ticks, EQX = {start_eqx:.2f}°")
    
    # Zero reference point
    zero_ticks = start_ticks
    motor_rev_count = 0
    last_motor_rev = 0
    
    # Target: one full EQX revolution in NEGATIVE direction (matches normal operation)
    target_ticks = start_ticks - int(360 * GEAR_RATIO * TICKS_PER_REV / 360)
    target_eqx = -360.0  # We want EQX to reach -360° relative to start
    
    print(f"\nTarget: EQX {target_eqx}° ({int(-GEAR_RATIO * TICKS_PER_REV)} ticks)")
    print("(Negative direction matches normal operation: ~-15°/hour)")
    print("\nTracking motor revolutions...")
    print("-" * 40)
    
    # Display header
    display.clear()
    display.text("EQX TRACKING", 16, 0)
    display.text(f"Ratio: {GEAR_RATIO:.2f}:1", 0, 16)
    display.text("Starting...", 0, 40)
    display.show()
    time.sleep(1)
    
    # Command the move
    write_dword(EQX_ID, 116, target_ticks)  # Goal position
    
    # Track progress
    results = []
    
    while True:
        pos = read_present_position(EQX_ID)
        if pos is None:
            continue
        
        # Calculate positions relative to start
        delta_ticks = pos - zero_ticks
        motor_degrees = ticks_to_motor_degrees(delta_ticks)
        eqx_degrees = motor_degrees / GEAR_RATIO
        
        # Track motor revolutions (use abs for comparison)
        current_motor_rev_abs = int(abs(motor_degrees) / 360)
        
        # Display at each new motor revolution
        if current_motor_rev_abs > last_motor_rev:
            last_motor_rev = current_motor_rev_abs
            motor_rev_count += 1
            
            print(f"Motor Rev {motor_rev_count}: Motor={motor_degrees:.1f}°, EQX={eqx_degrees:.2f}°")
            results.append((motor_rev_count, motor_degrees, eqx_degrees))
            
            # Update OLED
            display.clear()
            display.text("EQX TRACKING (-)", 16, 0)
            display.text(f"Motor Rev: {motor_rev_count}", 0, 20)
            display.text(f"Motor: {motor_degrees:.0f}", 0, 36)
            display.text(f"EQX: {eqx_degrees:.1f}", 0, 52)
            display.show()
        
        # Check if EQX reached -360.0°
        if eqx_degrees <= -360.0:
            print("-" * 40)
            print(f"✓ EQX reached {eqx_degrees:.2f}° after {motor_rev_count} motor revolutions")
            break
        
        # Timeout check (travelled too far in either direction)
        if abs(motor_degrees) > 4000:
            print("ERROR: Motor travelled too far!")
            break
        
        time.sleep_ms(50)
    
    # Final summary
    print("\n" + "="*50)
    print("RESULTS:")
    print(f"  Motor revolutions: {motor_rev_count}")
    print(f"  Final EQX position: {eqx_degrees:.2f}°")
    print(f"  Expected ratio: {GEAR_RATIO:.2f}:1")
    print(f"  Actual ratio: {motor_degrees/eqx_degrees:.2f}:1")
    print("="*50)
    
    # Final display
    display.clear()
    display.text("EQX COMPLETE", 16, 0)
    display.text(f"Revs: {motor_rev_count}", 0, 20)
    display.text(f"EQX: {eqx_degrees:.1f}", 0, 36)
    display.text(f"Ratio: {motor_degrees/eqx_degrees:.2f}:1", 0, 52)
    display.show()
    
    return results


if __name__ == "__main__":
    run_test()
