
import math

# Constants from Orbigator
EQX_GEAR_RATIO = 120.0 / 14.0 # 8.5714
TICKS_PER_REV = 4096
TICKS_PER_MOTOR_DEGREE = TICKS_PER_REV / 360.0
EQX_OFFSET = 0.0 # Simplified for storyboard

def get_new_pos(current_pos, command_pos, direction=None):
    """Refined Logic: Shortest path from current_pos to command_pos (mod 360)"""
    turns, pos = divmod(current_pos, 360)
    change = command_pos - pos
    
    # Normalize change to shortest path: -180 to +180
    if direction is None or direction == 0:
        change = (change + 180) % 360 - 180
    elif direction > 0:
        change = change % 360
    else: # direction < 0:
        change = change % 360 - 360
        
    return turns * 360 + pos + change

def simulate_case(name, start_eqx, target_eqx, hardware_revs_moved=0):
    print(f"\n{'='*60}")
    print(f" STORYBOARD: {name}")
    print(f"{'='*60}")
    
    # 1. INITIAL STATE
    motor_start_deg = (start_eqx + EQX_OFFSET) * EQX_GEAR_RATIO
    motor_start_ticks = int(motor_start_deg * TICKS_PER_MOTOR_DEGREE)
    
    print(f"[INITIAL STATE]")
    print(f"  UI Output:      {start_eqx:.2f}°")
    print(f"  Abs Motor Ticks: {motor_start_ticks} (Software Anchor)")
    print(f"  HW Register:    {motor_start_ticks % TICKS_PER_REV} (0-4095 phase)")
    
    print(f"\n[POWER CYCLE / DELAY]")
    print(f"  ...Time passes. Satellite moves to {target_eqx:.2f}°")
    if hardware_revs_moved != 0:
        print(f"  ...Physical motor bumped by {hardware_revs_moved} revolutions")

    # 2. WAKE UP (Software has the anchor, Hardware has the register)
    # The register might have reset to 0-4095 if it was a hard power cycle,
    # or it might be preserved if it was just a sleep. Let's assume hard reset (0-4095 base).
    hw_register_now = (motor_start_ticks + (hardware_revs_moved * TICKS_PER_REV)) % TICKS_PER_REV
    
    # Logic Step 1: Read Hardware (0-4095)
    # Note: Even in Extended Mode, the local phase is raw_ticks % 4096
    print(f"\n[ORBIGATOR WAKES UP]")
    print(f"  Reading HW Register: {hw_register_now} ticks")
    
    # Logic Step 2: Convert register to current "Phase Output"
    current_hw_output_deg = (hw_register_now / TICKS_PER_MOTOR_DEGREE / EQX_GEAR_RATIO) - EQX_OFFSET
    print(f"  Calculated Phase:    {current_hw_output_deg:.2f}°")
    
    # Logic Step 3: Calculate Nearest target relative to that register
    # This is Step 4 in user storyboard: "rotate total of X degrees to align"
    new_output_deg = get_new_pos(current_hw_output_deg, target_eqx)
    delta_output = new_output_deg - current_hw_output_deg
    
    # 3. THE MOVE
    target_motor_deg = (new_output_deg + EQX_OFFSET) * EQX_GEAR_RATIO
    target_ticks = int(target_motor_deg * TICKS_PER_MOTOR_DEGREE)
    target_register = target_ticks % TICKS_PER_REV
    
    print(f"\n[COMMUTATION]")
    print(f"  Commanded Delta: {delta_output:+.2f}° Output")
    print(f"  Motor Rotation:  {delta_output * EQX_GEAR_RATIO:+.2f}° Motor")
    print(f"  Goal Register:   {target_register} ticks")
    
    print(f"\n[FINAL STATE]")
    print(f"  UI Output:    {target_eqx:.2f}°")
    
    # Safety Check
    if abs(delta_output) > 180:
        print("\n!!! DANGER: MOVE EXCEEDS 180 DEGREES (Endless Spinning) !!!")
    else:
        print("\n✓ SUCCESS: Shortest physical path taken.")

# Run the Storyboard
simulate_case("1. No Delay Restart", 38.0, 38.5)
simulate_case("2. 35° EQX Delay (Forward Catch-up)", 38.0, 73.0)
simulate_case("3. 270° EQX Delay (Shortest path is -90° Back)", 38.0, 308.0)
simulate_case("User Scenario: target 10, current 38", 38.0, 10.0)
