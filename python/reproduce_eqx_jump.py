
import math

# EQX Simulation Constants
TICKS_PER_REV = 4096
GEAR_RATIO = 120.0 / 14.0  # 8.5714
TICKS_PER_MOTOR_DEG = TICKS_PER_REV / 360.0
TICKS_PER_OUTPUT_DEG = (TICKS_PER_MOTOR_DEG) * GEAR_RATIO # ~97.51

def get_new_pos_delta(current_pos, target_pos):
    """Shortest path delta (-180 to +180) between two phases."""
    delta = target_pos - current_pos
    return (delta + 180) % 360 - 180

def simulate_geared_jump(name, start_output_deg, target_output_deg, method="safe"):
    print(f"\n--- {name} ({method.upper()} method) ---")
    
    # Starting state: Motor has been running.
    # Case: We are at Turn 10 + 38 degrees.
    abs_ticks_start = int((start_output_deg) * TICKS_PER_OUTPUT_DEG)
    print(f"Initial State: {start_output_deg:.2f}° Output ({abs_ticks_start} Abs Ticks)")
    
    # 1. Power Cycle / Boot
    # Hardware register resets to 0-4095 range.
    hw_register = abs_ticks_start % TICKS_PER_REV
    print(f"HW Register Reset on Boot: {hw_register} ticks (0-4095)")
    
    if method == "flawed":
        # PREVIOUS BUGGY LOGIC:
        # It assumed the hardware register WAS the globe phase (assuming Turn 0)
        # current_hw_output_deg = (3705 / 11.37 / 8.57) = 38.0
        # But if the motor was actually at Turn 10, this math is only phase!
        hw_motor_deg = hw_register / TICKS_PER_MOTOR_DEG
        current_hw_output_deg = (hw_motor_deg / GEAR_RATIO) # THIS LOSES THE TURNS!
        
        # Calculate move from this 'Phase 0' context
        delta = get_new_pos_delta(current_hw_output_deg, target_output_deg)
        print(f"Flawed Calc phase: {current_hw_output_deg:.2f}° (Assumes Turn 0)")
    else:
        # NEW SAFE DELTA LOGIC:
        # Use our Anchor (start_output_deg) to provide the PHASE context.
        # But we move RELATIVE to the hardware.
        current_context_output = start_output_deg
        delta = get_new_pos_delta(current_context_output, target_output_deg)
        print(f"Safe Calc context: {current_context_output:.2f}° (Uses Anchor Context)")

    # 2. Results
    print(f"Commanded Delta:   {delta:+.2f}° Output")
    
    # The "Correction" happens when target_ticks is calculated.
    if method == "flawed":
        # Flawed target: (Phase0 + Delta + Offset) * Ratio 
        # This creates the jump!
        target_motor_deg = (current_hw_output_deg + delta) * GEAR_RATIO
        target_ticks = int(target_motor_deg * TICKS_PER_MOTOR_DEG)
    else:
        # Safe target: HW_REG + (Delta * Ratio)
        # This stays in the current gear turn.
        delta_ticks = int(delta * TICKS_PER_OUTPUT_DEG)
        target_ticks = hw_register + delta_ticks

    # The physical "Jump" is the difference between where it SHOULD be and where it goes.
    physical_move_ticks = target_ticks - hw_register
    physical_move_deg = physical_move_ticks / TICKS_PER_REV * 360 # Motor side
    physical_output_move = physical_move_deg / GEAR_RATIO
    
    print(f"Physical Move:     {physical_output_move:+.2f}° Output ({physical_move_ticks:+.0f} HW Ticks)")
    
    if abs(physical_output_move) > 10.0:
        print(f"!!! JUMP DETECTED: Motor jumped {abs(physical_output_move):.1f}° (Approx {abs(physical_output_move)/42:.1f} motor revs) !!!")
    else:
        print("✓ SUCCESS: Move is minimal and stays in gear.")

# Reproduce the bug: Start 38, move to 38.5 (Minimal change)
# But starting context is Turn 10 (approx 3600 degrees)
start_pos = 3600 + 38.0
target_pos = 38.5 # Tracking phase is normalized 0-360

simulate_geared_jump("Reproducing the Geared Jump", start_pos, target_pos, method="flawed")
simulate_geared_jump("Applying Safe Delta Fix", start_pos, target_pos, method="safe")
