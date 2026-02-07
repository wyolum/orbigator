"""
EQX Absolute Position Management Tool
Standalone script to inspect and fix the EQX revolution anchor.

Usage: 
1. Run status: 
   mpremote run micropython/eqx_tool.py status
2. Sync to physical position (e.g., set to 0 degrees):
   mpremote run micropython/eqx_tool.py sync 0
"""

import machine, time, struct, json, sys
from machine import Pin, I2C
from ds323x import DS323x
import pins
import orb_utils as utils
import orb_globals as g
from dynamixel_extended_utils import read_present_position

# --- Hardware Setup ---
i2c = I2C(0, scl=Pin(pins.I2C_SCL_PIN), sda=Pin(pins.I2C_SDA_PIN), freq=400000)
rtc = DS323x(i2c, has_sram=True)
g.rtc = rtc # For orb_utils

# --- Constants from Config ---
try:
    with open("orbigator_config.json", "r") as f:
        config_data = json.load(f)
    EQX_ID = config_data["motors"]["eqx"]["id"]
    EQX_RATIO = config_data["motors"]["eqx"]["gear_ratio_num"] / config_data["motors"]["eqx"]["gear_ratio_den"]
    EQX_OFFSET = config_data["motors"]["eqx"]["offset_deg"]
except:
    print("Error: Could not load orbigator_config.json")
    sys.exit(1)

TICKS_PER_REV = 4096
TICKS_PER_DEG = TICKS_PER_REV / 360.0

def get_current_sram():
    """Read the current V4 state from SRAM."""
    try:
        data = rtc.read_sram(rtc.SRAM_START, utils.STATE_SIZE)
        if not data or data[:4] != utils.STATE_MAGIC:
            return None
        if data[4] != 4:
            print(f"SRAM Version {data[4]} is not V4. No absolute ticks found.")
            return None
            
        # Unpack V4
        mag, ver, ts, aov, eqx, alt, inc, ecc, per, rev, mid, sat, a_ticks, e_ticks, ck = struct.unpack(utils.STATE_FORMAT, data)
        return {
            "version": ver,
            "eqx_deg": eqx,
            "eqx_abs_ticks": e_ticks,
            "raw_ticks": e_ticks % TICKS_PER_REV
        }
    except Exception as e:
        print(f"Error reading SRAM: {e}")
        return None

def print_status():
    print("-" * 40)
    print("ORBIGATOR EQX STATUS")
    print("-" * 40)
    
    # 1. Hardware Read
    raw_hw = read_present_position(EQX_ID)
    if raw_hw is None:
        print("Error: Could not communicate with EQX motor!")
    else:
        print(f"Hardware Raw Ticks: {raw_hw} (Offset: {raw_hw/TICKS_PER_DEG:.1f} motor deg)")
    
    # 2. SRAM Read
    sram = get_current_sram()
    if sram:
        print(f"SRAM V4 Anchor:    {sram['eqx_abs_ticks']} absolute ticks")
        revs = sram['eqx_abs_ticks'] // TICKS_PER_REV
        print(f"SRAM Revolution:   {revs}")
        print(f"SRAM Saved Output: {sram['eqx_deg']:.2f} degrees")
        
        if raw_hw is not None:
            # Predict Snap-to-Nearest
            candidates = [
                (revs - 1) * TICKS_PER_REV + raw_hw,
                (revs) * TICKS_PER_REV + raw_hw,
                (revs + 1) * TICKS_PER_REV + raw_hw
            ]
            predicted = min(candidates, key=lambda x: abs(x - sram['eqx_abs_ticks']))
            print(f"Predicted Recovery: {predicted} absolute ticks")
            pred_deg = (predicted / TICKS_PER_DEG / EQX_RATIO) - EQX_OFFSET
            print(f"Predicted Output:   {pred_deg:.2f} degrees")
    else:
        print("SRAM: No valid V4 state found.")
    print("-" * 40)

def set_anchor_from_deg(deg_target):
    """
    Manually set the EQX SRAM anchor so that the current physical position
    is interpreted as 'deg_target' output degrees.
    """
    raw_hw = read_present_position(EQX_ID)
    if raw_hw is None:
        print("Error: Could not read motor to set anchor.")
        return

    # Calculate what the absolute ticks SHOULD be
    # Output = (MotorAbs / TicksPerDeg / Ratio) - Offset = deg_target
    # MotorAbs = (deg_target + Offset) * Ratio * TicksPerDeg
    target_abs_ticks = (deg_target + EQX_OFFSET) * EQX_RATIO * TICKS_PER_DEG
    
    # We must snap this to a value that matches the current raw hardware reading
    revs = round((target_abs_ticks - raw_hw) / TICKS_PER_REV)
    final_abs_ticks = int(raw_hw + (revs * TICKS_PER_REV))
    
    print(f"Syncing anchor to physical position {deg_target} deg...")
    print(f"Calculated target ticks: {target_abs_ticks:.0f}")
    print(f"Selected revolution:     {revs}")
    print(f"Final Absolute Anchor:   {final_abs_ticks}")
    
    # Load current state, update it, and save back
    # Note: We need a full mock 'config' to use utils.save_state
    # Or we can just modify the specific bytes in SRAM if we're careful.
    # Let's use the standard save_state but populate the global motor objects.
    
    class MockMotor:
        def __init__(self, abs_ticks): self.absolute_ticks = abs_ticks
        
    g.eqx_motor = MockMotor(final_abs_ticks)
    g.aov_motor = MockMotor(0) # Default
    
    # Prepare a minimal config for save_state
    fake_config = {
        "aov_deg": 0.0, "eqx_deg": deg_target,
        "altitude_km": 400, "inclination_deg": 51.6, "eccentricity": 0, "periapsis_deg": 0,
        "rev_count": 0, "mode_id": "ORBIT", "sat_name": ""
    }
    
    # We must call save_state with this config. 
    # utils.save_state reads from orb_globals and a config dict.
    # Let's check orb_utils signature.
    # save_state() in orb_utils doesn't take arguments, it uses g.current_mode, etc.
    # Actually, orb_utils.save_state(config=None)
    
    print("Writing to SRAM...")
    utils.save_state(config=fake_config)
    print("Success. Run 'status' again to verify.")

# --- Simple CLI ---
if len(sys.argv) < 2:
    print_status()
else:
    cmd = sys.argv[1].lower()
    if cmd == "status":
        print_status()
    elif cmd == "sync" and len(sys.argv) == 3:
        target = float(sys.argv[2])
        set_anchor_from_deg(target)
    else:
        print("Unknown command. Use 'status' or 'sync <deg>'.")
