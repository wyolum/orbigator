
import time
from machine import I2C, Pin
import ds323x

# Initialize I2C (match orbigator.py pins)
# Assuming Pico 2W pins: SDA=0, SCL=1 or different?
# I need to check pins.py to be sure.
import pins

print("Initializing I2C...")
i2c = I2C(0, scl=Pin(pins.I2C_SCL_PIN), sda=Pin(pins.I2C_SDA_PIN), freq=400000)

print("Scanning I2C...")
devs = i2c.scan()
print("Devices found:", [hex(x) for x in devs])

if 0x68 not in devs:
    print("Error: DS3232 (0x68) not found!")
else:
    print("Found 0x68. Testing SRAM...")
    try:
        rtc = ds323x.DS323x(i2c, 0x68, has_sram=True)
        
        # Test Pattern
        addr = rtc.SRAM_START
        test_byte = 0x77
        
        print(f"Writing {hex(test_byte)} to SRAM addr {hex(addr)}...")
        rtc.write_sram(addr, bytes([test_byte]))
        
        print("Reading back...")
        check = rtc.read_sram(addr, 1)
        
        if check and check[0] == test_byte:
            print("SUCCESS: SRAM Read/Write verified!")
        else:
            print(f"FAILURE: Read {check} (Expected {hex(test_byte)})")
            
    except Exception as e:
        print(f"Test Exception: {e}")
