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

def sync_system_time(rtc):
    """Sync the Pico internal clock to the external RTC."""
    try:
        if not rtc: return
        import machine
        # RTC: (YY, MM, DD, WD, HH, MM, SS, SS)
        t = rtc.datetime()
        if t and t[0] >= 2024:
            machine.RTC().datetime(t)
            print(f"System time synced to RTC: {t[0]}-{t[1]}-{t[2]} {t[4]:02d}:{t[5]:02d}:{t[6]:02d}")
    except Exception as e:
        print("Sync time failed:", e)

# Global time reference for high-res timestamping
_time_ref = (time.time(), time.ticks_ms())

def get_timestamp(rtc=None):
    """
    Get high-resolution unix timestamp.
    Pico's time.time() is only 1s resolution. This adds ticks_ms for sub-second precision.
    """
    base_s, base_ms = _time_ref
    
    diff_ms = time.ticks_diff(time.ticks_ms(), base_ms)
    elapsed_s = diff_ms / 1000.0
    
    return base_s + elapsed_s

def set_datetime(year, month, day, hour, minute, second, rtc=None):
    """Set the RTC and system time."""
    global _time_ref
    try:
        import machine
        # (Y, M, D, WD, H, M, S, SS)
        t = (year, month, day, 0, hour, minute, second, 0)
        if rtc:
            rtc.datetime(t)
        machine.RTC().datetime(t)
        # Invalidate time ref to force re-sync
        _time_ref = None
        print(f"Time set to: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
        return True
    except Exception as e:
        print("Error setting time:", e)
        return False

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
            "timestamp": now
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        print(f"State saved: AoV={g.aov_position_deg:.3f} at TS={now:.3f}")
    except Exception as e:
        print("Error saving state:", e)

def load_state():
    """Load orbital parameters and reconstruct motor positions."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        g.orbital_altitude_km = config.get("altitude_km", 400.0)
        g.orbital_inclination_deg = config.get("inclination_deg", 51.6)
        g.orbital_eccentricity = config.get("eccentricity", 0.0)
        g.orbital_periapsis_deg = config.get("periapsis_deg", 0.0)
        
        # Reconstruct absolute positions
        last_eqx_deg = config.get("eqx_deg", 0.0)
        last_aov_deg = config.get("aov_deg", 0.0)
        
        if g.eqx_motor:
            raw_motor_val = g.eqx_motor.get_angle_degrees()
            # Trust motor RAM if valid multi-turn data exists (Soft Reboot)
            if abs(raw_motor_val) > 360:
                g.eqx_position_deg = raw_motor_val
                current_raw_deg = raw_motor_val
            else:
                # Reconstruct from modulo (Power Cycle)
                current_raw_deg = raw_motor_val % 360
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
            
            print(f"  EQX: Saved={last_eqx_deg:.2f}, RawNow={raw_motor_val:.2f}, Final={g.eqx_position_deg:.2f}")
            
        if g.aov_motor:
            raw_motor_val = g.aov_motor.get_angle_degrees()
            # Trust motor RAM if valid multi-turn data exists (Soft Reboot)
            if abs(raw_motor_val) > 360:
                g.aov_position_deg = raw_motor_val
                current_raw_deg = raw_motor_val
            else:
                # Reconstruct from modulo (Power Cycle)
                current_raw_deg = raw_motor_val % 360
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
            
            print(f"  AoV: Saved={last_aov_deg:.2f}, RawNow={raw_motor_val:.2f}, Final={g.aov_position_deg:.2f}")

        print("State loaded and positions reconstructed.")
        return config.get("timestamp", 0), last_eqx_deg, last_aov_deg
    except Exception as e:
        print("No config or error loading:", e)
        return 0, 0, 0
