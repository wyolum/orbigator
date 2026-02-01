import machine
import time
from ds323x import DS323x
import pins

MAGIC_ADDR = 0x20

def test_persistence():
    print("--- SRAM Persistence Counter Test ---")
    i2c = machine.I2C(pins.I2C_ID, scl=machine.Pin(pins.I2C_SCL_PIN), sda=machine.Pin(pins.I2C_SDA_PIN))
    
    try:
        rtc = DS323x(i2c, 0x68, has_sram=True)
        
        # 1. Read current
        current = rtc.read_sram(MAGIC_ADDR, 1)
        val = current[0] if current else 0
        
        print(f"Current Value at 0x{MAGIC_ADDR:02X}: {val}")
        
        # 2. Increment
        new_val = (val + 1) % 256
        
        # 3. Write
        print(f"Writing New Value: {new_val}...")
        rtc.write_sram(MAGIC_ADDR, bytes([new_val]))
        
        # 4. Verify
        check = rtc.read_sram(MAGIC_ADDR, 1)
        if check and check[0] == new_val:
            print("Write Verified.")
            print("---------------------------------")
            print(f"Expected Next Run: {new_val}")
            print("(Unplug/Reboot now to test persistence)")
        else:
            print("Write FAILED!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_persistence()
