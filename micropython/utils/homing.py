"""
Motor Homing Script for GearClock2

Zeros out the motor position in Extended Position Mode.
Use this when attaching a new arm/gear to align it with motor position 0.

Usage:
    mpremote run homing.py
"""

from machine import Pin, UART
import time
from gearclock_config import MOTOR_ID, MOTOR_BAUDRATE, UART_TX_PIN, UART_RX_PIN
from dynamixel_motor import DynamixelMotor

def main():
    print("="*60)
    print("GearClock2 Motor Homing Script")
    print("="*60)
    print()
    
    # Initialize UART
    print("Initializing UART...")
    uart = UART(0, baudrate=MOTOR_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
    time.sleep_ms(100)
    print(f"✓ UART initialized at {MOTOR_BAUDRATE} baud")
    print()
    
    # Create motor controller
    print("Initializing motor controller...")
    motor = DynamixelMotor(MOTOR_ID, "GearClock", gear_ratio=1.0)
    print(f"✓ Motor {MOTOR_ID} ready")
    print()
    
    # Step 1: Read current position
    print("Step 1: Reading current position...")
    current_pos = motor.get_angle_degrees()
    if current_pos is not None:
        print(f"✓ Current position: {current_pos:.2f}°")
    else:
        print("✗ Failed to read position")
        print("  Check motor connection and power")
        return
    print()
    
    # Step 2: Move to position 0
    print("Step 2: Moving to position 0...")
    print("This will move the motor to align with zero position.")
    print("Make sure the arm/gear is attached and can move freely!")
    print()
    
    try:
        input("Press Enter to continue or Ctrl+C to abort...")
    except:
        pass
    print()
    
    # Set target position to 0 degrees
    target_pos = 0.0
    print(f"Setting goal position to {target_pos}°...")
    
    success = motor.set_angle_degrees(target_pos)
    if success:
        print("✓ Goal position set")
    else:
        print("✗ Failed to set goal position")
        return
    print()
    
    # Step 3: Monitor movement
    print("Step 3: Monitoring movement to zero...")
    start_time = time.time()
    last_pos = current_pos
    
    while True:
        time.sleep_ms(200)
        pos = motor.get_angle_degrees()
        
        if pos is not None:
            elapsed = time.time() - start_time
            print(f"  Position: {pos:7.2f}° | Time: {elapsed:.1f}s")
            
            # Check if reached target (within 0.5°)
            if abs(pos - target_pos) < 0.5:
                print()
                print("="*60)
                print("✓ HOMING COMPLETE!")
                print(f"  Final position: {pos:.2f}°")
                print("="*60)
                print()
                print("The motor is now at position 0.")
                print("You can now align your arm/gear with this position.")
                print()
                print("Note: The motor will hold this position until powered off")
                print("      or another command is sent.")
                break
            
            # Timeout after 30 seconds
            if elapsed > 30:
                print()
                print("⚠ Timeout - motor did not reach zero position")
                print(f"  Current position: {pos:.2f}°")
                print("  The motor may be stuck or moving very slowly")
                break
            
            # Check if motor stopped moving (no change for 2 seconds)
            if abs(pos - last_pos) < 0.2 and elapsed > 2:
                print()
                print("⚠ Motor appears to have stopped moving")
                print(f"  Current position: {pos:.2f}°")
                print(f"  Target position: {target_pos:.2f}°")
                print(f"  Error: {abs(pos - target_pos):.2f}°")
                break
            
            last_pos = pos
        else:
            print("  ✗ Failed to read position")
            break
    
    print()
    print("Homing script complete.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Homing aborted by user")
    except Exception as e:
        print(f"Error: {e}")
        import sys
        sys.print_exception(e)

