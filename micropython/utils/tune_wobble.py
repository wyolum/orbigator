
import machine
import time
from dynamixel_motor import DynamixelMotor
import dynamixel_extended_utils as dxl_utils

def run_tuning():
    print("="*40)
    print("AoV Motor Tuning: WOBBLE FIX (Slow Full Turns)")
    print("Testing 3 PID Profiles for stability...")
    print("Speed: 2 | Move: 360 degrees")
    print("="*40)

    # Setup
    uart = machine.UART(0, baudrate=57600, tx=machine.Pin(0), rx=machine.Pin(1))
    dir_pin = machine.Pin(2, machine.Pin.OUT)
    dxl_utils.uart = uart
    dxl_utils.dir_pin = dir_pin
    
    # Connect
    aov = DynamixelMotor(2, "AoV", gear_ratio=1.0)
    # Utility call for mode 4
    dxl_utils.set_extended_mode(2)
    aov.enable_torque()
    
    # Profiles: (P, D)
    profiles = [
        ("1. Baseline (Orbigator Default)", 600, 0),
        ("2. Damped (Medium D)", 600, 400),
        ("3. Heavy Load (High D)", 800, 800), # Very Stiff
        ("4. Soft & Damped", 400, 300)
    ]
    
    for name, p, d in profiles:
        print(f"\n>>> TESTING: {name}")
        print(f"    Setting P={p}, D={d}")
        aov.set_pid_gains(p=p, i=0, d=d)
        
        # Move Forward (Full Turn)
        print("    Moving +360 degrees (Full Turn)...")
        start_pos = aov.output_degrees
        target = start_pos + 360
        
        # CRITICAL: User requested Speed 2
        aov.set_speed_limit(2) 
        aov.set_angle_degrees(target)
        
        # Wait until arrival (or timeout)
        wait_for_arrival(aov, target)
        
        time.sleep(1)

        # Move Backward
        print("    Moving BACK (-360)...")
        aov.set_angle_degrees(start_pos)
        wait_for_arrival(aov, start_pos)
        
        time.sleep(2)
        
    print("\nTests Complete!")
    print("Which profile looked most stable?")
    print("Update orbigator.py with preferred values.")

def wait_for_arrival(motor, target_degrees, timeout_ms=300000):
    """Wait for motor to reach target with a long timeout for slow moves"""
    t0 = time.ticks_ms()
    last_print = 0
    
    while True:
        current = motor.get_angle_degrees()
        if current is None: continue
        
        diff = abs(target_degrees - current)
        
        # Print status every 2 seconds
        if time.ticks_diff(time.ticks_ms(), last_print) > 2000:
             print(f"      Pos: {current:.1f} / {target_degrees:.1f} (Diff: {diff:.1f})")
             last_print = time.ticks_ms()
             
        # "Close enough" threshold
        if diff < 2.0:
            print("      ✓ Arrived")
            break
            
        if time.ticks_diff(time.ticks_ms(), t0) > timeout_ms:
            print("      ⚠ Timeout waiting for move.")
            break
            
        time.sleep_ms(100)

if __name__ == "__main__":
    run_tuning()
