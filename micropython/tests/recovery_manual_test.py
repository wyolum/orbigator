"""
Manual Verification of EQX Recovery
===================================
1. Move EQX to a multi-turn position.
2. Ensure checkpoint is saved to RTC SRAM.
3. Re-initialize DynamixelMotor and verify it recovers the position.
"""

from machine import Pin, I2C
import time
from dynamixel_motor import DynamixelMotor
from rtc import RTC
from oled_display import OledDisplay

def run_test():
    print("\nEQX Recovery Manual Test")
    print("========================")
    
    # Init hardware
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
    rtc = RTC(i2c)
    display = OledDisplay(i2c)
    
    # EQX Gear Ratio
    EQX_GEAR_RATIO = 120.0 / 14.0
    
    # 1. First init - should read current hardware state
    print("\nSTEP 1: Initializing motor...")
    eqx = DynamixelMotor(1, "EQX", gear_ratio=EQX_GEAR_RATIO, rtc=rtc)
    start_pos = eqx.output_degrees
    print(f"Current Position: {start_pos:.1f}°")
    
    # 2. Move to a new position to trigger multiple checkpoints (720° = ~17 motor revs)
    target = start_pos + 720.0
    print(f"\nSTEP 2: Moving to {target:.1f}° to trigger multiple checkpoints...")
    eqx.enable_torque()
    eqx.set_speed(70) # Slightly faster
    eqx.set_position(target)
    
    # Wait for arrival
    for i in range(120): # 60 seconds
        pos = eqx.update_position()
        if i % 10 == 0:
            print(f"  Traveling... {pos:.1f}° / {target:.1f}°")
        if abs(pos - target) < 1.0:
            print(f"Arrived at {pos:.1f}°")
            break
        time.sleep(0.5)
    
    print("Verifying checkpoint in SRAM...")
    data = rtc.read_sram(0x14, 14)
    if data:
        import struct
        timestamp, magic, saved_ticks, gear_phase = struct.unpack("<IHif", data)
        print(f"SRAM Checkpoint: T={timestamp}, Ticks={saved_ticks}, Gear Phase={gear_phase:.1f}")
    else:
        print("FAILED: No SRAM data found!")
        return

    # 3. Simulate "reboot" by deleting object and re-creating
    print("\nSTEP 3: Simulating reboot (re-initializing motor object)...")
    
    # Disable torque to stop movement for accurate comparison
    eqx.disable_torque()
    time.sleep(1) # Let it settle
    eqx.update_position()
    last_pos_before_reboot = eqx.output_degrees
    
    del eqx
    time.sleep(1)
    
    # Re-init should trigger recovery from SRAM
    eqx_recovered = DynamixelMotor(1, "EQX", gear_ratio=EQX_GEAR_RATIO, rtc=rtc)
    recovered_pos = eqx_recovered.output_degrees
    
    print(f"\nRESULTS:")
    print(f"  Position before reboot: {last_pos_before_reboot:.1f}°")
    print(f"  Position after reboot: {recovered_pos:.1f}°")
    
    error = abs(recovered_pos - last_pos_before_reboot)
    if error < 2.0:
        print("\n✓ SUCCESS: EQX Position successfully recovered from RTC SRAM!")
    else:
        print(f"\n✗ FAILURE: Position mismatch! Error: {error:.1f}°")

if __name__ == "__main__":
    run_test()
