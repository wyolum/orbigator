"""
Example: Orbigator Boot Initialization with Extended Position Mode

This demonstrates the recommended power-on routine:
1. Read current motor positions (prevents jumps!)
2. Use those positions as baseline for all movements
3. Demonstrate continuous forward motion from current position
"""

from dynamixel_extended_utils import orbigator_init, write_dword, read_present_position
import time

def main():
    print("="*60)
    print("ORBIGATOR BOOT SEQUENCE - EXTENDED POSITION MODE")
    print("="*60)
    print()
    
    # CRITICAL: Read current positions before any movement!
    lan_position, aov_position = orbigator_init()
    
    if lan_position is None or aov_position is None:
        print("\n✗ Initialization failed!")
        return
    
    print()
    print("="*60)
    print("DEMONSTRATION: Continuous Forward Motion")
    print("="*60)
    print()
    print("Both motors will move forward from their current positions.")
    print("This demonstrates proper baseline usage.")
    print("Press Ctrl+C to stop.")
    print()
    
    # Movement parameters
    TICKS_PER_DEGREE = 4096 / 360.0
    increment_degrees = 5  # Move 5° per step
    increment_ticks = int(increment_degrees * TICKS_PER_DEGREE)
    
    try:
        step = 0
        while True:
            step += 1
            
            # Increment from current baseline
            lan_position += increment_ticks
            aov_position += increment_ticks
            
            # Send commands
            write_dword(1, 116, lan_position)
            write_dword(2, 116, aov_position)
            
            # Display
            lan_rot = lan_position / 4096.0
            aov_rot = aov_position / 4096.0
            
            print(f"Step {step:3d} | LAN: {lan_position:8d} ({lan_rot:6.2f} rot) | "
                  f"AoV: {aov_position:8d} ({aov_rot:6.2f} rot)")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print()
        print("="*60)
        print("✓ DEMONSTRATION STOPPED")
        print("="*60)
        print()
        print(f"Final positions:")
        print(f"  LAN: {lan_position} ({lan_position/4096.0:.2f} rotations)")
        print(f"  AoV: {aov_position} ({aov_position/4096.0:.2f} rotations)")
        print()
        print("Motors will hold position. These values are your new baseline.")
        print("On next boot, orbigator_init() will read these positions.")

if __name__ == "__main__":
    main()
