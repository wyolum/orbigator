"""
EQX Power Failure Test (Tracking & Recovery Math)
================================================
1) Display current EQX on oled, follow encoder with 1 deg per detent until "confirm" is pressed.
2) Move in the negative eqx direction until confirm is pressed.
3) Stop motors, determine eqx position from cache... print recovery math. Go back to step 1.

(No actual power off or reset occurs in this test)
"""

import time
import json
from machine import Pin, I2C
from oled_display import OledDisplay
from rotary_encoder import RotaryEncoder
from buttons import Buttons
from dynamixel_motor import DynamixelMotor
from rtc import RTC
import pins

def calculate_absolute_position(last_absolute, current_motor_raw):
    """
    Calculate absolute position after a power cycle.
    The XL330 output is always in 0-4095 range after power-up.
    We find the absolute position closest to last_absolute that matches this 0-4095.
    """
    raw = current_motor_raw % 4096
    revs = last_absolute // 4096
    candidates = [
        (revs - 1) * 4096 + raw,
        (revs) * 4096 + raw,
        (revs + 1) * 4096 + raw
    ]
    return min(candidates, key=lambda x: abs(x - last_absolute))

def load_cached_abs_ticks():
    """Simple JSON-based state loader to avoid orb_utils dependency."""
    try:
        with open("orbigator_state.json", "r") as f:
            state = json.load(f)
            return state.get("eqx_abs_ticks", 0)
    except:
        return 0

def load_config():
    """Load hardware config to avoid orb_utils dependency."""
    try:
        with open("orbigator_config.json", "r") as f:
            return json.load(f)
    except:
        return {}

