import unittest

# Mock DS323x for testing
class MockRTC:
    def __init__(self, size=236):
        self.memory = bytearray(size) # Start with 0x00
        self.sram_calls = []

    def write_sram(self, address, data):
        self.sram_calls.append(('write', address, data))
        # Simulate DS3232 0x14 start address offset logic if needed, 
        # but the driver usually handles the physical mapping.
        # Here we assume address is passed correctly by the driver user.
        # But wait, the real DS323x driver takes absolute address (0x14-0xFF).
        # So our mock should simulate that space.
        # Valid range in real HW: 0x14 to 0xFF.
        if address < 0x14 or address > 0xFF:
            return False # Fail
        
        offset = address - 0x14
        if offset + len(data) > len(self.memory):
            return False # Overflow
            
        for i, b in enumerate(data):
            self.memory[offset + i] = b
        return True

    def read_sram(self, address, length):
        self.sram_calls.append(('read', address, length))
        if address < 0x14 or address > 0xFF:
            return None
            
        offset = address - 0x14
        if offset + length > len(self.memory):
            return None
            
        return bytes(self.memory[offset:offset+length])

import sys
import os
# Add parent directory to path to find persistence.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from persistence import Persist, SRAM
except ImportError:
    # Allow test to run (and fail on specific tests) even if module missing
    Persist = None
    SRAM = None

class TestPersistence(unittest.TestCase):
    
    def test_import_exists(self):
        self.assertIsNotNone(Persist, "persistence.Persist module could not be imported")
        self.assertIsNotNone(SRAM, "persistence.SRAM class could not be imported")

    def test_sram_initialization(self):
        if not SRAM: return
        rtc = MockRTC()
        # Create SRAM partition starting at 0x14 with size 10
        sram = SRAM(rtc, base_address=0x14, size=10)
        self.assertEqual(sram._base, 0x14)
        self.assertEqual(sram._size, 10)
        self.assertEqual(sram.unique_id, "DS3232SRAM_20_10") # 0x14 is 20 decimal

    def test_sram_write_read(self):
        if not SRAM: return
        rtc = MockRTC()
        sram = SRAM(rtc, base_address=0x20, size=20) # Start at 32
        
        payload = b'\xAA\xBB\xCC'
        # Write at offset 0
        written = sram.write(0, payload)
        self.assertEqual(written, 3)
        
        # Read back
        read_data = sram.read(0, 3)
        self.assertEqual(read_data, payload)
        
        # Verify it went to correct physical address (0x20 = 32)
        # MockRTC stores relative to 0x14 (20). So 32-20 = 12.
        # Check mock memory directly
        self.assertEqual(rtc.memory[12:15], payload)

    def test_sram_write_offset(self):
        if not SRAM: return
        rtc = MockRTC()
        sram = SRAM(rtc, base_address=0x20, size=20)
        
        payload = b'\x11\x22'
        sram.write(5, payload)
        
        read_data = sram.read(5, 2)
        self.assertEqual(read_data, payload)
        
        # Should not have touched offset 0
        self.assertEqual(sram.read(0, 1), b'\x00')

    def test_sram_boundary_checks(self):
        if not SRAM: return
        rtc = MockRTC()
        sram = SRAM(rtc, base_address=0x20, size=5)
        
        # 1. Write exceeding size
        payload = b'\x01' * 6
        # Should raise ValueError or return 0/None? 
        # Pythonic convention for memory access often raises ValueError or IndexError.
        # Let's assume implementation raises ValueError for safety.
        with self.assertRaises(ValueError):
             sram.write(0, payload)
             
        # 2. Write valid size but wrong offset
        with self.assertRaises(ValueError):
            sram.write(4, b'\x01\x02') # 4+2=6 > 5
            
        # 3. Read exceeding size
        with self.assertRaises(ValueError):
            sram.read(0, 6)

if __name__ == '__main__':
    unittest.main()
