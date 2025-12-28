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

# ============ Elliptical Orbit Support ============

def solve_kepler_equation(mean_anomaly, eccentricity, tolerance=1e-6, max_iterations=10):
    """
    Solve Kepler's equation for eccentric anomaly using Newton-Raphson iteration.
    
    Kepler's equation: M = E - e*sin(E)
    Where: M = mean anomaly, E = eccentric anomaly, e = eccentricity
    
    Args:
        mean_anomaly: Mean anomaly in radians
        eccentricity: Orbital eccentricity (0.0 = circular, 0.9 = highly elliptical)
        tolerance: Convergence tolerance (default 1e-6)
        max_iterations: Maximum iterations (default 10)
    
    Returns:
        Eccentric anomaly in radians
    """
    # Initial guess: E = M
    E = mean_anomaly
    
    for _ in range(max_iterations):
        # Newton-Raphson: E_new = E - f(E)/f'(E)
        # f(E) = E - e*sin(E) - M
        # f'(E) = 1 - e*cos(E)
        sin_E = math.sin(E)
        cos_E = math.cos(E)
        f = E - eccentricity * sin_E - mean_anomaly
        f_prime = 1.0 - eccentricity * cos_E
        
        E_new = E - f / f_prime
        
        # Check convergence
        if abs(E_new - E) < tolerance:
            return E_new
        
        E = E_new
    
    # Return best estimate if not converged
    return E

def compute_true_anomaly(eccentric_anomaly, eccentricity):
    """
    Compute true anomaly from eccentric anomaly.
    
    Args:
        eccentric_anomaly: Eccentric anomaly in radians
        eccentricity: Orbital eccentricity
    
    Returns:
        True anomaly in radians
    """
    # tan(ν/2) = sqrt((1+e)/(1-e)) * tan(E/2)
    sqrt_term = math.sqrt((1.0 + eccentricity) / (1.0 - eccentricity))
    true_anomaly = 2.0 * math.atan(sqrt_term * math.tan(eccentric_anomaly / 2.0))
    return true_anomaly

def compute_orbital_radius(semi_major_axis, eccentricity, true_anomaly):
    """
    Compute orbital radius at given true anomaly.
    
    Args:
        semi_major_axis: Semi-major axis in km
        eccentricity: Orbital eccentricity
        true_anomaly: True anomaly in radians
    
    Returns:
        Orbital radius in km
    """
    # r = a(1 - e²) / (1 + e*cos(ν))
    numerator = semi_major_axis * (1.0 - eccentricity**2)
    denominator = 1.0 + eccentricity * math.cos(true_anomaly)
    return numerator / denominator

def compute_elliptical_position(elapsed_sec, period_sec, eccentricity, periapsis_deg):
    """
    Compute orbital position for elliptical orbit.
    
    Args:
        elapsed_sec: Time since periapsis passage (seconds)
        period_sec: Orbital period (seconds)
        eccentricity: Orbital eccentricity (0.0 to 0.9)
        periapsis_deg: Argument of periapsis (degrees, 0-360)
    
    Returns:
        Tuple of (aov_position_deg, instantaneous_rate_deg_sec)
    """
    if eccentricity < 0.001:  # Treat as circular for very small eccentricity
        # Simple circular motion
        mean_motion = 2.0 * math.pi / period_sec  # rad/s
        aov_position_deg = math.degrees(mean_motion * elapsed_sec) + periapsis_deg
        rate_deg_sec = 360.0 / period_sec
        return aov_position_deg % 360.0, rate_deg_sec
    
    # Compute mean anomaly (angle if orbit were circular)
    mean_motion = 2.0 * math.pi / period_sec  # rad/s
    mean_anomaly = mean_motion * elapsed_sec  # radians
    
    # Solve Kepler's equation for eccentric anomaly
    eccentric_anomaly = solve_kepler_equation(mean_anomaly, eccentricity)
    
    # Compute true anomaly (actual angle in orbit)
    true_anomaly = compute_true_anomaly(eccentric_anomaly, eccentricity)
    
    # Convert to degrees and add periapsis offset
    aov_position_deg = (math.degrees(true_anomaly) + periapsis_deg) % 360.0
    
    # Compute instantaneous angular velocity
    # For elliptical orbits: dν/dt = (n * sqrt(1-e²)) / (1 + e*cos(ν))²
    # where n = mean motion
    cos_nu = math.cos(true_anomaly)
    denominator = (1.0 + eccentricity * cos_nu)**2
    angular_velocity = (mean_motion * math.sqrt(1.0 - eccentricity**2)) / denominator
    rate_deg_sec = math.degrees(angular_velocity)
    
    return aov_position_deg, rate_deg_sec

