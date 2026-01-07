#!/usr/bin/env python3
"""
Orbigator Motor Tuning Script
Allows live adjustment of PID gains and speed limits.
"""
import subprocess
import sys
import argparse

def run_mpremote(command):
    try:
        subprocess.run(["mpremote"] + command.split(), check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def set_tuning(motor_id, p, d, speed, test=False, dist=15.0):
    print(f"--- Tuning Motor {motor_id} ---")
    
    # Calculate required sleep based on distance and speed (roughly)
    # Speed 1 is 0.114 RPM = 0.684 deg/sec.
    calc_speed = speed if speed is not None else 2
    wait_time = (dist / (calc_speed * 0.68)) + 3.0
    
    test_code = """
        print("Starting motion test (Speed={}, Dist={}°)...".format(_SPEED_VAL_, _DIST_VAL_))
        start_pos = m.update_present_position(force=True)
        if start_pos is not None:
            target = start_pos + _DIST_VAL_
            print("  Moving to {:.1f}... (Wait {:.1f}s)".format(target, _WAIT_TIME_))
            m.set_angle_degrees(target)
            time.sleep(_WAIT_TIME_)
            print("  Returning to {:.1f}...".format(start_pos))
            m.set_angle_degrees(start_pos)
            time.sleep(_WAIT_TIME_)
            print("Motion test complete.")"""

    # We use a small python snippet on the Pico to do the tuning
    # We use .replace() instead of .format() to avoid brace collision with the MicroPython code
    template = """
import dynamixel_motor
from dynamixel_motor import DynamixelMotor
import orb_globals as g
import _thread, time

# Use global lock if available
lock = g.uart_lock if hasattr(g, 'uart_lock') else None

def do_tune():
    try:
        m = DynamixelMotor(_MOTOR_ID_, "Tuner")
        
        # Read current gains first
        curr_p, curr_i, curr_d = m.get_pid_gains()
        print("Current Gains: P={}, I={}, D={}".format(curr_p, curr_i, curr_d))
        
        if _P_VAL_ is not None: m.set_pid_gains(p=_P_VAL_)
        if _D_VAL_ is not None: m.set_pid_gains(d=_D_VAL_)
        if _SPEED_VAL_ is not None: m.set_speed_limit(_SPEED_VAL_)
        
        # Verify if changed
        new_p, new_i, new_d = m.get_pid_gains()
        print("New Gains: P={}, I={}, D={}".format(new_p, new_i, new_d))
        
        _TEST_CODE_
    except Exception as e:
        print("Error during tuning/test: {}".format(e))

if lock:
    with lock:
        do_tune()
else:
    do_tune()
"""
    # REPLACE TEST_CODE FIRST so its placeholders are expanded by subsequent replaces!
    py_code = template.replace("_TEST_CODE_", test_code if test else "")
    py_code = py_code.replace("_MOTOR_ID_", str(motor_id))
    py_code = py_code.replace("_P_VAL_", str(p) if p is not None else "None")
    py_code = py_code.replace("_D_VAL_", str(d) if d is not None else "None")
    py_code = py_code.replace("_SPEED_VAL_", str(speed) if speed is not None else "None")
    py_code = py_code.replace("_DIST_VAL_", str(dist))
    py_code = py_code.replace("_WAIT_TIME_", str(wait_time))

    # Write to a temp file and run it
    with open("temp_tune.py", "w") as f:
        f.write(py_code)
    
    subprocess.run(["mpremote", "run", "temp_tune.py"])

def main():
    parser = argparse.ArgumentParser(description="Tune Orbigator Motor Gains")
    parser.add_argument("--id", type=int, default=2, help="Motor ID (1=EQX, 2=AoV)")
    parser.add_argument("--p", type=int, help="P gain (stiffness, default 800)")
    parser.add_argument("--d", type=int, help="D gain (damping, default 0)")
    parser.add_argument("--speed", type=int, help="Profile velocity limit")
    parser.add_argument("--test", action="store_true", help="Run a short motion test after tuning")
    parser.add_argument("--dist", type=float, default=15.0, help="Distance for test move in degrees (default 15)")
    
    args = parser.parse_args()
    
    if args.p is None and args.d is None and args.speed is None and not args.test:
        print("Error: Specify at least one parameter (--p, --d, --speed) or --test")
        return

    set_tuning(args.id, args.p, args.d, args.speed, args.test, args.dist)

if __name__ == "__main__":
    main()
