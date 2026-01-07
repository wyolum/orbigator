
import machine
import time
from dynamixel_motor import DynamixelMotor
import dynamixel_extended_utils as dxl_utils

def run_tuning():
    print("="*40)
    print("AoV Motor Tuning: WOBBLE FIX")
    print("Testing 3 PID Profiles for stability...")
    print("="*40)

    # Setup
    uart = machine.UART(0, baudrate=57600, tx=machine.Pin(0), rx=machine.Pin(1))
    dir_pin = machine.Pin(2, machine.Pin.OUT)
    dxl_utils.uart = uart
    dxl_utils.dir_pin = dir_pin
    
    # Connect
    aov = DynamixelMotor(2, "AoV", gear_ratio=1.0)
    # aov.set_extended_mode() does not exist on the object
    # Call the utility directly
    dxl_utils.set_extended_mode(2)
    aov.enable_torque()
    
    # Profiles: (P, D)
    # D-gain acts as a damper (brake) for oscillation (wobble).
    profiles = [
        ("1. Baseline (Orbigator Default)", 600, 0),
        ("2. Damped (Medium D)", 600, 400),
        ("3. Heavy Load (High D)", 800, 800), # Increased P for holding, High D for anti-wobble
        ("4. Soft & Damped (Low P, Med D)", 400, 300)
    ]
    
    for name, p, d in profiles:
        print(f"\n>>> TESTING: {name}")
        print(f"    Setting P={p}, D={d}")
        aov.set_pid_gains(p=p, i=0, d=d)
        
        print("    Moving +30 degrees...")
        start_pos = aov.output_degrees
        target = start_pos + 30
        aov.set_speed_limit(10) # Fast enough to excite wobble
        aov.set_angle_degrees(target)
        
        # Monitor for 5 seconds
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < 5000:
             time.sleep_ms(100)
             
        print("    Moving BACK...")
        aov.set_angle_degrees(start_pos)
        time.sleep(3)
        
    print("\nTests Complete!")
    print("Which profile looked most stable?")
    print("Update orbigator.py with preferred values.")

if __name__ == "__main__":
    run_tuning()
