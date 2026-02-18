"""
EQX Absolute Position Recovery Demo
====================================
Demonstrates that the EQX motor never loses track of its position
using AbsoluteDynamixel + RTC SRAM persistence.

The demo:
  Phase 1 - Boot recovery: read raw SRAM, show the bounded-delta math
  Phase 2 - Live prediction: compute real-time EQX from saved anchor + elapsed time
  Phase 3 - Simulated power cycle: destroy and recreate the motor, verify recovery

Run:  import demo_eqx_recovery; demo_eqx_recovery.run()
"""

from machine import Pin, I2C
import time
import struct
import math
import json

# ---------- Hardware init ----------

def init_hardware():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    from ds323x import DS323x
    rtc = DS323x(i2c, has_sram=True)

    with open("orbigator_config.json", "r") as f:
        cfg = json.load(f)
    eqx_cfg = cfg["motors"]["eqx"]
    gear_ratio = eqx_cfg["gear_ratio_num"] / eqx_cfg["gear_ratio_den"]
    motor_id = eqx_cfg["id"]
    speed = eqx_cfg.get("speed_limit", 20)

    return i2c, rtc, motor_id, gear_ratio, speed


# ---------- Physical constants (duplicated to keep demo standalone) ----------

EARTH_RADIUS    = 6378.137
EARTH_MU        = 398600.4418
EARTH_J2        = 0.00108263
EARTH_ROT_DEG   = 360.0           # deg / sidereal day
TICKS_PER_REV   = 4096
SRAM_MAGIC      = 0xAB50
SRAM_ADDR       = 0x30            # slot 0


def eqx_rate_deg_sec(altitude_km, inclination_deg):
    """EQX angular velocity in the Earth-fixed frame (deg/s)."""
    a = altitude_km + EARTH_RADIUS
    inc = math.radians(inclination_deg)
    n = math.sqrt(EARTH_MU / (a ** 3))
    j2_rate = math.degrees(-1.5 * n * EARTH_J2 * (EARTH_RADIUS / a) ** 2 * math.cos(inc)) * 86400
    total_deg_day = -(j2_rate + EARTH_ROT_DEG)
    return total_deg_day / 86400.0


# ---------- Phase 1: Boot recovery ----------

def phase1_boot_recovery(rtc, motor_id, gear_ratio):
    """Show raw SRAM read and bounded-delta math step by step."""
    print("\n" + "=" * 60)
    print("PHASE 1: BOOT RECOVERY FROM SRAM")
    print("=" * 60)

    # 1. Read raw SRAM bytes
    raw = rtc.read_sram(SRAM_ADDR, 6)
    if not raw or len(raw) < 6:
        print("  SRAM is empty -- first boot")
        return None

    magic, saved_ticks = struct.unpack("<Hi", raw)
    #print(f"  Raw SRAM bytes : {' '.join(f'{b:02X}' for b in raw)}")
    print(f"  Magic          : 0x{magic:04X}  {'OK' if magic == SRAM_MAGIC else 'BAD'}")
    if magic != SRAM_MAGIC:
        print("  No valid checkpoint found -- treating as first boot")
        return None

    saved_deg = saved_ticks / (TICKS_PER_REV / 360.0) / gear_ratio
    print(f"  Saved abs ticks: {saved_ticks}")
    print(f"  Saved abs deg  : {saved_deg:.2f}")

    # 2. Read current hardware phase
    from dynamixel_extended_utils import read_present_position
    phase = read_present_position(motor_id)
    print(f"\n  Hardware phase  : {phase}  (0-4095)")

    # 3. Bounded-delta recovery
    CPR = TICKS_PER_REV
    p = phase % CPR
    revs = saved_ticks // CPR
    candidates = [(revs + d) * CPR + p for d in (-1, 0, 1)]
    deltas = [abs(c - saved_ticks) for c in candidates]

    print(f"\n  Bounded-delta candidates (revs={revs}):")
    for i, (c, d) in enumerate(zip(candidates, deltas)):
        tag = " <-- best" if d == min(deltas) else ""
        c_deg = c / (TICKS_PER_REV / 360.0) / gear_ratio
        print(f"    [{i}] ticks={c:>8d}  ({c_deg:>8.2f} deg)  delta={d:>6d}{tag}")

    recovered = min(candidates, key=lambda c: abs(c - saved_ticks))
    rec_deg = recovered / (TICKS_PER_REV / 360.0) / gear_ratio
    error = abs(recovered - saved_ticks) / (TICKS_PER_REV / 360.0) / gear_ratio
    print(f"\n  Recovered ticks: {recovered}")
    print(f"  Recovered deg  : {rec_deg:.2f}")
    print(f"  Recovery error : {error:.4f} deg")

    return recovered


# ---------- Phase 2: Live tracking while moving ----------

