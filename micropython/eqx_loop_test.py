"""
EQX Motor Loop Test - Forward and Back

This script tests the EQX motor (ID 1) by moving it forward one full turn (360°)
and then back to the starting position, in a continuous loop.

This helps identify:
- Motor response and movement
- Position tracking accuracy
- Any mechanical binding or issues
- Communication reliability

Usage:
1. Upload to Pico 2
2. Run in Thonny or REPL
3. Watch the motor and monitor output
4. Press Ctrl+C to stop
"""

from dynamixel_motor import DynamixelMotor
from dynamixel_extended_utils import set_extended_mode
import time

# Configuration
EQX_MOTOR_ID = 1
EQX_GEAR_RATIO = 120.0 / 11.0  # Ring gear ratio
SPEED_LIMIT = 100  # Moderate speed for testing (higher = slower)
LOOP_DELAY_MS = 2000  # Wait 2 seconds between movements

def main():
    print("=" * 60)
    print("EQX MOTOR LOOP TEST - Forward and Back")
    print("=" * 60)
    print()
    print("This will move the EQX motor:")
    print("  1. Forward +360° (one full turn)")
    print("  2. Back -360° (return to start)")
    print("  3. Repeat indefinitely")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    # Configure motor for Extended Position Mode
    print("Configuring EQX motor for Extended Position Mode...")
    if not set_extended_mode(EQX_MOTOR_ID):
        print("❌ Failed to configure Extended Position Mode!")
        print("Check motor connection and power.")
        return
    
    print("✓ Extended Position Mode configured")
    print()
    
    # Initialize motor
    print("Initializing EQX motor...")
    try:
        eqx = DynamixelMotor(EQX_MOTOR_ID, "EQX", gear_ratio=EQX_GEAR_RATIO)
    except RuntimeError as e:
        print(f"❌ Failed to initialize motor: {e}")
        print("Check UART connections and motor power.")
        return
    
    print("✓ Motor initialized")
    print()
    
    # Set speed limit
    print(f"Setting speed limit to {SPEED_LIMIT}...")
    eqx.set_speed_limit(SPEED_LIMIT)
    print()
    
    # Record starting position
    start_position = eqx.output_degrees
    print(f"Starting position: {start_position:.2f}°")
    print()
    
    # Flash LED to indicate start
    print("Flashing LED 3 times to indicate start...")
    eqx.flash_led(count=3, on_time_ms=200, off_time_ms=200)
    time.sleep_ms(1000)
    
    print("=" * 60)
    print("STARTING LOOP - Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    loop_count = 0
    
    try:
        while True:
            loop_count += 1
            print(f"--- Loop {loop_count} ---")
            
            # Move forward one full turn
            target_forward = start_position + 360.0
            print(f"Moving FORWARD to {target_forward:.2f}° (+360°)...")
            eqx.set_angle_degrees(target_forward)
            
            # Wait for movement to complete
            time.sleep_ms(LOOP_DELAY_MS)
            
            # Read actual position
            actual_pos = eqx.get_angle_degrees()
            if actual_pos is not None:
                error = actual_pos - target_forward
                print(f"  Reached: {actual_pos:.2f}° (error: {error:.2f}°)")
            else:
                print("  ⚠️ Failed to read position!")
            
            # Wait before reversing
            time.sleep_ms(500)
            
            # Move back to start
            print(f"Moving BACK to {start_position:.2f}° (-360°)...")
            eqx.set_angle_degrees(start_position)
            
            # Wait for movement to complete
            time.sleep_ms(LOOP_DELAY_MS)
            
            # Read actual position
            actual_pos = eqx.get_angle_degrees()
            if actual_pos is not None:
                error = actual_pos - start_position
                print(f"  Reached: {actual_pos:.2f}° (error: {error:.2f}°)")
            else:
                print("  ⚠️ Failed to read position!")
            
            # Update start position for next loop (to handle any drift)
            start_position = actual_pos if actual_pos is not None else start_position
            
            # Wait before next loop
            time.sleep_ms(500)
            print()
    
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("STOPPED BY USER")
        print("=" * 60)
        print(f"Completed {loop_count} loops")
        
        # Read final position
        final_pos = eqx.get_angle_degrees()
        if final_pos is not None:
            print(f"Final position: {final_pos:.2f}°")
        
        # Flash LED to indicate stop
        print("Flashing LED to indicate stop...")
        eqx.flash_led(count=2, on_time_ms=500, off_time_ms=200)
        print("Done!")

if __name__ == "__main__":
    main()
