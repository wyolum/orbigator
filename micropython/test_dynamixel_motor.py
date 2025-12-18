"""
Unit test for DynamixelMotor abstraction layer

Tests the motor class with both direct drive (AoV) and geared (LAN) configurations.
"""

from dynamixel_motor import DynamixelMotor
import time

def test_motor_initialization():
    """Test that motors initialize and read baseline positions"""
    print("="*60)
    print("TEST 1: Motor Initialization")
    print("="*60)
    
    try:
        # Initialize AoV motor (direct drive)
        print("\nInitializing AoV motor (ID 2, direct drive)...")
        aov_motor = DynamixelMotor(2, "AoV", gear_ratio=1.0)
        print(f"✓ AoV motor initialized: {aov_motor}")
        
        # Initialize LAN motor (geared)
        print("\nInitializing LAN motor (ID 1, geared 120/11)...")
        lan_motor = DynamixelMotor(1, "LAN", gear_ratio=120.0/11.0)
        print(f"✓ LAN motor initialized: {lan_motor}")
        
        return lan_motor, aov_motor
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return None, None

def test_absolute_positioning(motor, test_angles):
    """Test setting absolute angles"""
    print(f"\n--- Testing {motor.name} Absolute Positioning ---")
    
    for angle in test_angles:
        print(f"\nSetting {motor.name} to {angle}°...")
        success = motor.set_angle_degrees(angle)
        
        if success:
            time.sleep(1.5)  # Wait for motor to reach position
            
            # Read back position
            actual = motor.get_angle_degrees()
            if actual is not None:
                error = abs(actual - angle)
                print(f"  Target: {angle}°, Actual: {actual:.2f}°, Error: {error:.2f}°")
                
                if error < 2.0:  # Within 2 degrees
                    print(f"  ✓ Position accurate")
                else:
                    print(f"  ⚠ Position error > 2°")
            else:
                print(f"  ✗ Failed to read position")
        else:
            print(f"  ✗ Failed to set position")

def test_relative_movement(motor):
    """Test relative movement"""
    print(f"\n--- Testing {motor.name} Relative Movement ---")
    
    # Get starting position
    start_pos = motor.get_angle_degrees()
    print(f"\nStarting position: {start_pos:.2f}°")
    
    # Move +45°
    print(f"Moving +45°...")
    motor.move_relative_degrees(45)
    time.sleep(1.5)
    
    pos1 = motor.get_angle_degrees()
    print(f"Position after +45°: {pos1:.2f}° (expected ~{start_pos + 45:.2f}°)")
    
    # Move -90°
    print(f"Moving -90°...")
    motor.move_relative_degrees(-90)
    time.sleep(1.5)
    
    pos2 = motor.get_angle_degrees()
    print(f"Position after -90°: {pos2:.2f}° (expected ~{pos1 - 90:.2f}°)")
    
    # Return to start
    print(f"Returning to start...")
    motor.move_relative_degrees(45)
    time.sleep(1.5)
    
    final_pos = motor.get_angle_degrees()
    print(f"Final position: {final_pos:.2f}° (expected ~{start_pos:.2f}°)")

def test_continuous_rotation(motor):
    """Test continuous rotation beyond 360°"""
    print(f"\n--- Testing {motor.name} Continuous Rotation ---")
    
    angles = [0, 360, 720, 1080, 720, 360, 0]
    
    for angle in angles:
        print(f"\nSetting to {angle}°...")
        motor.set_angle_degrees(angle)
        time.sleep(2.0)
        
        actual = motor.get_angle_degrees()
        print(f"  Actual: {actual:.2f}°")

def test_gear_ratio_verification(lan_motor):
    """Verify gear ratio is working correctly for LAN motor"""
    print("\n" + "="*60)
    print("TEST: Gear Ratio Verification (LAN Motor)")
    print("="*60)
    
    # Set globe to 45°
    globe_angle = 45.0
    print(f"\nSetting globe to {globe_angle}°...")
    lan_motor.set_angle_degrees(globe_angle)
    time.sleep(2.0)
    
    # Motor should be at 45 * (120/11) ≈ 490.9°
    expected_motor_degrees = globe_angle * (120.0 / 11.0)
    print(f"Expected motor position: {expected_motor_degrees:.2f}°")
    print(f"Actual motor position: {lan_motor.motor_degrees:.2f}°")
    print(f"Globe position: {lan_motor.output_degrees:.2f}°")
    
    error = abs(lan_motor.output_degrees - globe_angle)
    if error < 2.0:
        print(f"✓ Gear ratio working correctly (error: {error:.2f}°)")
    else:
        print(f"✗ Gear ratio error: {error:.2f}°")

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("DYNAMIXEL MOTOR ABSTRACTION LAYER TEST SUITE")
    print("="*60)
    
    # Test 1: Initialization
    lan_motor, aov_motor = test_motor_initialization()
    
    if lan_motor is None or aov_motor is None:
        print("\n✗ Tests aborted - initialization failed")
        return
    
    time.sleep(1)
    
    # Test 2: Absolute positioning - AoV (direct drive)
    print("\n" + "="*60)
    print("TEST 2: Absolute Positioning (AoV - Direct Drive)")
    print("="*60)
    test_absolute_positioning(aov_motor, [0, 90, 180, 270, 0])
    
    time.sleep(1)
    
    # Test 3: Absolute positioning - LAN (geared)
    print("\n" + "="*60)
    print("TEST 3: Absolute Positioning (LAN - Geared)")
    print("="*60)
    test_absolute_positioning(lan_motor, [0, 45, 90, 180, 0])
    
    time.sleep(1)
    
    # Test 4: Relative movement - AoV
    print("\n" + "="*60)
    print("TEST 4: Relative Movement (AoV)")
    print("="*60)
    test_relative_movement(aov_motor)
    
    time.sleep(1)
    
    # Test 5: Continuous rotation - AoV
    print("\n" + "="*60)
    print("TEST 5: Continuous Rotation (AoV)")
    print("="*60)
    test_continuous_rotation(aov_motor)
    
    time.sleep(1)
    
    # Test 6: Gear ratio verification
    test_gear_ratio_verification(lan_motor)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
    print("\nManual verification required:")
    print("- Motors should move smoothly without jumps")
    print("- Continuous rotation should not rewind")
    print("- LAN motor should rotate ~10.9× more than commanded angle")
    print("- AoV motor should match commanded angle 1:1")

# Run tests
if __name__ == "__main__":
    run_all_tests()
