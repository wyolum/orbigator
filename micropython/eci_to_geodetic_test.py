"""
ECI to Geodetic Conversion for MicroPython on Pico2W
Uses the existing sgp4.py library and implements GMST calculation
"""

import json
import math
import time
try:
    from sgp4 import SGP4
    import tle_parser
except ImportError:
    # For testing with regular Python, adjust import path
    import sys
    sys.path.insert(0, '/home/justin/code/orbigator/micropython')
    from sgp4 import SGP4
    import tle_parser

def parse_tle_skip_checksum(line1, line2):
    """Parse TLE without checksum validation for testing"""
    original_verify = tle_parser._verify_checksum
    tle_parser._verify_checksum = lambda x: True
    try:
        result = tle_parser.parse_tle(line1, line2)
    finally:
        tle_parser._verify_checksum = original_verify
    return result

def load_tle_from_cache(satellite_name="ISS"):
    """Load TLE data from the cache file"""
    cache_path = '/home/justin/code/orbigator/micropython/tle_cache.json'
    
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    if satellite_name not in cache:
        raise ValueError(f"Satellite {satellite_name} not found in cache")
    
    tle_data = cache[satellite_name]
    return tle_data['line1'], tle_data['line2']

def compute_julian_date(year, month, day, hour, minute, second):
    """Compute Julian Date from calendar date"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd = jdn + (hour - 12) / 24.0 + minute / 1440.0 + second / 86400.0
    
    return jd

def gmst_from_jd(jd):
    """
    Calculate Greenwich Mean Sidereal Time from Julian Date
    Returns GMST in radians
    
    Uses the standard formula from Vallado's "Fundamentals of Astrodynamics"
    """
    # Julian centuries from J2000.0
    T = (jd - 2451545.0) / 36525.0
    
    # GMST in seconds
    gmst_sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * T + \
               0.093104 * T**2 - 6.2e-6 * T**3
    
    # Convert to degrees, then radians
    gmst_deg = (gmst_sec / 240.0) % 360.0
    gmst_rad = math.radians(gmst_deg)
    
    return gmst_rad

def eci_to_ecef(x_eci, y_eci, z_eci, gmst):
    """
    Convert ECI coordinates to ECEF (Earth-Centered Earth-Fixed)
    
    Args:
        x_eci, y_eci, z_eci: Position in ECI frame (km)
        gmst: Greenwich Mean Sidereal Time (radians)
    
    Returns:
        x_ecef, y_ecef, z_ecef: Position in ECEF frame (km)
    """
    cos_gmst = math.cos(gmst)
    sin_gmst = math.sin(gmst)
    
    # Rotation matrix from ECI to ECEF
    x_ecef = cos_gmst * x_eci + sin_gmst * y_eci
    y_ecef = -sin_gmst * x_eci + cos_gmst * y_eci
    z_ecef = z_eci
    
    return x_ecef, y_ecef, z_ecef

def ecef_to_geodetic(x, y, z):
    """
    Convert ECEF coordinates to geodetic (lat, lon, alt)
    Uses WGS-84 ellipsoid model with iterative algorithm
    
    Args:
        x, y, z: Position in ECEF frame (km)
    
    Returns:
        lat, lon, alt: Latitude (deg), Longitude (deg), Altitude (km)
    """
    # WGS-84 constants
    a = 6378.137  # Semi-major axis (km)
    f = 1.0 / 298.257223563  # Flattening
    e2 = 2*f - f*f  # Eccentricity squared
    
    # Longitude is straightforward
    lon = math.atan2(y, x)
    
    # Iterative calculation for latitude and altitude
    p = math.sqrt(x*x + y*y)
    lat = math.atan2(z, p * (1.0 - e2))
    
    for _ in range(5):  # Usually converges in 3-4 iterations
        sin_lat = math.sin(lat)
        N = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
        alt = p / math.cos(lat) - N
        lat = math.atan2(z, p * (1.0 - e2 * N / (N + alt)))
    
    # Final altitude calculation
    sin_lat = math.sin(lat)
    N = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    alt = p / math.cos(lat) - N
    
    # Convert to degrees
    lat_deg = math.degrees(lat)
    lon_deg = math.degrees(lon)
    
    return lat_deg, lon_deg, alt

def get_current_time():
    """Get current UTC time - works on both desktop and micropython"""
    try:
        # Try desktop Python
        from datetime import datetime, timezone
        dt = datetime.now(timezone.utc)
        return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond/1e6)
    except:
        # MicroPython - assume time is already set via NTP
        t = time.gmtime()
        return (t[0], t[1], t[2], t[3], t[4], t[5])

def compute_satellite_position(satellite_name="ISS"):
    """
    Compute satellite position in ECI, ECEF, and geodetic coordinates
    
    Returns:
        dict with all coordinate systems
    """
    # Load and parse TLE
    line1, line2 = load_tle_from_cache(satellite_name)
    tle = parse_tle_skip_checksum(line1, line2)
    
    # Initialize SGP4
    sgp4 = SGP4()
    sgp4.init(
        epoch_year=tle['epoch_year'],
        epoch_day=tle['epoch_day'],
        bstar=tle['bstar'],
        inc=tle['inclination'],
        raan=tle['raan'],
        ecc=tle['eccentricity'],
        argp=tle['arg_perigee'],
        m=tle['mean_anomaly'],
        n=tle['mean_motion']
    )
    
    # Get current time
    year, month, day, hour, minute, second = get_current_time()
    
    # Compute Julian Date
    jd = compute_julian_date(year, month, day, hour, minute, second)
    
    # Compute time since epoch in minutes
    epoch_jd = compute_julian_date(
        tle['epoch_year'], 
        1, 1, 0, 0, 0
    ) + tle['epoch_day'] - 1.0
    
    t_min = (jd - epoch_jd) * 1440.0  # days to minutes
    
    # Propagate to current time (returns ECI coordinates)
    x_eci, y_eci, z_eci = sgp4.propagate(t_min)
    
    # Calculate GMST
    gmst = gmst_from_jd(jd)
    
    # Convert ECI to ECEF
    x_ecef, y_ecef, z_ecef = eci_to_ecef(x_eci, y_eci, z_eci, gmst)
    
    # Convert ECEF to Geodetic
    lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)
    
    # Calculate magnitudes
    eci_magnitude = math.sqrt(x_eci**2 + y_eci**2 + z_eci**2)
    ecef_magnitude = math.sqrt(x_ecef**2 + y_ecef**2 + z_ecef**2)
    
    return {
        'satellite': satellite_name,
        'time': {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'second': second,
            'julian_date': jd
        },
        'gmst': {
            'radians': gmst,
            'degrees': math.degrees(gmst)
        },
        'eci': {
            'x': x_eci,
            'y': y_eci,
            'z': z_eci,
            'magnitude': eci_magnitude
        },
        'ecef': {
            'x': x_ecef,
            'y': y_ecef,
            'z': z_ecef,
            'magnitude': ecef_magnitude
        },
        'geodetic': {
            'latitude': lat,
            'longitude': lon,
            'altitude': alt
        },
        'tle_line1': line1,
        'tle_line2': line2
    }

def print_separator(char='=', length=70):
    print(char * length)

def main():
    print_separator()
    print("ECI to Geodetic Conversion - MicroPython")
    print_separator()
    print()
    
    satellites = ["ISS", "HUBBLE"]
    
    for sat_name in satellites:
        try:
            print_separator()
            print(f"Satellite: {sat_name}")
            print_separator()
            
            result = compute_satellite_position(sat_name)
            
            t = result['time']
            print(f"\nTime: {t['year']:04d}-{t['month']:02d}-{t['day']:02d} "
                  f"{t['hour']:02d}:{t['minute']:02d}:{t['second']:06.3f} UTC")
            print(f"Julian Date: {t['julian_date']:.6f}")
            
            gmst = result['gmst']
            print(f"GMST: {gmst['degrees']:.4f}° ({gmst['radians']:.6f} rad)")
            print()
            
            print("ECI Position (km):")
            eci = result['eci']
            print(f"  X: {eci['x']:>12.3f}")
            print(f"  Y: {eci['y']:>12.3f}")
            print(f"  Z: {eci['z']:>12.3f}")
            print(f"  Magnitude: {eci['magnitude']:>12.3f}")
            print()
            
            print("ECEF Position (km):")
            ecef = result['ecef']
            print(f"  X: {ecef['x']:>12.3f}")
            print(f"  Y: {ecef['y']:>12.3f}")
            print(f"  Z: {ecef['z']:>12.3f}")
            print(f"  Magnitude: {ecef['magnitude']:>12.3f}")
            print()
            
            print("Geodetic Coordinates:")
            geo = result['geodetic']
            print(f"  Latitude:  {geo['latitude']:>9.4f}°")
            print(f"  Longitude: {geo['longitude']:>9.4f}°")
            print(f"  Altitude:  {geo['altitude']:>9.3f} km")
            print()
            
            print("TLE Data:")
            print(f"  Line 1: {result['tle_line1']}")
            print(f"  Line 2: {result['tle_line2']}")
            print()
            
        except Exception as e:
            print(f"Error processing {sat_name}: {e}")
            import sys
            if hasattr(sys, 'print_exception'):
                sys.print_exception(e)
    
    print_separator()
    print("Test complete!")
    print_separator()

if __name__ == "__main__":
    main()
