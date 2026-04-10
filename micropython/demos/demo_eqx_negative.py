"""
EQX Negative Direction Demo
============================
Moves the EQX motor in the negative direction, stopping every 90 degrees
for 3 seconds. Displays the current EQX position on the OLED.

At each stop, prints the SRAM recovery math: raw bytes, bounded-delta
candidates, recovered position vs live motor position.

Run:  import demo_eqx_negative; demo_eqx_negative.run()
"""

from machine import Pin, I2C
import time
import json
import struct
import _thread


# ---------- Constants ----------

TICKS_PER_REV = 4096
TICKS_PER_DEGREE = TICKS_PER_REV / 360.0
SRAM_MAGIC_V1 = 0xAB50
SRAM_MAGIC = 0xAB51
SRAM_RECORD_SIZE = 10


# ---------- Hardware init ----------

def init_hardware():
    import orb_globals as g
    if g.i2c_lock is None:
        g.i2c_lock = _thread.allocate_lock()

    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)

    from ds323x import DS323x
    rtc = DS323x(i2c, has_sram=True)

    with open("orbigator_config.json", "r") as f:
        cfg = json.load(f)
    eqx_cfg = cfg["motors"]["eqx"]
    gear_ratio = eqx_cfg["gear_ratio_num"] / eqx_cfg["gear_ratio_den"]
    motor_id = eqx_cfg["id"]
    speed = eqx_cfg.get("speed_limit", 50)

    # OLED display (SH1106)
    from sh1106 import SH1106_I2C
    oled_w = cfg.get("system", {}).get("oled", {}).get("width", 128)
    oled_h = cfg.get("system", {}).get("oled", {}).get("height", 64)
    disp = SH1106_I2C(oled_w, oled_h, i2c, addr=0x3C)

    return i2c, rtc, disp, motor_id, gear_ratio, speed


# ---------- Display ----------

def _degree_symbol(disp, x, y, c=1):
    """Draw a small degree symbol at (x, y)."""
    disp.pixel(x + 1, y, c)
    disp.pixel(x, y + 1, c)
    disp.pixel(x + 2, y + 1, c)
    disp.pixel(x + 1, y + 2, c)


def display_eqx(disp, position_deg, step, total_steps, paused=False):
    """Update the OLED with current EQX position."""
    disp.fill(0)

    disp.text("EQX DEMO", 32, 0)
    disp.text("Direction: NEG", 0, 14)

    pos_mod = position_deg % 360
    pos_str = f"{pos_mod:.1f}"
    disp.text("EQX: " + pos_str, 0, 28)
    _degree_symbol(disp, len("EQX: " + pos_str) * 8 + 1, 28)

    abs_str = f"Abs: {position_deg:.1f}"
    disp.text(abs_str, 0, 40)
    _degree_symbol(disp, len(abs_str) * 8 + 1, 40)

    status = "PAUSED" if paused else "MOVING"
    disp.text(f"Step {step}/{total_steps}", 0, 54)
    disp.text(status, 80, 54)

    disp.show()


# ---------- Recovery math ----------

def print_recovery_math(rtc, motor_id, gear_ratio, sram_addr, live_deg):
    """
    Read raw SRAM and hardware phase, show bounded-delta recovery
    step by step, then compare to the motor's live position.
    """
    from dynamixel_extended_utils import read_present_position

    print("\n    ---- SRAM Recovery Check ----")

    # 1. Read raw SRAM bytes
    raw = rtc.read_sram(sram_addr, SRAM_RECORD_SIZE)
    if not raw or len(raw) < 6:
        print("    SRAM: empty")
        return

    magic = struct.unpack("<H", raw[:2])[0]
    if magic == SRAM_MAGIC and len(raw) >= SRAM_RECORD_SIZE:
        _, saved_ticks, saved_offset = struct.unpack("<Hif", raw[:SRAM_RECORD_SIZE])
        fmt = "v2"
    elif magic == SRAM_MAGIC_V1 and len(raw) >= 6:
        _, saved_ticks = struct.unpack("<Hi", raw[:6])
        saved_offset = 0.0
        fmt = "v1"
    else:
        print(f"    SRAM: bad magic 0x{magic:04X}")
        return

    saved_deg = saved_ticks / TICKS_PER_DEGREE / gear_ratio
    print(f"    SRAM format  : {fmt}  magic=0x{magic:04X}")
    print(f"    Saved ticks  : {saved_ticks}")
    print(f"    Saved deg    : {saved_deg:.2f}")
    print(f"    Saved offset : {saved_offset:.2f}")

    # 2. Read current hardware phase
    phase = read_present_position(motor_id)
    if phase is None:
        print("    Hardware: no response")
        return
    print(f"    HW phase     : {phase}  (raw register)")
    phase_mod = phase % TICKS_PER_REV
    print(f"    HW phase%%CPR : {phase_mod}  (0-4095)")

    # 3. Bounded-delta candidates
    CPR = TICKS_PER_REV
    revs = saved_ticks // CPR
    candidates = [(revs + d) * CPR + phase_mod for d in (-1, 0, 1)]
    deltas = [abs(c - saved_ticks) for c in candidates]
    best_delta = min(deltas)

    print(f"    Candidates (saved revs={revs}):")
    for i, (c, d) in enumerate(zip(candidates, deltas)):
        c_deg = c / TICKS_PER_DEGREE / gear_ratio
        tag = " <-- BEST" if d == best_delta else ""
        print(f"      [{i}] ticks={c:>8d}  deg={c_deg:>9.2f}  delta={d:>6d}{tag}")

    recovered_ticks = min(candidates, key=lambda c: abs(c - saved_ticks))
    recovered_deg = recovered_ticks / TICKS_PER_DEGREE / gear_ratio

    # 4. Compare to live motor
    error = recovered_deg - live_deg
    print(f"    Recovered deg: {recovered_deg:.2f}")
    print(f"    Live motor   : {live_deg:.2f}")
    print(f"    Error        : {error:+.4f} deg")
    if abs(error) < 1.0:
        print("    PASS")
    else:
        print(f"    WARN: error exceeds 1 deg")
    print("    ----------------------------")