def run_test():
    print("EQX Power Fail Test (Tracking) Starting...")
    
    # Load config
    config = load_config()
    eqx_cfg = config.get("motors", {}).get("eqx", {})
    EQX_ID = eqx_cfg.get("id", 1)
    SPEED_LIMIT = eqx_cfg.get("speed_limit", 50)
    
    # Gear Ratio from config
    GR_NUM = eqx_cfg.get("gear_ratio_num", 120.0)
    GR_DEN = eqx_cfg.get("gear_ratio_den", 14.0)
    EQX_RATIO = GR_NUM / GR_DEN
    
    # Initialize I2C and hardware
    i2c = I2C(0, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400000)
    display = OledDisplay(i2c)
    encoder = RotaryEncoder(pins.ENC_A_PIN, pins.ENC_B_PIN, pins.ENC_BTN_PIN)
    buttons = Buttons(pins.BACK_BTN_PIN, pins.CONFIRM_BTN_PIN)
    rtc = RTC(i2c)
    
    print(f"Initializing EQX Motor (ID: {EQX_ID}, Speed: {SPEED_LIMIT}, Ratio: {GR_NUM}/{GR_DEN})...")
    eqx = DynamixelMotor(EQX_ID, "EQX", gear_ratio=EQX_RATIO, rtc=rtc)
    eqx.enable_torque()
    eqx.set_speed_limit(SPEED_LIMIT)
    
    # Reload state to get the latest cached values
    cached_eqx_abs = load_cached_abs_ticks()
    print(f"Loaded cached EQX Abs Ticks: {cached_eqx_abs}")

    while True:
        # --- STEP 1: Follow encoder ---
        print("\nSTEP 1: Follow Encoder (1 deg/detent)")
        # Start encoder at current position
        encoder.value = int(eqx.output_degrees)
        last_encoder_val = encoder.value
        
        while not buttons.confirm_pressed:
            enc_val = encoder.value
            if enc_val != last_encoder_val:
                # Tight sync: update software state then immediately command hardware
                eqx.update_present_position()
                eqx.set_nearest_degrees(float(enc_val))
                last_encoder_val = enc_val
            else:
                eqx.update_present_position()
            
            display.clear()
            display.text("STEP 1: SET EQX", 10, 0)
            display.text(f"Target: {enc_val:>4} deg", 0, 20)
            display.text(f"Actual: {eqx.output_degrees:>4.1f} deg", 0, 35)
            display.text("PRESS [OK] TO MOVE", 0, 55)
            display.show()
            time.sleep_ms(30) # Slightly faster loop for responsiveness
            
        # Wait for button release
        while buttons.confirm_pressed: time.sleep_ms(10)
        time.sleep_ms(200) # Debounce
        
        # --- STEP 2: Move Negative ---
        print("\nSTEP 2: Moving Negative")
        start_pos = eqx.output_degrees
        target_pos = start_pos
        
        # Calculate nudge rate from config speed limit (higher limit = faster nudge)
        # SPEED_LIMIT=50 gives 0.2 deg/loop (4 deg/sec)
        nudge_per_loop = SPEED_LIMIT / 250.0
        
        while not buttons.confirm_pressed:
            eqx.update_present_position()
            
            # Continuously nudge target negative based on config speed
            target_pos -= nudge_per_loop
            eqx.set_nearest_degrees(target_pos)
            
            display.clear()
            display.text("STEP 2: MOVING NEG", 10, 0)
            display.text(f"Start:  {start_pos:>4.1f} deg", 0, 20)
            display.text(f"Actual: {eqx.output_degrees:>4.1f} deg", 0, 35)
            display.text("PRESS [OK] TO STOP", 0, 55)
            display.show()
            time.sleep_ms(50)

        # Stop
        # Disable torque briefly to ensure it stops, then re-enable and hold current position
        eqx.disable_torque()
        time.sleep_ms(100)
        curr_pos = eqx.update_present_position()
        eqx.set_nearest_degrees(curr_pos)
        eqx.enable_torque()
        
        # Wait for button release
        while buttons.confirm_pressed: time.sleep_ms(10)
        time.sleep_ms(200) # Debounce

        # --- STEP 3: Recovery Math ---
        print("\nSTEP 3: Recovery Math")
        
        # Determine eqx position from cache
        cached_abs = load_cached_abs_ticks()
        
        # Get current hardware raw position (ticks)
        # Note: we want the 0-4095 phase for the recovery math demonstration
        from dynamixel_extended_utils import read_present_position
        curr_raw_ticks = read_present_position(EQX_ID)
        
        if curr_raw_ticks is not None:
            curr_phase = curr_raw_ticks % 4096
            # calculate_absolute_position logic
            recovered_abs = calculate_absolute_position(cached_abs, curr_phase)
            
            print("="*40)
            print("EQX RECOVERY MATH REPORT:")
            print(f"  Cached Abs Ticks (A):  {cached_abs}")
            print(f"  Current Phase (P):     {curr_phase} (mod 4096)")
            print(f"  Predicted Revs (R):    {cached_abs // 4096}")
            
            # Show candidates
            revs = cached_abs // 4096
            c1 = (revs - 1) * 4096 + curr_phase
            c2 = (revs) * 4096 + curr_phase
            c3 = (revs + 1) * 4096 + curr_phase
            
            print(f"  Candidates:")
            print(f"    1. {c1} (delta: {abs(c1 - cached_abs)})")
            print(f"    2. {c2} (delta: {abs(c2 - cached_abs)}) {'<-- BEST' if c2 == recovered_abs else ''}")
            print(f"    3. {c3} (delta: {abs(c3 - cached_abs)})")
            
            print(f"  \n  Final Recovered Abs:   {recovered_abs}")
            print(f"  Total Ticks Delta:     {recovered_abs - cached_abs}")
            print(f"  Output Degrees Delta:  {(recovered_abs - cached_abs) / (4096 * EQX_RATIO) * 360:.2f}°")
            print("="*40)
            
            display.clear()
            display.text("RECOVERY MATH", 10, 0)
            display.text(f"Cache: {cached_abs}", 0, 20)
            display.text(f"Phase: {curr_phase}", 0, 32)
            display.text(f"Delta: {recovered_abs - cached_abs}", 0, 44)
            display.text("PRESS [OK] TO RESTART", 0, 56)
            display.show()
        else:
            print("ERROR: Failed to read motor position!")
            display.clear()
            display.text("MOTOR READ ERROR", 10, 25)
            display.show()

        while not buttons.confirm_pressed: time.sleep_ms(50)
        while buttons.confirm_pressed: time.sleep_ms(10)
        time.sleep_ms(200)

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
