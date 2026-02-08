"""
TDD Test: OLED Display with Rotary Encoder
===========================================
Test that the OLED display initializes and responds to encoder input.

Run this test by copying to the Pico and running:
    import tests.test_oled_encoder as t; t.run_tests()
"""

from machine import Pin, I2C
import sys

# Pin assignments (from pins.py)
I2C_SDA = 4
I2C_SCL = 5
ENC_A = 6
ENC_B = 7
ENC_BTN = 8

OLED_ADDR = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 64


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


def test_i2c_bus_initializes(result):
    """Test that I2C bus can be initialized on correct pins."""
    try:
        i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)
        result.ok("I2C bus initializes")
        return i2c
    except Exception as e:
        result.fail("I2C bus initializes", str(e))
        return None


def test_oled_detected_on_i2c(result, i2c):
    """Test that OLED display is detected at expected I2C address."""
    if i2c is None:
        result.fail("OLED detected on I2C", "I2C not available")
        return False
    
    devices = i2c.scan()
    if OLED_ADDR in devices:
        result.ok(f"OLED detected at 0x{OLED_ADDR:02X}")
        return True
    else:
        result.fail("OLED detected on I2C", f"Found devices: {[hex(d) for d in devices]}")
        return False


def test_oled_display_initializes(result, i2c):
    """Test that OledDisplay class initializes correctly."""
    if i2c is None:
        result.fail("OledDisplay initializes", "I2C not available")
        return None
    
    try:
        from oled_display import OledDisplay
        display = OledDisplay(i2c)
        result.ok("OledDisplay class initializes")
        return display
    except ImportError:
        result.fail("OledDisplay initializes", "oled_display module not found")
        return None
    except Exception as e:
        result.fail("OledDisplay initializes", str(e))
        return None


def test_oled_can_show_text(result, display):
    """Test that display can show text."""
    if display is None:
        result.fail("OLED can show text", "Display not available")
        return
    
    try:
        display.clear()
        display.text("TEST", 0, 0)
        display.show()
        result.ok("OLED can show text")
    except Exception as e:
        result.fail("OLED can show text", str(e))


def test_encoder_pins_initialize(result):
    """Test that encoder pins can be configured."""
    try:
        pin_a = Pin(ENC_A, Pin.IN, Pin.PULL_UP)
        pin_b = Pin(ENC_B, Pin.IN, Pin.PULL_UP)
        pin_btn = Pin(ENC_BTN, Pin.IN, Pin.PULL_UP)
        result.ok("Encoder pins initialize")
        return (pin_a, pin_b, pin_btn)
    except Exception as e:
        result.fail("Encoder pins initialize", str(e))
        return None


def test_encoder_class_initializes(result):
    """Test that RotaryEncoder class initializes correctly."""
    try:
        from rotary_encoder import RotaryEncoder
        encoder = RotaryEncoder(ENC_A, ENC_B, ENC_BTN)
        result.ok("RotaryEncoder class initializes")
        return encoder
    except ImportError:
        result.fail("RotaryEncoder initializes", "rotary_encoder module not found")
        return None
    except Exception as e:
        result.fail("RotaryEncoder initializes", str(e))
        return None


def test_encoder_has_value_property(result, encoder):
    """Test that encoder has a value property."""
    if encoder is None:
        result.fail("Encoder has value property", "Encoder not available")
        return
    
    try:
        val = encoder.value
        if isinstance(val, int):
            result.ok(f"Encoder has value property (current: {val})")
        else:
            result.fail("Encoder has value property", f"Expected int, got {type(val)}")
    except AttributeError:
        result.fail("Encoder has value property", "No 'value' attribute")
    except Exception as e:
        result.fail("Encoder has value property", str(e))


def run_tests():
    """Run all OLED + Encoder tests."""
    print("\n" + "="*40)
    print("OLED + ENCODER TDD TESTS")
    print("="*40 + "\n")
    
    result = TestResult()
    
    # I2C / OLED tests
    print("I2C / OLED:")
    i2c = test_i2c_bus_initializes(result)
    test_oled_detected_on_i2c(result, i2c)
    display = test_oled_display_initializes(result, i2c)
    test_oled_can_show_text(result, display)
    
    # Encoder tests
    print("\nEncoder:")
    test_encoder_pins_initialize(result)
    encoder = test_encoder_class_initializes(result)
    test_encoder_has_value_property(result, encoder)
    
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