# ---------- Main ----------

def run(steps=8, speed=50):
    """
    Move EQX in the negative direction, stopping every 90 degrees.

    Args:
        steps: Number of 90-degree stops (default 8 = two full revolutions)
        speed: Motor speed percent (default 50)
    """
    i2c, rtc, disp, motor_id, gear_ratio, spd = init_hardware()

    print("\nEQX NEGATIVE DIRECTION DEMO")
    print(f"Motor ID={motor_id}, Gear Ratio={gear_ratio:.4f}:1")
    print(f"Steps={steps}, each -90 deg, 3s pause")

    # Create motor
    from absolute_motor import AbsoluteDynamixel
    from dynamixel_extended_utils import set_extended_mode
    set_extended_mode(motor_id)
    motor = AbsoluteDynamixel(motor_id, rtc, gear_ratio=gear_ratio,
                              sram_slot=0)

    motor.set_speed_limit(speed)
    motor.enable_torque()

    sram_addr = motor._sram_addr
    start_deg = motor.position_deg
    print(f"Starting position: {start_deg:.1f} deg")

    # Show recovery math at start
    print_recovery_math(rtc, motor_id, gear_ratio, sram_addr, start_deg)

    # Show starting position
    display_eqx(disp, start_deg, 0, steps, paused=True)
    time.sleep(1)

    try:
        for step in range(1, steps + 1):
            # Move -90 degrees from current target
            target = start_deg - (step * 90)
            print(f"\n  Step {step}/{steps}: Moving to {target:.1f} deg ...")

            motor.absolute_goto(target)
            display_eqx(disp, target, step, steps, paused=False)

            # Wait for motor to arrive (poll position)
            deadline = time.ticks_ms() + 15000  # 15s timeout
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                actual = motor.update()
                err = abs(actual - target)
                display_eqx(disp, actual, step, steps, paused=False)
                if err < 2.0:
                    break
                time.sleep_ms(100)

            actual = motor.update()
            print(f"  Arrived at {actual:.1f} deg (target {target:.1f})")

            # Print SRAM recovery math at each stop
            print_recovery_math(rtc, motor_id, gear_ratio, sram_addr, actual)

            # Pause for 3 seconds, updating display
            display_eqx(disp, actual, step, steps, paused=True)
            print(f"  Pausing 3 seconds...")
            for _ in range(30):
                actual = motor.update()
                display_eqx(disp, actual, step, steps, paused=True)
                time.sleep_ms(100)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    final = motor.update()
    print(f"\nDone. Final position: {final:.1f} deg")

    # Final recovery check
    print_recovery_math(rtc, motor_id, gear_ratio, sram_addr, final)

    display_eqx(disp, final, steps, steps, paused=True)
    disp.fill(0)
    disp.text("EQX DEMO", 32, 0)
    disp.text("COMPLETE", 32, 28)
    pos_str = f"{final:.1f}"
    disp.text("EQX: " + pos_str, 0, 48)
    _degree_symbol(disp, len("EQX: " + pos_str) * 8 + 1, 48)
    disp.show()

    return motor


if __name__ == "__main__":
    run()
