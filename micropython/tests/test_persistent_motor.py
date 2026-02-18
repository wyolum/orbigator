import unittest
import struct
import sys
import os
import time

# Add parent directory to path to find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from persistence import Persist
    from absolute_motor import PersistentDrive, AxisKinematics
except ImportError:
    # Use mocks if modules not available
    Persist = object
    PersistentDrive = None
    AxisKinematics = None

class MockPersist(Persist):
    def __init__(self):
        self.data = bytearray()
        
    def read(self, offset, length):
        if offset + length > len(self.data):
            return None
        return self.data[offset:offset+length]
        
    def write(self, offset, payload):
        end = offset + len(payload)
        if end > len(self.data):
             self.data.extend(b'\x00' * (end - len(self.data)))
        self.data[offset:end] = payload
        return len(payload)

class TestPersistentDrive(unittest.TestCase):
    
    def setUp(self):
        if not PersistentDrive: self.skipTest("Module not found")
        self.persist = MockPersist()

    def test_init_cold_boot(self):
        """Test initialization with empty persistence."""
        drive = PersistentDrive(self.persist, identity_hash=0xDEADBEEF)
        
        # Should initialize to 0
        self.assertEqual(drive.ticks, 0)
        
        # Should have saved initial state
        # Magic(H) + Ver(H) + Ticks(i) + Hash(I) + Res(I) = 16 bytes
        self.assertEqual(len(self.persist.data), 16)
        
        # Check magic
        magic = struct.unpack("<H", self.persist.data[:2])[0]
        self.assertEqual(magic, 0x5044)

    def test_restore_state(self):
        """Test restoring valid state."""
        drive = PersistentDrive(self.persist, identity_hash=0x1234)
        drive.set_ticks(50000)
        # Force save (hack private method or trigger logic)
        drive._save_state()
        
        # New instance
        drive2 = PersistentDrive(self.persist, identity_hash=0x1234)
        self.assertEqual(drive2.ticks, 50000)

    def test_identity_mismatch(self):
        """Test reset on identity hash mismatch."""
        drive = PersistentDrive(self.persist, identity_hash=0x1111)
        drive.set_ticks(9999)
        drive._save_state()
        
        # New instance with different hash (e.g. gear ratio changed)
        drive2 = PersistentDrive(self.persist, identity_hash=0x2222)
        
        # Should NOT restore 9999, should reset to 0
        self.assertEqual(drive2.ticks, 0)

    def test_dual_checkpoint_triggers(self):
        """Test time and distance triggers."""
        drive = PersistentDrive(self.persist)
        
        # 1. Small move, no time passed -> No Save
        drive.set_ticks(10) # < 100 threshold
        # Inspect raw data (should still be 0 if only init saved)
        # Actually init saved 0. 
        # But we need to know if it saved 10.
        # We can check internal _last_saved_ticks
        self.assertEqual(drive._last_saved_ticks, 0)
        
        # 2. Large move -> Save
        drive.set_ticks(200) # > 100 delta
        self.assertEqual(drive._last_saved_ticks, 200)
        
        # 3. Time trigger
        drive.set_ticks(250) # Small delta
        self.assertEqual(drive._last_saved_ticks, 200) # Not saved yet
        
        # Mock time passage
        drive._last_saved_time -= 400 # 400s > 300s limit
        drive._check_checkpoint()
        self.assertEqual(drive._last_saved_ticks, 250) # Saved due to time

class TestAxisKinematics(unittest.TestCase):
    
    def test_ratios(self):
        if not AxisKinematics: self.skipTest("Module not found")
        
        # 1:1, 4096 TPR
        k = AxisKinematics(gear_ratio=1.0)
        self.assertAlmostEqual(k.ticks_to_degrees(4096), 360.0)
        self.assertEqual(k.degrees_to_ticks(180.0), 2048)
        
        # 10:1 reduction (10 motor turns = 1 output turn)
        # Ticks per DEGREE = (4096 * 10) / 360 = 113.77
        k10 = AxisKinematics(gear_ratio=10.0)
        self.assertAlmostEqual(k10.ticks_to_degrees(40960), 360.0)
        self.assertEqual(k10.degrees_to_ticks(36.0), 4096)

    def test_offsets(self):
        k = AxisKinematics()
        # Physical 0 = Logical 10
        k.offset_degrees = 10.0
        
        self.assertAlmostEqual(k.ticks_to_degrees(0), 10.0)
        
        # To get Logical 10, go to Physical 0
        self.assertEqual(k.degrees_to_ticks(10.0), 0)
        
        # To get Logical 370 (one turn + 10), go to Physical 4096
        self.assertEqual(k.degrees_to_ticks(370.0), 4096)

    def test_calc_offset(self):
        k = AxisKinematics()
        # Current Phys: 0 ticks. We want it to mean 90 degrees.
        offset = k.calculate_offset(0, 90.0)
        self.assertEqual(offset, 90.0)
        
        k.offset_degrees = offset
        self.assertAlmostEqual(k.ticks_to_degrees(0), 90.0)

if __name__ == '__main__':
    unittest.main()
