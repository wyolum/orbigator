"""
Verify integration of AbsoluteDynamixel with simulated hardware.
Simulates the startup logic of orbigator.py
"""
import sys
import os

# Add parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from absolute_motor import AbsoluteDynamixel, PersistentDrive

# Mocks
class MockRTC:
    def __init__(self):
        self.memory = bytearray(256) # 256 bytes SRAM
    
    def read_sram(self, addr, length):
        if addr + length > len(self.memory): return b'\x00'*length
        return self.memory[addr:addr+length]

    def write_sram(self, addr, data):
        end = addr + len(data)
        if end > len(self.memory): return
        self.memory[addr:end] = data

# Mock Micropython modules BEFORE imports
from unittest.mock import MagicMock
sys.modules['machine'] = MagicMock()
sys.modules['framebuf'] = MagicMock()
sys.modules['time'] = MagicMock()

import dynamixel_extended_utils
dynamixel_extended_utils.ping_motor = lambda id: True
# ... (rest of mocks)
dynamixel_extended_utils.reboot_motor = lambda id: None
dynamixel_extended_utils.set_extended_mode = lambda id: None
dynamixel_extended_utils.read_present_position = lambda id: 0 # Always at 0 initially
dynamixel_extended_utils.write_dword = lambda id, addr, val: None
dynamixel_extended_utils.write_byte = lambda id, addr, val: None

class TestIntegration(unittest.TestCase):
    def test_orbigator_startup(self):
        rtc = MockRTC()
        
        # AoV: Slot 1, Forward Only
        aov = AbsoluteDynamixel(2, rtc, gear_ratio=1.0, sram_slot=1, offset_degrees=0.0, direction=1)
        
        # Check defaults
        self.assertEqual(aov.drive.ticks, 0)
        self.assertEqual(aov.kinematics.gear_ratio, 1.0)
        
        # Move it
        aov.goto(180.0) # Should be 2048 ticks
        self.assertEqual(aov.drive.ticks, 2048)
        
        # EQX: Slot 0, Shortest Path
        eqx = AbsoluteDynamixel(1, rtc, gear_ratio=120/14.0, sram_slot=0, offset_degrees=0.0, direction=None)
        
        self.assertTrue(isinstance(eqx.drive, PersistentDrive))
        
        # Verify persistence is saving to "RTC"
        # Slot 0 starts at 0x80. RECORD_SIZE=16.
        # Check magic at 0x80
        magic = rtc.memory[0x80] | (rtc.memory[0x81] << 8)
        self.assertEqual(magic, PersistentDrive.STORAGE_MAGIC)

if __name__ == '__main__':
    unittest.main()
