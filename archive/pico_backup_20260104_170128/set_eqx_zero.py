
import machine
import json
import time
from dynamixel_motor import DynamixelMotor
import dynamixel_extended_utils as dxl_utils

def set_zero():
    print("="*40)
    print("      EQX RING ZEROING TOOL")
    print("="*40)
    
    # Load Config to get ID/Ratio
    try:
        with open("orbigator_config.json", "r") as f:
            config = json.load(f)
        eqx_conf = config["motors"]["eqx"]
        m_id = eqx_conf["id"]
        ratio = eqx_conf["gear_ratio_num"] / eqx_conf["gear_ratio_den"]
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # Setup UART
    uart = machine.UART(0, baudrate=57600, tx=machine.Pin(0), rx=machine.Pin(1))
    dxl_utils.uart = uart
    dxl_utils.dir_pin = machine.Pin(2, machine.Pin.OUT)
    
    # Connect (using 0 offset initially to read RAW)
    # We want raw motor degrees to calculate new offset.
    # DynamixelMotor calculates: Output = (Motor/Ratio) - Offset
    # If we init with Offset=0, then Output = Motor/Ratio.
    motor = DynamixelMotor(m_id, "EQX", gear_ratio=ratio, offset_degrees=0.0)
    
    print("\n1. Disabling Torque...")
    motor.relax()
    
    print("\n2. >>> ACTION REQUIRED <<<")
    print("   Please manually rotate the Ring Gear")
    print("   until the Prime Meridian (Longitude 0)")
    print("   is perfectly aligned with the pointer.")
    print("\n   Type 'ok' + ENTER when done, or 'q' to quit.")
    
    while True:
        # Simple blocking input not ideal for mpremote run, so we loop wait
        # But for 'mpremote run', stdin is forwarded.
        i = input("   > ")
        if i.strip().lower() == 'q':
            print("Cancelled.")
            return
        if i.strip().lower() == 'ok':
            break
            
    print("\n3. Reading Motor Position...")
    # This reads (Motor / Ratio) because we set offset=0 above
    current_raw_output = motor.get_angle_degrees()
    
    if current_raw_output is None:
        print("Error: Could not read motor position.")
        return
        
    print(f"   Raw Output Position: {current_raw_output:.4f} deg")
    
    # We want this position to be 0.
    # Output_New = Raw - Offset_New
    # 0 = Raw - Offset_New  =>  Offset_New = Raw
    new_offset = current_raw_output
    
    print(f"   Calculated Zero Offset: {new_offset:.4f} deg")
    
    print("\n4. Updating Configuration...")
    config["motors"]["eqx"]["offset_deg"] = new_offset
    
    try:
        with open("orbigator_config.json", "w") as f:
            json.dump(config, f)
        print("   Saved to orbigator_config.json")
    except Exception as e:
        print(f"   Error saving config: {e}")
        return
        
    print("\n5. Verifying...")
    # Re-init with new offset
    motor = DynamixelMotor(m_id, "EQX", gear_ratio=ratio, offset_degrees=new_offset)
    motor.enable_torque()
    
    check_pos = motor.get_angle_degrees()
    print(f"   Current Calibrated Position: {check_pos:.4f} deg (Should be ~0.0)")
    
    print("\nDONE! You may now reset the board.")

if __name__ == "__main__":
    set_zero()
