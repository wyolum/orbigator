"""
Automated Motor Multi-Turn Test
================================
Tests each motor by:
1. Turn 5 times forward (1800°)
2. Verify position increased by ~1800°
3. Turn 5 times back (-1800°)
4. Verify position returned to start

Uses config file for speed limits.

Run: import tests.turn_test as t; t.run_test()
"""

from machine import Pin, I2C
import time
import json

from oled_display import OledDisplay
from dynamixel_motor import DynamixelMotor

# Initialize
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
display = OledDisplay(i2c)

# Load config for speed limits
try:
    with open("orbigator_config.json", "r") as f:
        config = json.load(f)
    EQX_SPEED = config["motors"]["eqx"]["speed_limit"]
    AOV_SPEED = config["motors"]["aov"]["speed_limit"]
    print(f"Config loaded: EQX speed={EQX_SPEED}, AoV speed={AOV_SPEED}")
except Exception as e:
    print(f"Config load failed, using defaults: {e}")
    EQX_SPEED = 50
    AOV_SPEED = 20

TURNS = 2.25
DEGREES_PER_TURN = 360
TOTAL_DEGREES = TURNS * DEGREES_PER_TURN  # 810°
TOLERANCE = 30.0  # Acceptable error in degrees


def wait_for_arrival(motor, target_ticks, timeout_ms=60000):
    """Wait for motor to reach target position (absolute ticks)."""
    start = time.ticks_ms()
    last_pos = None
    settled_count = 0
    
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        motor.update_position()
        current_ticks = motor._raw_ticks
        delta_ticks = abs(current_ticks - target_ticks)
        
        # Convert to degrees for display
        current_deg = motor.output_degrees
        target_deg = target_ticks / 4096 * 360
        
        # Check if close enough
        if delta_ticks < 100:  # ~8.8 degrees
            # Check if settled (position stable)
            if last_pos == current_ticks:
                settled_count += 1
                if settled_count >= 3:
                    return True, current_ticks
            else:
                settled_count = 0
        
        last_pos = current_ticks
        
        # Progress update
        if time.ticks_diff(time.ticks_ms(), start) % 2000 < 100:
            print(f"  Progress: {current_ticks} ticks ({current_deg:.0f}°) -> {target_ticks} ({target_deg:.0f}°)")
        
        time.sleep_ms(200)
    
    motor.update_position()
    return False, motor._raw_ticks


def test_motor_turns(motor, speed):
    """Test a single motor with forward and reverse turns."""
    print(f"\n{'='*40}")
    print(f"TESTING: {motor.name} (speed={speed})")
    print(f"{'='*40}")
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    # Get starting position (absolute ticks)
    motor.update_position()
    start_ticks = motor._raw_ticks
    start_deg = motor.output_degrees
    print(f"Start: {start_ticks} ticks ({start_deg:.1f}°)")
    
    # Configure motor
    motor.set_speed(speed)
    motor.enable_torque()
    
    # === FORWARD TEST: 5 turns ===
    print(f"\n[1] FORWARD {TURNS} turns ({TOTAL_DEGREES}°)...")
    
    display.clear()
    display.text(f"{motor.name} FWD", 0, 0)
    display.text(f"{TURNS} turns", 0, 16)
    display.show()
    
    # Calculate target in ticks (not degrees)
    ticks_per_turn = 4096
    target_ticks_fwd = start_ticks + (TURNS * ticks_per_turn)
    
    motor.set_position(target_ticks_fwd / 4096 * 360)  # Convert to degrees for API
    
    arrived, final_ticks = wait_for_arrival(motor, target_ticks_fwd)
    
    actual_travel_ticks = final_ticks - start_ticks
    actual_travel_deg = actual_travel_ticks / 4096 * 360
    expected_ticks = TURNS * ticks_per_turn
    
    print(f"  Expected: {expected_ticks} ticks ({TOTAL_DEGREES}°)")
    print(f"  Actual: {actual_travel_ticks} ticks ({actual_travel_deg:.1f}°)")
    
    if abs(actual_travel_ticks - expected_ticks) < 200:  # ~17 degrees tolerance
        print(f"  ✓ Forward PASSED")
        results["passed"] += 1
    else:
        print(f"  ✗ Forward FAILED")
        results["failed"] += 1
        results["errors"].append(f"Forward: expected {expected_ticks}, got {actual_travel_ticks}")
    
    # === REVERSE TEST: 5 turns back ===
    print(f"\n[2] BACK {TURNS} turns...")
    
    display.clear()
    display.text(f"{motor.name} BACK", 0, 0)
    display.text(f"{TURNS} turns", 0, 16)
    display.show()
    
    target_ticks_back = start_ticks  # Return to start
    motor.set_position(start_deg)  # Use original degree value
    
    arrived, final_ticks = wait_for_arrival(motor, target_ticks_back)
    
    return_error_ticks = abs(final_ticks - start_ticks)
    return_error_deg = return_error_ticks / 4096 * 360
    
    print(f"  Target: {start_ticks} ticks")
    print(f"  Final: {final_ticks} ticks (error: {return_error_ticks} ticks, {return_error_deg:.1f}°)")
    
    if return_error_ticks < 200:
        print(f"  ✓ Reverse PASSED")
        results["passed"] += 1
    else:
        print(f"  ✗ Reverse FAILED")
        results["failed"] += 1
        results["errors"].append(f"Reverse: error {return_error_ticks} ticks")
    
    return results


def run_test():
    """Run the full multi-turn test on both motors."""
    print("\n" + "="*50)
    print("AUTOMATED MULTI-TURN TEST")
    print(f"Testing {TURNS} turns forward and back")
    print("="*50)
    
    display.clear()
    display.text("TURN TEST", 20, 0)
    display.text(f"{TURNS}x fwd/back", 16, 20)
    display.text("Init motors...", 0, 44)
    display.show()
    
    try:
        eqx = DynamixelMotor(1, "EQX")
        aov = DynamixelMotor(2, "AoV")
    except Exception as e:
        print(f"Motor init failed: {e}")
        display.clear()
        display.text("MOTOR ERROR", 10, 28)
        display.show()
        return
    
    total_passed = 0
    total_failed = 0
    
    # Test EQX
    result = test_motor_turns(eqx, EQX_SPEED)
    total_passed += result["passed"]
    total_failed += result["failed"]
    
    # Test AoV  
    result = test_motor_turns(aov, AOV_SPEED)
    total_passed += result["passed"]
    total_failed += result["failed"]
    
    # Summary
    print("\n" + "="*50)
    print(f"RESULTS: {total_passed}/{total_passed+total_failed} passed")
    print("="*50)
    
    display.clear()
    display.text("TURN TEST", 20, 0)
    display.text("COMPLETE", 28, 16)
    display.text(f"{total_passed}/{total_passed+total_failed} passed", 20, 40)
    display.show()
    
    return {"passed": total_passed, "failed": total_failed}


if __name__ == "__main__":
    run_test()
