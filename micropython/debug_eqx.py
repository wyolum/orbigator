
from dynamixel_motor import DynamixelMotor
import dynamixel_extended_utils as utils
import time
import machine

EQX_ID = 1
EQX_GEAR_RATIO = 120.0 / 11.0 # From config roughly

print("Initializing EQX...")
try:
    # Minimal init
    motor = DynamixelMotor(EQX_ID, "EQX", gear_ratio=EQX_GEAR_RATIO)
    
    print(f"\nCurrent State:")
    print(f"  Motor Ticks: {utils.read_present_position(EQX_ID)}")
    print(f"  Motor Deg:   {motor.motor_degrees:.2f}")
    print(f"  Output Deg:  {motor.output_degrees:.2f}")
    
    # Test Scenarios
    targets = [0, 90, 180, 270, 360]
    print(f"\nSimulated Targets (Current Output: {motor.output_degrees:.2f}°):")
    
    for target in targets:
        next_pos = utils.get_new_pos(motor.output_degrees, target, direction=None)
        delta = next_pos - motor.output_degrees
        print(f"  Target {target:>3}° -> Next Pos {next_pos:>8.2f}° (Δ {delta:>6.2f}°)")
        
except Exception as e:
    print(f"Error: {e}")