def compute_mean_from_true_anomaly(true_anomaly_deg, eccentricity):
    """
    Compute Mean Anomaly from True Anomaly.
    Used for resuming elliptical orbits with correct velocity by backdating time.
    
    Args:
        true_anomaly_deg: True Anomaly in degrees (0-360)
        eccentricity: Orbital eccentricity (0.0 to 0.9)
        
    Returns:
        Mean Anomaly in radians (0 to 2pi)
    """
    if eccentricity < 1e-6:
        return math.radians(true_anomaly_deg)
        
    nu = math.radians(true_anomaly_deg)
    
    # tan(E/2) = sqrt((1-e)/(1+e)) * tan(nu/2)
    # Use atan which returns value in [-pi/2, pi/2]
    # We want E/2 in same quadrant.
    
    term1 = math.sqrt((1.0 - eccentricity) / (1.0 + eccentricity))
    term2 = math.tan(nu / 2.0)
    
    E_half = math.atan(term1 * term2)
    E = 2.0 * E_half
    
    # Kepler's Equation: M = E - e*sin(E)
    M = E - eccentricity * math.sin(E)
    
    # Normalize to 0-2pi
    if M < 0: M += 2 * math.pi
    return M % (2.0 * math.pi)

def sync_system_time(rtc):
    """Sync the Pico internal clock to the external RTC."""
    try:
        if not rtc: return
        import machine
        # RTC: (YY, MM, DD, WD, HH, MM, SS, SS)
        if g.i2c_lock:
            with g.i2c_lock:
                t = rtc.datetime()
        else:
            t = rtc.datetime()
            
        if t and t[0] >= 2024:
            machine.RTC().datetime(t)
            print(f"System time synced to RTC: {t[0]}-{t[1]}-{t[2]} {t[4]:02d}:{t[5]:02d}:{t[6]:02d}")
    except Exception as e:
        print("Sync time failed:", e)

# Global time reference for high-res timestamping
_time_ref = None

def get_timestamp(rtc=None):
    """Get stable integer unix timestamp."""
    return int(time.time())

def get_shortest_path_delta(current_deg, target_deg):
    """Calculate the shortest delta between two angles (0-360)."""
    delta = (target_deg - current_deg) % 360
    if delta > 180:
        delta -= 360
    return delta

