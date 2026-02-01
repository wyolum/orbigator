import machine
from ds323x import DS323x
import time

I2C_ADDR = 0x68
SRAM_TEST_ADDR = 0xFF # Test the very last byte to avoid collision with State struct at 0x14

def test_sram():
    print("Initializing I2C...")
    # Matches pins.py (SDA=4, SCL=5)
    i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
    
    print(f"Scanning I2C... Found: {[hex(x) for x in i2c.scan()]}")
    
    rtc = DS323x(i2c, I2C_ADDR, has_sram=True)
    
    print(f"Testing SRAM at address 0x{SRAM_TEST_ADDR:02X}...")
    
    try:
        # 1. Backup
        original = rtc.read_sram(SRAM_TEST_ADDR, 1)
        if original is None:
            print("FAIL: Read returned None")
            return
        
        print(f"Original value: 0x{original[0]:02X}")
        
        # 2. Write 0x55
        print("Writing 0x55...")
        if not rtc.write_sram(SRAM_TEST_ADDR, b'\x55'):
            print("FAIL: Write Error")
            return
            
        read1 = rtc.read_sram(SRAM_TEST_ADDR, 1)
        if read1[0] != 0x55:
            print(f"FAIL: Expected 0x55, got 0x{read1[0]:02X}")
            # Try to restore anyway
        else:
            print("PASS: 0x55 verified.")
            
        # 3. Write 0xAA
        print("Writing 0xAA...")
        if not rtc.write_sram(SRAM_TEST_ADDR, b'\xAA'):
            print("FAIL: Write Error")
            return
            
        read2 = rtc.read_sram(SRAM_TEST_ADDR, 1)
        if read2[0] != 0xAA:
            print(f"FAIL: Expected 0xAA, got 0x{read2[0]:02X}")
        else:
            print("PASS: 0xAA verified.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        
    finally:
        # 4. Restore
        print(f"Restoring original value 0x{original[0]:02X}...")
        rtc.write_sram(SRAM_TEST_ADDR, original)
        final_read = rtc.read_sram(SRAM_TEST_ADDR, 1)
        if final_read and final_read[0] == original[0]:
            print("Restoration Verified.")
        else:
            print("Restoration FAILED!")

if __name__ == "__main__":
    test_sram()
