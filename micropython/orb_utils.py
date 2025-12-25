"""
Orbigator Utilities and Constants
Shared functions and physical constants to break circular dependencies
"""
import math, time, json
import orb_globals as g

# Physical constants
EARTH_RADIUS = 6378.137  # km
EARTH_MU = 398600.4418   # km^3/s^2 (gravitational parameter)
EARTH_J2 = 0.00108263    # J2 perturbation coefficient
SIDEREAL_DAY_SEC = 86164.0905  # seconds
EARTH_ROTATION_DEG_DAY = 360.0
CONFIG_FILE = "orbigator_config.json"

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

def compute_period_from_altitude(altitude_km):
    """Compute orbital period from altitude using Kepler's third law."""
    a = altitude_km + EARTH_RADIUS  # semi-major axis
    period_sec = 2 * math.pi * math.sqrt(a**3 / EARTH_MU)
    period_min = period_sec / 60.0
    return period_min

def compute_altitude_from_period(period_min):
    """Compute orbital altitude from period using Kepler's third law."""
    period_sec = period_min * 60.0
    # T = 2π√(a³/μ) => a = (μT²/4π²)^(1/3)
    a = (EARTH_MU * period_sec**2 / (4 * math.pi**2)) ** (1.0/3.0)
    altitude = a - EARTH_RADIUS
    return altitude, a

def compute_eqx_rate_j2(altitude_km, inclination_deg=None):
    """Compute EQX rate in Earth-fixed frame (deg/day)."""
    if inclination_deg is None:
        inclination_deg = g.orbital_inclination_deg
        
    a = altitude_km + EARTH_RADIUS
    inc_rad = math.radians(inclination_deg)
    n = math.sqrt(EARTH_MU / (a**3))
    eqx_rate_rad_s = -1.5 * n * EARTH_J2 * (EARTH_RADIUS / a)**2 * math.cos(inc_rad)
    eqx_j2_deg_day = math.degrees(eqx_rate_rad_s) * 86400
    eqx_total_deg_day = -(eqx_j2_deg_day + EARTH_ROTATION_DEG_DAY)
    return eqx_total_deg_day

def compute_motor_rates(altitude_km):
    """Compute motor rotation rates for given altitude."""
    period_min = compute_period_from_altitude(altitude_km)
    aov_deg_per_sec = 360.0 / (period_min * 60.0)
    eqx_rate_deg_day = compute_eqx_rate_j2(altitude_km)
    eqx_deg_per_sec = eqx_rate_deg_day / 86400.0
    return aov_deg_per_sec, eqx_deg_per_sec, eqx_rate_deg_day, period_min

def get_timestamp(rtc=None):
    """Get current unix timestamp from RTC or system time."""
    try:
        if rtc:
            t = rtc.datetime()
            if t is None or t[0] < 2024:
                # External RTC is dead/reset, try internal Pico RTC
                import machine
                t = machine.RTC().datetime()
                if t[0] < 2024:
                    # Both are reset
                    return time.time()
            
            # Rearrange to (YY, MM, DD, HH, MM, SS, WD, YD) for time.mktime
            mk_tuple = (t[0], t[1], t[2], t[4], t[5], t[6], t[3], 0)
            return time.mktime(mk_tuple)
        else:
            return time.time()
    except Exception:
        return time.time()

def save_state():
    """Save current orbital parameters and absolute motor positions."""
    try:
        config = {
            "altitude_km": g.orbital_altitude_km,
            "inclination_deg": g.orbital_inclination_deg,
            "eqx_deg": g.eqx_position_deg,
            "aov_deg": g.aov_position_deg,
            "timestamp": get_timestamp(g.rtc)
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        print("State saved:", config)
    except Exception as e:
        print("Error saving state:", e)

def load_state():
    """Load orbital parameters and reconstruct motor positions."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        g.orbital_altitude_km = config.get("altitude_km", 400.0)
        g.orbital_inclination_deg = config.get("inclination_deg", 51.6)
        
        # Reconstruct absolute positions
        last_eqx_deg = config.get("eqx_deg", 0.0)
        last_aov_deg = config.get("aov_deg", 0.0)
        
        if g.eqx_motor:
            current_raw_deg = g.eqx_motor.get_angle_degrees() % 360
            revs = int(last_eqx_deg // 360)
            candidates = [
                (revs - 1) * 360 + current_raw_deg,
                (revs) * 360 + current_raw_deg,
                (revs + 1) * 360 + current_raw_deg
            ]
            g.eqx_position_deg = min(candidates, key=lambda x: abs(x - last_eqx_deg))
            
            # Sync back to motor object
            g.eqx_motor.output_degrees = g.eqx_position_deg
            g.eqx_motor.motor_degrees = g.eqx_position_deg * g.eqx_motor.gear_ratio
            
            print(f"  EQX: Saved={last_eqx_deg:.2f}, RawNow={current_raw_deg:.2f}, Final={g.eqx_position_deg:.2f}")
            
        if g.aov_motor:
            current_raw_deg = g.aov_motor.get_angle_degrees() % 360
            revs = int(last_aov_deg // 360)
            candidates = [
                (revs - 1) * 360 + current_raw_deg,
                (revs) * 360 + current_raw_deg,
                (revs + 1) * 360 + current_raw_deg
            ]
            g.aov_position_deg = min(candidates, key=lambda x: abs(x - last_aov_deg))
            
            # Sync back to motor object
            g.aov_motor.output_degrees = g.aov_position_deg
            g.aov_motor.motor_degrees = g.aov_position_deg * g.aov_motor.gear_ratio
            
            print(f"  AoV: Saved={last_aov_deg:.2f}, RawNow={current_raw_deg:.2f}, Final={g.aov_position_deg:.2f}")

        print("State loaded and positions reconstructed.")
        return config.get("timestamp", 0)
    except Exception as e:
        print("No config or error loading:", e)
        return 0
