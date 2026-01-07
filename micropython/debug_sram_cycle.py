
import sys
sys.path.append(".")
import time
import struct
import machine
from machine import I2C, Pin
import ds323x
import pins

print("Initializing I2C...")
i2c = I2C(0, scl=Pin(pins.I2C_SCL_PIN), sda=Pin(pins.I2C_SDA_PIN), freq=400000)

SRAM_START = 0x14

# Define format matching orb_utils
STATE_FORMAT = "<4sBIffffffIB16sB"
STATE_MAGIC = b"ORB2"
STATE_VERSION = 2

def compute_checksum(data):
    return sum(data[:-1]) & 0xFF

def run_test():
    try:
        rtc = ds323x.DS323x(i2c, 0x68, has_sram=True)
        print("RTC Connected.")
        
        # Create Dummy Data
        ts = int(time.time())
        aov = 10.5
        eqx = -45.2
        alt = 420.0
        inc = 51.6
        ecc = 0.001
        peri = 90.0
        rev = 123
        mode = 0 # Orbit
        sat_name = b"ISS" + b"\0"*13 # Pad to 16
        
        print("Packing data...")
        # Pack without checksum (last byte 0)
        data = bytearray(struct.pack(STATE_FORMAT,
            STATE_MAGIC, STATE_VERSION,
            ts, aov, eqx, alt, inc, ecc, peri, rev, mode, sat_name, 0
        ))
        
        # Calculate Checksum
        chk = compute_checksum(data)
        data[-1] = chk
        print(f"Data size: {len(data)} bytes. Checksum: {chk}")
        
        # Write
        print(f"Writing to {hex(SRAM_START)}...")
        if rtc.write_sram(SRAM_START, data):
            print("Write OK.")
        else:
            print("Write FAILED.")
            return

        # Read Back
        print("Reading back...")
        read_data = rtc.read_sram(SRAM_START, len(data))
        
        if not read_data:
            print("Read FAILED (None).")
            return
            
        print(f"Read {len(read_data)} bytes.")
        
        # Validate logic
        if read_data[:4] != STATE_MAGIC:
            print(f"Magic Mismatch! Got {read_data[:4]}")
        else:
            print("Magic OK.")
            
        if read_data[-1] != compute_checksum(read_data):
            print(f"Checksum Mismatch! Got {read_data[-1]}, Calc {compute_checksum(read_data)}")
        else:
            print("Checksum OK.")
            
        # Unpack
        try:
             mag, ver, r_ts, r_aov, r_eqx, r_alt, r_inc, r_ecc, r_peri, r_rev, r_mid, r_sat, r_ck = struct.unpack(STATE_FORMAT, read_data)
             print(f"Unpacked: AoV={r_aov:.1f}, EQX={r_eqx:.1f}, Rev={r_rev}")
             if abs(r_aov - aov) < 0.1:
                 print("Data Matches!")
             else:
                 print("Data Mismatch!")
        except Exception as e:
            print(f"Unpack error: {e}")

    except Exception as e:
        print(f"Test Exception: {e}")

run_test()