def set_datetime(year, month, day, hour, minute, second, rtc=None):
    """Set the RTC and system time."""
    global _time_ref
    try:
        import machine
        # (Y, M, D, WD, H, M, S, SS)
        t = (year, month, day, 0, hour, minute, second, 0)
        if rtc:
            if g.i2c_lock:
                with g.i2c_lock:
                    rtc.datetime(t)
            else:
                rtc.datetime(t)
        machine.RTC().datetime(t)
        print(f"Time set to: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
        return True
    except Exception as e:
        print("Error setting time:", e)
        return False

import struct

STATE_FORMAT = "<4sQfffffffB16sB"
STATE_MAGIC = b"ORB!"
STATE_SIZE = struct.calcsize(STATE_FORMAT)

def _compute_checksum(data):
    """Simple 8-bit checksum for data except the last byte."""
    return sum(data[:-1]) & 0xFF

def save_state():
    """Save current orbital parameters and absolute motor positions."""
    try:
        now = get_timestamp()
        config = {
            "altitude_km": g.orbital_altitude_km,
            "inclination_deg": g.orbital_inclination_deg,
            "eccentricity": g.orbital_eccentricity,
            "periapsis_deg": g.orbital_periapsis_deg,
            "eqx_deg": g.eqx_position_deg,
            "aov_deg": g.aov_position_deg,
            "mode_id": g.current_mode_id,
            "sat_name": getattr(g.current_mode, 'satellite_name', None) if g.current_mode_id == "SGP4" else "",
            "timestamp": now
        }
        
        # 1. Attempt SRAM save if DS3232
        if g.rtc and getattr(g.rtc, 'has_sram', False):
            try:
                # Map Mode ID to integer
                mode_map = {"ORBIT": 0, "SGP4": 1, "DATETIME": 2}
                m_id = mode_map.get(g.current_mode_id, 0)
                sat_name = str(config["sat_name"])[:16]
                
                # Pack binary block (leaving checksum 0 for now)
                data = struct.pack(STATE_FORMAT, 
                    STATE_MAGIC, int(now), 
                    float(g.aov_position_deg), float(g.eqx_position_deg),
                    float(g.orbital_altitude_km), float(g.orbital_inclination_deg),
                    float(g.orbital_eccentricity), float(g.orbital_periapsis_deg),
                    m_id, sat_name.encode('utf-8'), 0
                )
                
                # Calculate and insert checksum
                data_list = bytearray(data)
                data_list[-1] = _compute_checksum(data_list)
                
                if g.i2c_lock:
                    with g.i2c_lock:
                        if g.rtc.write_sram(g.rtc.SRAM_START, data_list):
                            # SUCCESS: Stop here to avoid flash wear
                            return
                else:
                    if g.rtc.write_sram(g.rtc.SRAM_START, data_list):
                        return
            except Exception as e:
                print("SRAM save error:", e)
                    
        # 2. Fallback to Flash
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        print(f"State saved to Flash at TS={now}")
    except Exception as e:
        print("Error saving state:", e)

def load_state():
    """Load orbital parameters and reconstruct motor positions."""
    config = None
    
    # 1. Attempt RTC SRAM recovery
    if g.rtc and getattr(g.rtc, 'has_sram', False):
        try:
            if g.i2c_lock:
                with g.i2c_lock:
                    data = g.rtc.read_sram(g.rtc.SRAM_START, STATE_SIZE)
            else:
                data = g.rtc.read_sram(g.rtc.SRAM_START, STATE_SIZE)
                
            if data and data[:4] == STATE_MAGIC:
                # Verify checksum
                if data[-1] == _compute_checksum(data):
                    # Unpack
                    mag, ts, aov, eqx, alt, inc, ecc, per, mid, sat, ck = struct.unpack(STATE_FORMAT, data)
                    
                    # Decoded Mode
                    mode_rev = {0: "ORBIT", 1: "SGP4", 2: "DATETIME"}
                    config = {
                        "timestamp": ts,
                        "aov_deg": aov,
                        "eqx_deg": eqx,
                        "altitude_km": alt,
                        "inclination_deg": inc,
                        "eccentricity": ecc,
                        "periapsis_deg": per,
                        "mode_id": mode_rev.get(mid, "ORBIT"),
                        "sat_name": sat.decode('utf-8').strip('\x00')
                    }
                    print("State recovered from RTC SRAM.")
                else:
                    print("RTC SRAM checksum failed.")
            else:
                print("RTC SRAM magic missing or invalid.")
        except Exception as e:
            print("RTC SRAM recovery error:", e)

    # 2. Fallback to Flash recovery
    if config is None:
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            print("State loaded from Flash.")
        except Exception as e:
            print("No Flash config found:", e)
            return {"timestamp": 0, "mode_id": "ORBIT", "sat_name": None}

    # Common reconstruction logic
    try:
        g.orbital_altitude_km = config.get("altitude_km", 400.0)
        g.orbital_inclination_deg = config.get("inclination_deg", 51.6)
        g.orbital_eccentricity = config.get("eccentricity", 0.0)
        g.orbital_periapsis_deg = config.get("periapsis_deg", 0.0)
        
        # Import get_new_pos for shortest path calculation
        from dynamixel_extended_utils import get_new_pos
        
        last_eqx_deg = config.get("eqx_deg", 0.0)
        last_aov_deg = config.get("aov_deg", 0.0)
        timestamp = config.get("timestamp", 0)
        
        if g.eqx_motor:
            raw_motor_val = g.eqx_motor.get_angle_degrees()
            g.eqx_position_deg = get_new_pos(last_eqx_deg, raw_motor_val % 360)
            
        if g.aov_motor:
            raw_motor_val = g.aov_motor.get_angle_degrees()
            g.aov_position_deg = get_new_pos(last_aov_deg, raw_motor_val % 360)
            
        return {
            "timestamp": timestamp,
            "mode_id": config.get("mode_id", "ORBIT"),
            "sat_name": config.get("sat_name", None)
        }
    except Exception as e:
        print("Reconstruction error:", e)
        return {"timestamp": 0, "mode_id": "ORBIT", "sat_name": None}

# ============ SGP4 Support Functions ============

def compute_gmst(unix_timestamp):
    """
    Compute Greenwich Mean Sidereal Time from Unix timestamp.
    
    Args:
        unix_timestamp: Unix timestamp (seconds since 1970-01-01 00:00:00 UTC)
    
    Returns:
        GMST in radians
    """
    # Julian Date from Unix timestamp
    # Julian Date from Unix timestamp
    # MicroPython time.time() starts at 2000-01-01 00:00:00
    # JD for 2000-01-01 00:00:00 UTC is 2451544.5
    jd = (unix_timestamp / 86400.0) + 2451544.5
    
    # Days since J2000.0
    d = jd - 2451545.0
    
    # GMST at 0h UT (simplified formula, accurate to ~1 arcsecond)
    gmst_hours = 18.697374558 + 24.06570982441908 * d
    
    # Convert to radians and normalize to [0, 2π]
    gmst_rad = math.radians(gmst_hours * 15.0)  # 15 deg/hour
    gmst_rad = gmst_rad % (2.0 * math.pi)
    
    return gmst_rad

def get_jd(unix_timestamp):
    """Julian Date from MicroPython unix timestamp (starts at 2000)."""
    return (unix_timestamp / 86400.0) + 2451544.5

def get_jd_of_tle_epoch(year, day):
    """
    Calculate Julian Date for TLE epoch.
    year is 4-digit (e.g. 1997 or 2025)
    day is fractional day of year (1.0 = Jan 1 0h)
    """
    # Precise formula for JD of Jan 1 0h of the given year
    y = year
    m = 1
    d = 1
    jd_jan1 = 367*y - (7*(y + (m+9)//12))//4 + (275*m)//9 + d + 1721013.5
    # Add fractional dayoffset (TLE day 1.0 is Jan 1 0h)
    return jd_jan1 + (day - 1.0)

def parse_tle_epoch(line1):
    """
    Extract epoch year and day from TLE line 1.
    
    Args:
        line1: TLE line 1 string
    
    Returns:
        Tuple of (epoch_year, epoch_day)
    """
    epoch_year = int(line1[18:20])
    if epoch_year < 57:
        epoch_year += 2000
    else:
        raise ValueError("Pre-2000 TLEs are not supported")
    
    epoch_day = float(line1[20:32])
    
    return (epoch_year, epoch_day)

def load_tle_cache():
    """
    Load TLE cache from file.
    
    Returns:
        Dictionary of {satellite_name: {"line1": ..., "line2": ..., "last_fetch": ...}}
    """
    try:
        with open("tle_cache.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_tle_cache(cache):
    """
    Save TLE cache to file.
    
    Args:
        cache: Dictionary of TLE data
    """
    try:
        with open("tle_cache.json", "w") as f:
            json.dump(cache, f)
        return True
    except Exception as e:
        print(f"Error saving TLE cache: {e}")
        return False

def tle_needs_update(last_fetch_timestamp):
    """
    Check if TLE needs updating (>24 hours old).
    
    Args:
        last_fetch_timestamp: Unix timestamp of last fetch
    
    Returns:
        True if update needed, False otherwise
    """
    if last_fetch_timestamp == 0:
        return True
    
    now = get_timestamp()
    age_hours = (now - last_fetch_timestamp) / 3600.0
    
    return age_hours > 24.0

def get_tle_age_str(last_fetch_timestamp):
    """
    Get human-readable TLE age string.
    
    Args:
        last_fetch_timestamp: Unix timestamp of last fetch
    
    Returns:
        String like "2h" or "3d"
    """
    if last_fetch_timestamp == 0:
        return "never"
    
    now = get_timestamp()
    age_sec = now - last_fetch_timestamp
    
    if age_sec < 3600:
        return f"{int(age_sec/60)}m"
    elif age_sec < 86400:
        return f"{int(age_sec/3600)}h"
    else:
        return f"{int(age_sec/86400)}d"
