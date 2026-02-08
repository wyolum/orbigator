"""
TDD Test: DS3232 Real-Time Clock
=================================
Non-destructive tests for DS3232 RTC with SRAM.
Saves original time/SRAM and restores after tests.

Run this test by copying to the Pico and running:
    import tests.test_ds3232 as t; t.run_tests()
"""

from machine import Pin, I2C
import time

# Pin assignments
I2C_SDA = 4
I2C_SCL = 5
DS3232_ADDR = 0x68

# Test SRAM location (use end of SRAM to avoid conflicts)
TEST_SRAM_ADDR = 0xF0
TEST_SRAM_LEN = 8


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


def test_ds3232_detected_on_i2c(result, i2c):
    """Test that DS3232 is detected at expected I2C address."""
    devices = i2c.scan()
    if DS3232_ADDR in devices:
        result.ok(f"DS3232 detected at 0x{DS3232_ADDR:02X}")
        return True
    else:
        result.fail("DS3232 detected on I2C", f"Found devices: {[hex(d) for d in devices]}")
        return False


def test_rtc_class_initializes(result, i2c):
    """Test that RTC class initializes correctly."""
    try:
        from rtc import RTC
        rtc = RTC(i2c)
        result.ok("RTC class initializes")
        return rtc
    except ImportError:
        result.fail("RTC class initializes", "rtc module not found")
        return None
    except Exception as e:
        result.fail("RTC class initializes", str(e))
        return None


def test_rtc_read_time(result, rtc):
    """Test that RTC can read current time."""
    if rtc is None:
        result.fail("RTC read time", "RTC not available")
        return None
    
    try:
        dt = rtc.datetime()
        if dt is None:
            result.fail("RTC read time", "datetime() returned None")
            return None
        if len(dt) == 8:
            year, month, day, weekday, hour, minute, second, _ = dt
            result.ok(f"RTC read time: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
            return dt
        else:
            result.fail("RTC read time", f"Expected 8-tuple, got {len(dt)}")
            return None
    except Exception as e:
        result.fail("RTC read time", str(e))
        return None


def test_rtc_write_time(result, rtc, original_dt, start_ticks):
    """Test that RTC can write time (restores original + elapsed)."""
    if rtc is None or original_dt is None:
        result.fail("RTC write time", "RTC or original time not available")
        return False
    
    try:
        # Calculate elapsed seconds since test start
        elapsed_ms = time.ticks_diff(time.ticks_ms(), start_ticks)
        elapsed_s = elapsed_ms // 1000
        
        # Add elapsed time to original datetime
        year, month, day, weekday, hour, minute, second, subsec = original_dt
        second += elapsed_s
        
        # Handle overflow (simple version - just seconds/minutes)
        while second >= 60:
            second -= 60
            minute += 1
        while minute >= 60:
            minute -= 60
            hour += 1
        while hour >= 24:
            hour -= 24
            # weekday and day would need more complex handling
        
        restored_dt = (year, month, day, weekday, hour, minute, second, subsec)
        rtc.datetime(restored_dt)
        
        # Verify by reading back
        verify_dt = rtc.datetime()
        if verify_dt is None:
            result.fail("RTC write time", "Read-back returned None")
            return False
        
        # Check that time was written (allow 1 second drift)
        if abs(verify_dt[6] - second) <= 1 or (second >= 59 and verify_dt[6] <= 1):
            result.ok(f"RTC write time (restored to +{elapsed_s}s)")
            return True
        else:
            result.fail("RTC write time", f"Write mismatch: wrote {second}s, read {verify_dt[6]}s")
            return False
    except Exception as e:
        result.fail("RTC write time", str(e))
        return False


def test_rtc_read_sram(result, rtc):
    """Test that RTC can read SRAM."""
    if rtc is None:
        result.fail("RTC read SRAM", "RTC not available")
        return None
    
    try:
        data = rtc.read_sram(TEST_SRAM_ADDR, TEST_SRAM_LEN)
        if data is None:
            result.fail("RTC read SRAM", "read_sram() returned None")
            return None
        if len(data) == TEST_SRAM_LEN:
            result.ok(f"RTC read SRAM ({TEST_SRAM_LEN} bytes from 0x{TEST_SRAM_ADDR:02X})")
            return bytes(data)  # Return copy for restore
        else:
            result.fail("RTC read SRAM", f"Expected {TEST_SRAM_LEN} bytes, got {len(data)}")
            return None
    except AttributeError:
        result.fail("RTC read SRAM", "read_sram method not found")
        return None
    except Exception as e:
        result.fail("RTC read SRAM", str(e))
        return None


def test_rtc_write_sram(result, rtc, original_sram):
    """Test that RTC can write SRAM (then restore original)."""
    if rtc is None:
        result.fail("RTC write SRAM", "RTC not available")
        return False
    
    try:
        # Write test pattern
        test_pattern = bytes([0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE])
        success = rtc.write_sram(TEST_SRAM_ADDR, test_pattern)
        if not success:
            result.fail("RTC write SRAM", "write_sram() returned False")
            return False
        
        # Verify by reading back
        verify = rtc.read_sram(TEST_SRAM_ADDR, TEST_SRAM_LEN)
        if verify is None or bytes(verify) != test_pattern:
            result.fail("RTC write SRAM", "Write verification failed")
            # Still try to restore
            if original_sram:
                rtc.write_sram(TEST_SRAM_ADDR, original_sram)
            return False
        
        # Restore original SRAM
        if original_sram:
            rtc.write_sram(TEST_SRAM_ADDR, original_sram)
            result.ok("RTC write SRAM (verified & restored)")
        else:
            result.ok("RTC write SRAM (verified, no restore needed)")
        return True
    except AttributeError:
        result.fail("RTC write SRAM", "write_sram method not found")
        return False
    except Exception as e:
        result.fail("RTC write SRAM", str(e))
        return False


def run_tests():
    """Run all DS3232 RTC tests (non-destructive)."""
    print("\n" + "="*40)
    print("DS3232 RTC TDD TESTS (Non-Destructive)")
    print("="*40 + "\n")
    
    result = TestResult()
    
    # Initialize I2C
    print("Setup:")
    try:
        i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)
        print(f"  ✓ I2C initialized")
    except Exception as e:
        print(f"  ✗ I2C init failed: {e}")
        return result
    
    # Record start time for elapsed calculation
    start_ticks = time.ticks_ms()
    
    # Detection test
    print("\nDetection:")
    if not test_ds3232_detected_on_i2c(result, i2c):
        print("\n" + "="*40)
        print("ABORTED: DS3232 not found on I2C bus")
        print("="*40 + "\n")
        return result
    
    # RTC class tests
    print("\nRTC Class:")
    rtc = test_rtc_class_initializes(result, i2c)
    
    # Time tests (save original first)
    print("\nTime Operations:")
    original_dt = test_rtc_read_time(result, rtc)
    
    # SRAM tests (save original first)
    print("\nSRAM Operations:")
    original_sram = test_rtc_read_sram(result, rtc)
    test_rtc_write_sram(result, rtc, original_sram)
    
    # Restore time at the end (after SRAM tests complete)
    print("\nCleanup:")
    test_rtc_write_time(result, rtc, original_dt, start_ticks)
    
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
