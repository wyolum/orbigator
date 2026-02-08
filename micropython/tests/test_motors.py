"""
TDD Test: Dynamixel Motors (XL330)
===================================
Non-destructive tests for Dynamixel XL330-M288-T motors.
Tests communication, reads position, does NOT move motors.

Run this test:
    import tests.test_motors as t; t.run_tests()
"""

import time

# Motor IDs from config
EQX_MOTOR_ID = 1
AOV_MOTOR_ID = 2


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def ok(self, name):
        self.passed += 1
        print(f"  ✓ {name}")
    
    def fail(self, name, msg=""):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"  ✗ {name}: {msg}")


def test_uart_initializes(result):
    """Test that motor UART can be initialized."""
    try:
        from machine import Pin, UART
        import pins
        uart = UART(pins.DYNAMIXEL_UART_ID, baudrate=57600, bits=8, parity=None, stop=1)
        uart.init(tx=Pin(pins.DYNAMIXEL_TX_PIN), rx=Pin(pins.DYNAMIXEL_RX_PIN))
        dir_pin = Pin(pins.DYNAMIXEL_DIR_PIN, Pin.OUT, value=0)
        result.ok(f"UART initialized (TX=GP{pins.DYNAMIXEL_TX_PIN}, RX=GP{pins.DYNAMIXEL_RX_PIN}, DIR=GP{pins.DYNAMIXEL_DIR_PIN})")
        return True
    except Exception as e:
        result.fail("UART initializes", str(e))
        return False


def test_motor_utils_import(result):
    """Test that motor utilities can be imported."""
    try:
        from dynamixel_extended_utils import read_present_position, ping_motor
        result.ok("dynamixel_extended_utils imports")
        return True
    except ImportError as e:
        result.fail("dynamixel_extended_utils imports", str(e))
        return False


def test_ping_motor(result, motor_id, name):
    """Test that a motor responds to ping."""
    try:
        from dynamixel_extended_utils import ping_motor
        response = ping_motor(motor_id)
        if response:
            result.ok(f"{name} motor (ID={motor_id}) responds to ping")
            return True
        else:
            result.fail(f"{name} motor ping", f"No response from ID={motor_id}")
            return False
    except Exception as e:
        result.fail(f"{name} motor ping", str(e))
        return False


def test_read_position(result, motor_id, name):
    """Test that motor position can be read."""
    try:
        from dynamixel_extended_utils import read_present_position
        pos = read_present_position(motor_id)
        if pos is not None:
            degrees = (pos / 4096.0) * 360.0
            result.ok(f"{name} position: {pos} ticks ({degrees:.1f}°)")
            return pos
        else:
            result.fail(f"{name} read position", "Returned None")
            return None
    except Exception as e:
        result.fail(f"{name} read position", str(e))
        return None


def test_motor_class_initializes(result, motor_id, name):
    """Test that DynamixelMotor class initializes correctly."""
    try:
        from dynamixel_motor import DynamixelMotor
        motor = DynamixelMotor(motor_id, name)
        result.ok(f"DynamixelMotor class initializes for {name}")
        return motor
    except ImportError:
        result.fail(f"DynamixelMotor class initializes ({name})", "dynamixel_motor module not found")
        return None
    except Exception as e:
        result.fail(f"DynamixelMotor class initializes ({name})", str(e))
        return None


def test_motor_has_position_property(result, motor, name):
    """Test that Motor has output_degrees property."""
    if motor is None:
        result.fail(f"{name} has output_degrees", "Motor not available")
        return
    
    try:
        pos = motor.output_degrees
        if isinstance(pos, (int, float)):
            result.ok(f"{name} has output_degrees ({pos:.1f}°)")
        else:
            result.fail(f"{name} has output_degrees", f"Expected number, got {type(pos)}")
    except AttributeError:
        result.fail(f"{name} has output_degrees", "No 'output_degrees' attribute")
    except Exception as e:
        result.fail(f"{name} has output_degrees", str(e))


def run_tests():
    """Run all motor tests (non-destructive, read-only)."""
    print("\n" + "="*40)
    print("DYNAMIXEL MOTOR TDD TESTS (Read-Only)")
    print("="*40 + "\n")
    
    result = TestResult()
    
    # Hardware setup
    print("Hardware Setup:")
    if not test_uart_initializes(result):
        print("\n" + "="*40)
        print("ABORTED: UART init failed")
        print("="*40 + "\n")
        return result
    
    if not test_motor_utils_import(result):
        print("\n" + "="*40)
        print("ABORTED: Motor utils not available")
        print("="*40 + "\n")
        return result
    
    # Test EQX motor
    print("\nEQX Motor (ID=1):")
    eqx_ok = test_ping_motor(result, EQX_MOTOR_ID, "EQX")
    if eqx_ok:
        test_read_position(result, EQX_MOTOR_ID, "EQX")
    
    # Test AoV motor
    print("\nAoV Motor (ID=2):")
    aov_ok = test_ping_motor(result, AOV_MOTOR_ID, "AoV")
    if aov_ok:
        test_read_position(result, AOV_MOTOR_ID, "AoV")
    
    # Test Motor wrapper class
    print("\nMotor Class:")
    eqx_motor = test_motor_class_initializes(result, EQX_MOTOR_ID, "EQX")
    test_motor_has_position_property(result, eqx_motor, "EQX")
    
    aov_motor = test_motor_class_initializes(result, AOV_MOTOR_ID, "AoV")
    test_motor_has_position_property(result, aov_motor, "AoV")
    
    # Summary
    print("\n" + "="*40)
    total = result.passed + result.failed
    print(f"RESULTS: {result.passed}/{total} passed")
    if result.failed > 0:
        print(f"FAILURES: {result.failed}")
        for name, msg in result.errors:
            print(f"  - {name}: {msg}")
    print("="*40 + "\n")
    
    return result


if __name__ == "__main__":
    run_tests()
