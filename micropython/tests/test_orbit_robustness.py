"""
Orbit Robustness Test
======================
Runs BOTH EQX and AoV motors simultaneously to test mechanical 
robustness (e.g., checking for binding after shimming gears).

Tracks progress on OLED like eqx_track_test.py.
EQX rotates continuously while AoV sweeps back and forth.

Run: import tests.test_orbit_robustness as t; t.run_test()
"""

from machine import Pin, I2C  
import time
import json

from oled_display import OledDisplay
from dynamixel_extended_utils import (
    read_present_position, write_dword, write_byte, set_extended_mode
)

# Hardware
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
display = OledDisplay(i2c)

# Load config
try:
    with open("orbigator_config.json", "r") as f:
        config = json.load(f)
    EQX_ID = config["motors"]["eqx"]["id"]
    GEAR_NUM = config["motors"]["eqx"]["gear_ratio_num"]
    GEAR_DEN = config["motors"]["eqx"]["gear_ratio_den"]
    # Strictly adhere to config speed limit
    EQX_SPEED = config["motors"]["eqx"]["speed_limit"]
    
    AOV_ID = config["motors"]["aov"]["id"]
    # Strictly adhere to config speed limit
    AOV_SPEED = config["motors"]["aov"]["speed_limit"]
    
except Exception as e:
    print(f"Config error: {e}, using defaults")
    EQX_ID = 1
    GEAR_NUM = 120.0
    GEAR_DEN = 14.0
    EQX_SPEED = 50
    AOV_ID = 2
    AOV_SPEED = 20

GEAR_RATIO = GEAR_NUM / GEAR_DEN  # ~8.57
TICKS_PER_REV = 4096

def ticks_to_motor_degrees(ticks):
    return (ticks / TICKS_PER_REV) * 360.0

def ticks_to_eqx_degrees(ticks):
    return ticks_to_motor_degrees(ticks) / GEAR_RATIO

def motor_degrees_to_ticks(degrees):
    return int((degrees / 360.0) * TICKS_PER_REV)

def run_test(orbits_to_test=1000):
    """
    Run robustness test indefinitely (default 1000 EQX orbits).
    AoV will continuously sweep between +720 and -720 degrees.
    """
    print("\n" + "="*50)
    print("ORBIT ROBUSTNESS TEST")
    print("Target: Running continuously (Ctrl+C to stop).")
    print("="*50)
    
    # Initialize motors
    print("\nInitializing motors...")
    for motor_id, speed in [(EQX_ID, EQX_SPEED), (AOV_ID, AOV_SPEED)]:
        set_extended_mode(motor_id)
        write_byte(motor_id, 64, 1)  # Enable torque
        write_dword(motor_id, 112, speed)  # Set speed
        
    # Read starting positions
    start_eqx_ticks = read_present_position(EQX_ID)
    start_aov_ticks = read_present_position(AOV_ID)
    
    if start_eqx_ticks is None or start_aov_ticks is None:
        print("ERROR: Cannot read motor positions! Check connections.")
        return
        
    start_eqx_deg = ticks_to_eqx_degrees(start_eqx_ticks)
    start_aov_deg = ticks_to_motor_degrees(start_aov_ticks)
    
    print(f"Start EQX: {start_eqx_ticks} ticks ({start_eqx_deg:.2f}°)")
    print(f"Start AoV: {start_aov_ticks} ticks ({start_aov_deg:.2f}°)")
    
    # Target EQX = multiple orbits in the negative direction
    eqx_orbit_degrees = -360.0 * orbits_to_test
    target_eqx_ticks = start_eqx_ticks + motor_degrees_to_ticks(eqx_orbit_degrees * GEAR_RATIO)
    
    # AoV Sweep logic
    aov_sweep_limit = 720.0 # 2x 360 degrees
    aov_target_deg = start_aov_deg + aov_sweep_limit
    aov_target_ticks = start_aov_ticks + motor_degrees_to_ticks(aov_sweep_limit)
    aov_direction = 1 # 1 for positive sweep, -1 for negative sweep
    
    print(f"\nCommanding EQX to run continuously...")
    print(f"Commanding AoV to sweep between +/- {aov_sweep_limit}°...")
    
    # Initial display
    display.clear()
    display.text("ROBUSTNESS TEST", 0, 0)
    display.text("Starting...", 0, 20)
    display.show()
    time.sleep(1)
    
    # Start motions
    write_dword(EQX_ID, 116, target_eqx_ticks)
    write_dword(AOV_ID, 116, aov_target_ticks)
    
    last_update_time = time.ticks_ms()
    eqx_orbits_completed = 0
    aov_sweeps_completed = 0
    
    zero_eqx_ticks = start_eqx_ticks
    
    try:
        while True:
            eqx_pos = read_present_position(EQX_ID)
            aov_pos = read_present_position(AOV_ID)
            
            if eqx_pos is None or aov_pos is None:
                continue
                
            # Calculate EQX progress
            delta_eqx_ticks = eqx_pos - zero_eqx_ticks
            eqx_degrees = ticks_to_eqx_degrees(delta_eqx_ticks)
            current_eqx_orbits = int(abs(eqx_degrees) / 360.0)
            
            # Calculate AOV progress
            aov_current_deg = ticks_to_motor_degrees(aov_pos) - start_aov_deg
            
            # Have we completed an EQX orbit?
            if current_eqx_orbits > eqx_orbits_completed:
                eqx_orbits_completed = current_eqx_orbits
                print(f"✓ EQX completed orbit {eqx_orbits_completed}")
                
            # Test if AOV reached its sweep target
            aov_error = abs(aov_pos - aov_target_ticks)
            if aov_error < 50:  # within ~4 degrees
                aov_sweeps_completed += 1
                # Reverse direction for AoV
                aov_direction *= -1
                aov_target_deg = start_aov_deg + (aov_sweep_limit * aov_direction)
                aov_target_ticks = start_aov_ticks + motor_degrees_to_ticks(aov_sweep_limit * aov_direction)
                write_dword(AOV_ID, 116, aov_target_ticks)
                print(f"AoV reversing... (Completed {aov_sweeps_completed} sweeps)")
            
            # Update display periodically
            now = time.ticks_ms()
            if time.ticks_diff(now, last_update_time) > 200:
                last_update_time = now
                
                display.clear()
                display.text("ROBUSTNESS TEST", 4, 0)
                display.text("-" * 16, 0, 12)
                display.text(f"EQX Orbit: {eqx_orbits_completed}", 0, 24)
                display.text(f"EQX Deg: {eqx_degrees:.1f}", 0, 40)
                display.text(f"AoV Deg: {aov_current_deg:.1f}", 0, 56)
                display.show()
                
            time.sleep_ms(50)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user. Stopping motors.")
        
    # Stop motors (send current position as goal to hold)
    for mid in (EQX_ID, AOV_ID):
        pos = read_present_position(mid)
        if pos is not None:
            write_dword(mid, 116, pos)
            
    # Final display
    display.clear()
    display.text("TEST FINISHED", 12, 0)
    display.text(f"Orbits: {eqx_orbits_completed}", 0, 24)
    display.text(f"Sweeps: {aov_sweeps_completed}", 0, 40)
    display.show()

if __name__ == "__main__":
    run_test()
