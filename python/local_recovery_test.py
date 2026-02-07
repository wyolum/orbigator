
import math

# EQX Simulation Constants
TICKS_PER_REV = 4096
GEAR_RATIO = 120.0 / 14.0  # ~8.5714
TICKS_PER_OUTPUT_DEG = (TICKS_PER_REV / 360.0) * GEAR_RATIO # ~97.51
OFFSET = 0.0

def recover_abs_ticks(current_ticks, last_abs_ticks):
    """
    Snap current_ticks (0-4095) to the nearest revolution of last_abs_ticks.
    This is the core 'Boot Sync' stitching algorithm.
    """
    n_revs = round((last_abs_ticks - current_ticks) / TICKS_PER_REV)
    return int(current_ticks + (n_revs * TICKS_PER_REV))

def get_new_pos_delta(current_pos, target_pos):
    """
    Calculate the shortest-path delta (-180 to +180) between two phases.
    This is the core 'Operational Shortest Path' logic.
    """
    delta = target_pos - current_pos
    return (delta + 180) % 360 - 180

class MotorSimulator:
    def __init__(self, name, initial_abs_ticks):
        self.name = name
        self.abs_ticks = initial_abs_ticks  # Software's digital anchor
        
    def power_cycle(self, drift_output_deg=0):
        """Simulates power cycle/delay and satellite movement."""
        # Hardware register 'resets' to current physical position modulo 4096.
        # We also simulate the satellite moving by drift_output_deg.
        hw_register = self.abs_ticks % TICKS_PER_REV
        return hw_register

    def run_case(self, case_name, target_phase, saved_anchor_ticks):
        print(f"\n{'='*60}")
        print(f" TEST CASE: {case_name}")
        print(f"{'='*60}")
        
        # 1. Start from Software Anchor
        start_output = (saved_anchor_ticks / TICKS_PER_OUTPUT_DEG) - OFFSET
        print(f"[BOOT PRE-SYNC]")
        print(f"  Saved Anchor: {saved_anchor_ticks} ticks (Turn {saved_anchor_ticks // TICKS_PER_REV})")
        print(f"  Saved Phase:  {start_output % 360:.2f}°")
        
        # 2. Read HW Register (which reset on boot)
        hw_register = saved_anchor_ticks % TICKS_PER_REV
        print(f"\n[BOOT SYNC STEP]")
        print(f"  HW Register: {hw_register} ticks (0-4095)")
        
        # Stitch software to hardware orientation
        abs_ticks_synced = recover_abs_ticks(hw_register, saved_anchor_ticks)
        current_phase = (abs_ticks_synced / TICKS_PER_OUTPUT_DEG) % 360
        print(f"  Synced Abs:  {abs_ticks_synced} ticks")
        print(f"  Current Phase: {current_phase:.2f}°")
        
        # 3. Operational Tracking
        print(f"\n[TRACKING UPDATE]")
        print(f"  Target Phase: {target_phase:.2f}°")
        
        # Determine shortest path
        delta = get_new_pos_delta(current_phase, target_phase)
        print(f"  Path Delta:   {delta:+.2f}° (Shortest Path)")
        
        # Execute Move
        move_ticks = int(delta * TICKS_PER_OUTPUT_DEG)
        final_abs_ticks = abs_ticks_synced + move_ticks
        
        print(f"\n[FINAL STATE]")
        print(f"  Final Abs:   {final_abs_ticks} ticks")
        print(f"  Final Phase: {(final_abs_ticks / TICKS_PER_OUTPUT_DEG) % 360:.2f}°")
        print(f"  Final Turn:  {final_abs_ticks // TICKS_PER_REV}")
        
        if abs(delta) > 180:
             print("!!! FAILURE: Move > 180° detected !!!")
        else:
             print("✓ SUCCESS: Robust shortest-path recovery.")

# Run Cases
sim = MotorSimulator("EQX", 0)

# Turn 10 + 38 degrees = 354635 ticks approx
TURN_10_38_DEG = 354635 

sim.run_case("1. Minimal Delay (38.0 -> 38.5)", 
             target_phase=38.5, 
             saved_anchor_ticks=TURN_10_38_DEG)

sim.run_case("2. Med Delay (38.0 -> 73.0)", 
             target_phase=73.0, 
             saved_anchor_ticks=TURN_10_38_DEG)

sim.run_case("3. Long Delay (38.0 -> 308.0)", 
             target_phase=308.0, 
             saved_anchor_ticks=TURN_10_38_DEG)

sim.run_case("3b. User Scenario (38.0 -> 10.0)", 
             target_phase=10.0, 
             saved_anchor_ticks=TURN_10_38_DEG)
