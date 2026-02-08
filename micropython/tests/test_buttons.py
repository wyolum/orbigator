"""
TDD Test: Buttons (Back and Confirm)
=====================================
Test that Back and Confirm buttons initialize and respond.

Run this test:
    import tests.test_buttons as t; t.run_tests()
"""

from machine import Pin

# Pin assignments (from pins.py)
BACK_BTN_PIN = 9
CONFIRM_BTN_PIN = 10


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


def test_back_button_pin_initializes(result):
    """Test that Back button pin can be configured."""
    try:
        pin = Pin(BACK_BTN_PIN, Pin.IN, Pin.PULL_UP)
        val = pin.value()
        result.ok(f"Back button pin (GP{BACK_BTN_PIN}) initializes, state={val}")
        return pin
    except Exception as e:
        result.fail("Back button pin initializes", str(e))
        return None


def test_confirm_button_pin_initializes(result):
    """Test that Confirm button pin can be configured."""
    try:
        pin = Pin(CONFIRM_BTN_PIN, Pin.IN, Pin.PULL_UP)
        val = pin.value()
        result.ok(f"Confirm button pin (GP{CONFIRM_BTN_PIN}) initializes, state={val}")
        return pin
    except Exception as e:
        result.fail("Confirm button pin initializes", str(e))
        return None


def test_buttons_class_initializes(result):
    """Test that Buttons class initializes correctly."""
    try:
        from buttons import Buttons
        buttons = Buttons(BACK_BTN_PIN, CONFIRM_BTN_PIN)
        result.ok("Buttons class initializes")
        return buttons
    except ImportError:
        result.fail("Buttons class initializes", "buttons module not found")
        return None
    except Exception as e:
        result.fail("Buttons class initializes", str(e))
        return None


def test_buttons_has_back_property(result, buttons):
    """Test that Buttons has back_pressed property."""
    if buttons is None:
        result.fail("Buttons has back_pressed", "Buttons not available")
        return
    
    try:
        val = buttons.back_pressed
        if isinstance(val, bool):
            result.ok(f"Buttons has back_pressed property (current: {val})")
        else:
            result.fail("Buttons has back_pressed", f"Expected bool, got {type(val)}")
    except AttributeError:
        result.fail("Buttons has back_pressed", "No 'back_pressed' attribute")
    except Exception as e:
        result.fail("Buttons has back_pressed", str(e))


def test_buttons_has_confirm_property(result, buttons):
    """Test that Buttons has confirm_pressed property."""
    if buttons is None:
        result.fail("Buttons has confirm_pressed", "Buttons not available")
        return
    
    try:
        val = buttons.confirm_pressed
        if isinstance(val, bool):
            result.ok(f"Buttons has confirm_pressed property (current: {val})")
        else:
            result.fail("Buttons has confirm_pressed", f"Expected bool, got {type(val)}")
    except AttributeError:
        result.fail("Buttons has confirm_pressed", "No 'confirm_pressed' attribute")
    except Exception as e:
        result.fail("Buttons has confirm_pressed", str(e))


def run_tests():
    """Run all button tests."""
    print("\n" + "="*40)
    print("BUTTON TDD TESTS")
    print("="*40 + "\n")
    
    result = TestResult()
    
    # Raw pin tests
    print("Raw Pins:")
    test_back_button_pin_initializes(result)
    test_confirm_button_pin_initializes(result)
    
    # Buttons class tests
    print("\nButtons Class:")
    buttons = test_buttons_class_initializes(result)
    test_buttons_has_back_property(result, buttons)
    test_buttons_has_confirm_property(result, buttons)
    
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
