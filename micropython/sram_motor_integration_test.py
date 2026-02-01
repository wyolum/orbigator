import time
import machine
import json
import struct
import orb_utils as utils
from ds323x import DS323x
import pins
from dynamixel_motor import DynamixelMotor

# Initialize I2C and RTC
i2c = machine.I2C(pins.I2C_ID, scl=machine.Pin(pins.I2C_SCL_PIN), sda=machine.Pin(pins.I2C_SDA_PIN))
rtc = DS323x(i2c, 0x68, has_sram=True)
utils.g.rtc = rtc # Hack to let utils use it

print("\n--- SRAM vs MOTOR Isolation Test ---")

# 1. Read SRAM
print("Reading SRAM...")
saved_eqx = None
saved_ver = "?"
try:
    data = rtc.read_sram(rtc.SRAM_START, utils.STATE_SIZE)
    if data and data[:4] == utils.STATE_MAGIC:
        saved_ver = data[4]
        # Unpack based on version
        if saved_ver == 3: # V3 Double
            fmt = "<4sBIddddddIB16sB"
            if data[-1] == utils._compute_checksum(data):
                unpacked = struct.unpack(fmt, data)
                saved_eqx = unpacked[4] # Index 4 is EQX
                saved_ts = unpacked[2]
                print(f"SRAM (V3): EQX={saved_eqx} (TS={saved_ts})")
            else:
                print("SRAM (V3): Checksum Fail")
        elif saved_ver == 2: # V2 Float
            fmt = "<4sBIffffffIB16sB"
            # Note: utils.STATE_FORMAT is now V3, so we manually define V2 fmt
            if data[-1] == utils._compute_checksum(data):
                unpacked = struct.unpack(fmt, data)
                saved_eqx = unpacked[4]
                print(f"SRAM (V2): EQX={saved_eqx} (FLOAT32)")
            else:
                print("SRAM (V2): Checksum Fail")
        else:
             print(f"SRAM: Unknown Version {saved_ver}")
    else:
        print("SRAM: No Valid Magic Header (Empty/Corrupt)")
except Exception as e:
    print(f"SRAM Read Error: {e}")

# 2. Read Motor
print("Reading EQX Motor (ID 1)...")
# Load config for gear ratio
gear_ratio = 1.0
try:
    with open("orbigator_config.json", "r") as f:
        config = json.load(f)
        motor_data = config.get("motors", {}).get("eqx", {})
        num = motor_data.get("gear_ratio_num", 1.0)
        den = motor_data.get("gear_ratio_den", 1.0)
        gear_ratio = num / den
    print(f"Loaded Gear Ratio: {gear_ratio:.4f} ({num}/{den})")
except Exception as e:
    print(f"Config Load Error: {e} (Using 1.0)")

# Initialize Motor HARDWARE first (Reboot -> Mode)
print("Initializing Motor Hardware...")
try:
    from dynamixel_extended_utils import reboot_motor, set_extended_mode
    
    # Reboot simulates power loss - motor loses multi-turn position
    if reboot_motor(1):
        print("  Reboot OK (simulates power loss)")
    else:
        print("  Reboot Failed")
        
    time.sleep(0.5)

    # Set Extended Position Control Mode (4)
    if set_extended_mode(1):
        print("  Mode 4 (Extended Position) OK")
    else:
        print("  Mode Set Failed")

except ImportError:
    print("  WARNING: dynamixel_extended_utils not found.")

time.sleep(0.5)

# NOW create motor with saved position - this triggers restoration
uart = machine.UART(pins.DYNAMIXEL_UART_ID, baudrate=57600, tx=machine.Pin(pins.DYNAMIXEL_TX_PIN), rx=machine.Pin(pins.DYNAMIXEL_RX_PIN))
print(f"Creating motor with last_known_pos={saved_eqx}")
motor = DynamixelMotor(1, uart, gear_ratio=gear_ratio, last_known_pos=saved_eqx)

# Enable Torque
if motor.enable_torque():
    print("  Torque Enabled OK")
else:
    print("  Torque Enable Failed")

# Safety Speed Limit
print("Setting safe speed limit (20)...")
motor.set_speed_limit(20)

time.sleep(0.5)

# Read the restored position values directly (don't re-read from hardware yet)
print(f"\nRestored State:")
print(f"  Motor Shaft: {motor.motor_degrees:.2f}°")
print(f"  Offset: {motor.offset_degrees:.4f}°")
print(f"  Output: {motor.output_degrees:.2f}°")

actual_deg = motor.output_degrees

# 3. Move to Constant Target
TEST_TARGET = 180.0
print(f"\n--- Moving to Constant Target: {TEST_TARGET}° ---")

print(f"Current Motor Pos: {actual_deg:.4f}")
diff = TEST_TARGET - actual_deg
print(f"Required Move: {diff:.4f}°")

print(f"Moving Motor to {TEST_TARGET:.4f}...")
motor.set_nearest_degrees(TEST_TARGET % 360) 

# Wait for move to complete (no timeout - wait for stabilization)
print("Waiting for move to complete...")
last_pos = -999.0
steady_count = 0
check_interval = 0.5
max_iterations = 200  # Safety limit: 100 seconds max

for i in range(max_iterations):
    motor.update_present_position(force=True)
    curr = motor.get_angle_degrees()
    
    if curr is not None:
        print(f"  Pos: {curr:.2f}°")
        if abs(curr - last_pos) < 0.1:
            steady_count += 1
        else:
            steady_count = 0
        
        last_pos = curr
        
        if steady_count >= 6: # Steady for 3.0 seconds
            print("Motor Stabilized.")
            break
            
    time.sleep(check_interval)

# Verify
motor.update_present_position(force=True)
new_deg = motor.get_angle_degrees()
print(f"New Motor Pos: {new_deg:.4f}")

if abs(new_deg - TEST_TARGET) < 1.0: 
     print("Motor Arrived.")
     
     # Write to SRAM
     # Re-reading data to be safe
     try:
         full_data = bytearray(rtc.read_sram(rtc.SRAM_START, utils.STATE_SIZE))
         # Modify double at offset 17 (EQX)
         struct.pack_into("<d", full_data, 17, float(new_deg))
         # Recalculate Checksum
         full_data[-1] = utils._compute_checksum(full_data)
         
         print(f"Writing {new_deg:.4f} to SRAM...")
         if rtc.write_sram(rtc.SRAM_START, full_data):
             print("SRAM Updated.")
         else:
             print("SRAM Write Failed.")
     except Exception as e:
         print(f"SRAM Write Error: {e}")

else:
     print("Motor Move Failed to Reach Target.")