def phase2_track_satellite(motor, altitude_km, inclination_deg, duration_sec=20, override_rate_deg_s=None):
    """
    Drive the motor at the correct tracking rate for the given orbit,
    while continuously proving SRAM tracks the absolute position.
    """
    print("\n" + "=" * 60)
    print("PHASE 2: LIVE TRACKING")
    print("=" * 60)

    start_deg = motor.position_deg
    if override_rate_deg_s is not None:
        rate_deg_sec = override_rate_deg_s
        print(f"  MODE           : HIGH SPEED TEST")
        print(f"  Target Rate    : {rate_deg_sec:.2f} deg/s")
    else:
        rate_deg_sec = eqx_rate_deg_sec(altitude_km, inclination_deg)
        print(f"  Orbit          : {altitude_km:.1f} km, {inclination_deg:.1f} deg inc")
        print(f"  Tracking Rate  : {rate_deg_sec:.6f} deg/s")
    print(f"  Start position : {start_deg:.2f} deg")
    print(f"  Duration       : {duration_sec}s")

    print(f"\n  {'sec':>4s}  {'command':>10s}  {'SRAM':>10s}  {'actual':>10s}  {'err':>8s}")
    print(f"  {'---':>4s}  {'-------':>10s}  {'----':>10s}  {'------':>10s}  {'---':>8s}")

    start_time = time.ticks_ms()

    # Move at 1Hz steps for the demo
    for tick in range(duration_sec):
        # Calculate target based on elapsed time
        elapsed = tick  # roughly
        target = start_deg + rate_deg_sec * elapsed

        # 1. Command the motor
        motor.absolute_goto(target)
        time.sleep(1)

        # 2. Read SRAM (this is all a reboot would have)
        raw = motor.rtc.read_sram(motor._sram_addr, 6)
        _, sram_ticks = struct.unpack("<Hi", raw)
        sram_deg = sram_ticks / (TICKS_PER_REV / 360.0) / motor.gear_ratio

        # 3. Read actual hardware position
        actual = motor.update()

        # 4. Error between SRAM checkpoint and actual
        error = ((sram_deg % 360) - (actual % 360) + 180) % 360 - 180

        print(f"  {tick:4d}  {target:10.2f}  {sram_deg:10.2f}  {actual:10.2f}  {error:+8.2f}")


# ---------- Phase 3: Simulated power cycle ----------

def phase3_power_cycle(rtc, motor_id, gear_ratio, speed, pos_before):
    """Destroy the motor, re-create it, show position is retained."""
    print("\n" + "=" * 60)
    print("PHASE 3: SIMULATED POWER CYCLE")
    print("=" * 60)

    print(f"  Position before: {pos_before:.2f} deg")
    print("  Destroying motor object...")
    # (motor object is already out of scope from caller)
    time.sleep(1)

    print("  Re-creating AbsoluteDynamixel (simulates reboot)...")
    from absolute_motor import AbsoluteDynamixel
    motor2 = AbsoluteDynamixel(motor_id, rtc, gear_ratio=gear_ratio, sram_slot=0)

    from dynamixel_extended_utils import write_dword
    speed_val = int((speed / 100.0) * 445)
    if speed_val == 0: speed_val = 1
    write_dword(motor_id, 112, speed_val)

    pos_after = motor2.position_deg
    error = ((pos_after % 360) - (pos_before % 360) + 180) % 360 - 180

    print(f"  Position after : {pos_after:.2f} deg")
    print(f"  Error          : {error:+.4f} deg")

    if abs(error) < 1.0:
        print("\n  PASS: Position recovered within 1 degree")
    else:
        print(f"\n  FAIL: Recovery error {error:.4f} deg exceeds 1 degree")

    return motor2


# ---------- Main ----------

def run(altitude_km=400.0, inclination_deg=51.6, duration_sec=20):
    """
    Run the full EQX recovery demonstration.

    Args:
        altitude_km: Simulated orbital altitude (default ISS 400 km)
        inclination_deg: Orbital inclination (default ISS 51.6 deg)
        duration_sec: How long to run the live prediction phase
    """
    i2c, rtc, motor_id, gear_ratio, speed = init_hardware()

    print("\nEQX ABSOLUTE POSITION RECOVERY DEMO")
    print(f"Motor ID={motor_id}, Gear Ratio={gear_ratio:.4f}:1")

    # Phase 1: Show what SRAM contains and the recovery math
    phase1_boot_recovery(rtc, motor_id, gear_ratio)

    # Create motor
    from absolute_motor import AbsoluteDynamixel
    motor = AbsoluteDynamixel(motor_id, rtc, gear_ratio=gear_ratio, sram_slot=0)

    # Set speed
    from dynamixel_extended_utils import write_dword
    speed_val = int((speed / 100.0) * 445)
    if speed_val == 0: speed_val = 1
    write_dword(motor_id, 112, speed_val)

    # Phase 2: Live tracking (at max speed for test)
    # Calculate max speed in deg/s (Output Shaft)
    # Speed unit is 0.229 RPM (Motor Shaft). 
    # speed_val is the register value (0-1023 approx).
    speed_rpm_motor = speed_val * 0.229
    max_deg_s_motor = speed_rpm_motor * 6.0
    max_deg_s_output = max_deg_s_motor / gear_ratio
    
    # We want to move fast, so let's use 90% of max output speed
    test_rate = max_deg_s_output * 0.9
    
    print(f"  Max Motor Speed: {max_deg_s_motor:.2f} deg/s")
    print(f"  Max Output Speed: {max_deg_s_output:.2f} deg/s")

    phase2_track_satellite(motor, altitude_km, inclination_deg, duration_sec, override_rate_deg_s=test_rate)

    # Phase 3: Simulated power cycle
    pos_before = motor.update()
    del motor
    motor = phase3_power_cycle(rtc, motor_id, gear_ratio, speed, pos_before)

    # Final summary
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("Key takeaway: EQX position is fully recoverable from")
    print("6 bytes of SRAM + the current hardware phase (0-4095).")
    print("Combined with elapsed time and orbital parameters,")
    print("we can compute the correct EQX at any moment.")

    return motor


if __name__ == "__main__":
    run()
