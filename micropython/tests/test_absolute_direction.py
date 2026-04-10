import sys
import os

# Add parent directory to path to import absolute_motor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from absolute_motor import AbsoluteDynamixel
from absolute_motor import PersistentDrive
from absolute_motor import AxisKinematics

# Mock backend for persistence
# Mock backend for persistence
class MockSRAM:
    def __init__(self, rtc, base, size):
        pass
    def write(self, addr, data):
        pass
    def read(self, addr, size):
        return None

class MockPersistence:
    SRAM = MockSRAM

sys.modules['persistence'] = MockPersistence

# Mock AbsoluteDynamixel hardware calls
def mock_init_hardware(self):
    self._hw_offset = 0

def mock_recover_position(self):
    self._hw_offset = 0
    self.drive.set_ticks(0)

def mock_command(self, target_ticks):
    self.drive.set_ticks(target_ticks)

def mock_update(self):
    raw = self.drive.ticks - self._hw_offset
    true_ticks = raw + self._hw_offset
    self.drive.set_ticks(true_ticks)
    return self.kinematics.ticks_to_degrees(self.drive.ticks)

# Apply mocks
AbsoluteDynamixel._init_hardware = mock_init_hardware
AbsoluteDynamixel._recover_position = mock_recover_position
AbsoluteDynamixel._command = mock_command
AbsoluteDynamixel.update = mock_update


def test_absolute_direction():
    print("Testing AbsoluteDynamixel direction policy...")
    
    rtc = None
    
    # 1. Forward Only (direction=1)
    print("\n--- Testing FORWARD ONLY (direction=1) ---")
    motor_fwd = AbsoluteDynamixel(1, rtc, gear_ratio=1.0, direction=1)
    motor_fwd.drive.persist = MockSRAM(None, 0, 0)
    
    # Move to exactly 10 deg absolute
    motor_fwd.goto(10.0)
    print(f"Current Pos: {motor_fwd.position_deg}")
    
    # Target 340 starting from 10 is backwards 30 degrees.
    # 30 degrees is outside the 20.0 deadband, so it will move full +330 to 340.0.
    motor_fwd.mod_goto(340.0)
    print(f"Target 340 -> Result: {motor_fwd.position_deg}")
    assert abs(motor_fwd.position_deg - 340.0) < 0.1, f"Expected 340.0, got {motor_fwd.position_deg}"
    
    # Target 330.0 starting from 340.0 is backwards 10.0 degrees.
    # This is inside the deadband, so it should NOT move.
    motor_fwd.mod_goto(330.0)
    print(f"Target 330.0 -> Result: {motor_fwd.position_deg}")
    assert abs(motor_fwd.position_deg - 340.0) < 0.1, f"Expected 340.0 (deadbanded), got {motor_fwd.position_deg}"
    
    # Target 10. Since Forward, should move +20 to 360, plus 10 = 370.0
    motor_fwd.mod_goto(10.0)
    print(f"Target 10  -> Result: {motor_fwd.position_deg}")
    assert abs(motor_fwd.position_deg - 370.0) < 0.1, f"Expected 370.0, got {motor_fwd.position_deg}"

    # 2. Reverse Only (direction=-1)
    print("\n--- Testing REVERSE ONLY (direction=-1) ---")
    motor_rev = AbsoluteDynamixel(2, rtc, gear_ratio=1.0, direction=-1)
    motor_rev.drive.persist = MockSRAM(None, 0, 0)
    
    # Move to exactly 350 deg absolute
    motor_rev.goto(350.0)
    print(f"Current Pos: {motor_rev.position_deg}")
    
    # Target 10. Since Reverse, should move -340 to 10.0
    motor_rev.mod_goto(10.0)
    print(f"Target 10  -> Result: {motor_rev.position_deg}")
    assert abs(motor_rev.position_deg - 10.0) < 0.1, f"Expected 10.0, got {motor_rev.position_deg}"
    
    # Target 350. Since Reverse, should move -20 to -10.0
    motor_rev.mod_goto(350.0)
    print(f"Target 350 -> Result: {motor_rev.position_deg}")
    assert abs(motor_rev.position_deg - -10.0) < 0.1, f"Expected -10.0, got {motor_rev.position_deg}"

    # 3. Shortest Path (direction=None)
    print("\n--- Testing SHORTEST PATH (direction=None) ---")
    motor_short = AbsoluteDynamixel(3, rtc, gear_ratio=1.0, direction=None)
    motor_short.drive.persist = MockSRAM(None, 0, 0)
    
    motor_short.goto(350.0)
    print(f"Current Pos: {motor_short.position_deg}")
    
    # Target 10. Shortest path is +20, so 370.0
    motor_short.mod_goto(10.0)
    print(f"Target 10  -> Result: {motor_short.position_deg}")
    assert abs(motor_short.position_deg - 370.0) < 0.1, f"Expected 370.0, got {motor_short.position_deg}"

    # Target 350. Shortest path is -20, so 350.0
    motor_short.mod_goto(350.0)
    print(f"Target 350 -> Result: {motor_short.position_deg}")
    assert abs(motor_short.position_deg - 350.0) < 0.1, f"Expected 350.0, got {motor_short.position_deg}"

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    test_absolute_direction()
