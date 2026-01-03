"""
SGP4 MicroPython Test - Compute ECI coordinates using micropython sgp4 library
This script can be run on the Pico2W or tested locally with micropython
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
    # Temporarily disable checksum validation
    original_verify = tle_parser._verify_checksum
    tle_parser._verify_checksum = lambda x: True
    try:
        result = tle_parser.parse_tle(line1, line2)
    finally:
        tle_parser._verify_checksum = original_verify
    return result

def load_tle_from_cache(satellite_name="ISS"):
    """Load TLE data from the cache file"""
    # Always use the absolute path to ensure we get the right file
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

def compute_eci_position(satellite_name="ISS", use_current_time=True):
    """
    Compute ECI coordinates for a satellite using MicroPython SGP4
    
    Args:
        satellite_name: Name of satellite in TLE cache
        use_current_time: If True, use current UTC time
    
    Returns:
        dict with position (km), time info, and TLE data
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
    
    # Propagate to current time
    x, y, z = sgp4.propagate(t_min)
    
    # Calculate magnitude
    pos_magnitude = math.sqrt(x*x + y*y + z*z)
    
    # Calculate altitude
    EARTH_RADIUS = 6378.137  # km
    altitude = pos_magnitude - EARTH_RADIUS
    
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
        'epoch': {
            'year': tle['epoch_year'],
            'day': tle['epoch_day'],
            'julian_date': epoch_jd
        },
        'time_since_epoch_min': t_min,
        'position_eci_km': {
            'x': x,
            'y': y,
            'z': z,
            'magnitude': pos_magnitude
        },
        'altitude_km': altitude,
        'tle': {
            'inclination': tle['inclination'],
            'raan': tle['raan'],
            'eccentricity': tle['eccentricity'],
            'arg_perigee': tle['arg_perigee'],
            'mean_anomaly': tle['mean_anomaly'],
            'mean_motion': tle['mean_motion']
        },
        'tle_line1': line1,
        'tle_line2': line2
    }

def eci_to_lat_lon_alt(x, y, z):
    """
    Convert ECI coordinates to latitude, longitude, altitude
    Note: This is a simplified conversion that doesn't account for Earth's rotation
    For accurate lat/lon, you need to convert ECI to ECEF first using GMST
    """
    # Earth radius in km
    EARTH_RADIUS = 6378.137
    
    # Calculate magnitude
    r = math.sqrt(x*x + y*y + z*z)
    
    # Altitude
    altitude = r - EARTH_RADIUS
    
    # Latitude (geocentric)
    latitude = math.degrees(math.asin(z / r))
    
    # Longitude (this is ECI longitude, not geographic!)
    longitude = math.degrees(math.atan2(y, x))
    
    return latitude, longitude, altitude

def print_separator(char='=', length=70):
    print(char * length)

def main():
    print_separator()
    print("SGP4 MicroPython Test - ECI Coordinate Calculation")
    print_separator()
    print()
    
    # Test with ISS and HUBBLE
    satellites = ["ISS", "HUBBLE"]
    
    for sat_name in satellites:
        try:
            print_separator()
            print(f"Satellite: {sat_name}")
            print_separator()
            
            result = compute_eci_position(sat_name)
            
            t = result['time']
            print(f"\nTime: {t['year']:04d}-{t['month']:02d}-{t['day']:02d} "
                  f"{t['hour']:02d}:{t['minute']:02d}:{t['second']:06.3f} UTC")
            print(f"Julian Date: {t['julian_date']:.6f}")
            print(f"Time since epoch: {result['time_since_epoch_min']:.2f} minutes")
            print()
            
            print("ECI Position (km):")
            pos = result['position_eci_km']
            print(f"  X: {pos['x']:>12.3f}")
            print(f"  Y: {pos['y']:>12.3f}")
            print(f"  Z: {pos['z']:>12.3f}")
            print(f"  Magnitude: {pos['magnitude']:>12.3f}")
            print(f"  Altitude:  {result['altitude_km']:>12.3f}")
            print()
            
            # Convert to lat/lon (simplified - ECI frame)
            lat, lon, alt = eci_to_lat_lon_alt(pos['x'], pos['y'], pos['z'])
            
            print("Approximate Geodetic (ECI frame - not accounting for Earth rotation):")
            print(f"  Latitude:  {lat:>8.3f}°")
            print(f"  Longitude: {lon:>8.3f}° (ECI, not geographic!)")
            print(f"  Altitude:  {alt:>8.3f} km")
            print()
            
            print("TLE Orbital Elements:")
            tle = result['tle']
            print(f"  Inclination:  {tle['inclination']:>8.4f}°")
            print(f"  RAAN:         {tle['raan']:>8.4f}°")
            print(f"  Eccentricity: {tle['eccentricity']:>10.7f}")
            print(f"  Arg Perigee:  {tle['arg_perigee']:>8.4f}°")
            print(f"  Mean Anomaly: {tle['mean_anomaly']:>8.4f}°")
            print(f"  Mean Motion:  {tle['mean_motion']:>8.5f} rev/day")
            print()
            
            print("TLE Data:")
            print(f"  Line 1: {result['tle_line1']}")
            print(f"  Line 2: {result['tle_line2']}")
            print()
            
        except Exception as e:
            print(f"Error processing {sat_name}: {e}")
            import sys
            sys.print_exception(e) if hasattr(sys, 'print_exception') else None
    
    print_separator()
    print("Test complete!")
    print_separator()

if __name__ == "__main__":
    main()
