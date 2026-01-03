"""
Satellite Position Calculator for Pico2W
Computes geodetic coordinates (lat/lon/alt) from TLE data

This is a deployment-ready version for the Pico2W that can be imported
and used by other modules.
"""

import json
import math
import time
from sgp4 import SGP4

def compute_julian_date(year, month, day, hour=0, minute=0, second=0):
    """
    Compute Julian Date from calendar date.
    Note: For precise time offsets on 32-bit MicroPython, avoid using JD 
    subtraction. Use Unix timestamps instead.
    """
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    jd += (hour + (minute + second / 60.0) / 60.0) / 24.0
    return jd

def gmst_from_unix(unix_timestamp):
    """
    Calculate Greenwich Mean Sidereal Time from Unix timestamp.
    Uses integer math for the primary offset to maintain precision on 32-bit floats.
    """
    # J2000.0 is Jan 1 2000 12:00:00 UTC (946728000 in 1970 epoch)
    J2000_UNIX = 946728000
    
    # Seconds since J2000.0 (integer)
    s_since_j2000 = int(unix_timestamp) - J2000_UNIX
    
    d_int = s_since_j2000 // 86400
    s_rem = s_since_j2000 % 86400
    # d_frac is the fractional day [0, 1.0)
    d_frac = s_rem / 86400.0
    
    # Meeus GMST formula (accurate to 0.02 seconds over 50 years)
    d = d_int + d_frac
    gmst_deg = (280.46061837 + 360.98564736629 * d) % 360.0
    
    return math.radians(gmst_deg)

def eci_to_ecef(x_eci, y_eci, z_eci, gmst):
    """Convert ECI coordinates to ECEF (Earth-Centered Earth-Fixed)"""
    cos_gmst = math.cos(gmst)
    sin_gmst = math.sin(gmst)
    
    x_ecef = cos_gmst * x_eci + sin_gmst * y_eci
    y_ecef = -sin_gmst * x_eci + cos_gmst * y_eci
    z_ecef = z_eci
    
    return x_ecef, y_ecef, z_ecef

def ecef_to_geodetic(x, y, z):
    """
    Convert ECEF coordinates to geodetic (lat, lon, alt)
    Uses WGS-84 ellipsoid model
    
    Returns:
        lat, lon, alt: Latitude (deg), Longitude (deg), Altitude (km)
    """
    # WGS-84 constants
    a = 6378.137  # Semi-major axis (km)
    f = 1.0 / 298.257223563  # Flattening
    e2 = 2*f - f*f  # Eccentricity squared
    
    lon = math.atan2(y, x)
    p = math.sqrt(x*x + y*y)
    lat = math.atan2(z, p * (1.0 - e2))
    
    # Iterative refinement
    for _ in range(5):
        sin_lat = math.sin(lat)
        N = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
        alt = p / math.cos(lat) - N
        lat = math.atan2(z, p * (1.0 - e2 * N / (N + alt)))
    
    # Final altitude
    sin_lat = math.sin(lat)
    N = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    alt = p / math.cos(lat) - N
    
    return math.degrees(lat), math.degrees(lon), alt

def compute_satellite_geodetic(sgp4_obj, tle_epoch_year, tle_epoch_day, current_time_tuple=None):
    """
    Compute satellite geodetic position from SGP4 object
    
    Args:
        sgp4_obj: Initialized SGP4 object
        tle_epoch_year: TLE epoch year (4-digit)
        tle_epoch_day: TLE epoch day (fractional day of year)
        current_time_tuple: (year, month, day, hour, minute, second) or None for current time
    
    Returns:
        dict with 'latitude', 'longitude', 'altitude', 'eci', 'ecef', 'gmst'
    """
    # Get current time
    if current_time_tuple is None:
        t = time.gmtime()
        current_time_tuple = (t[0], t[1], t[2], t[3], t[4], t[5])
    
    # Compute Unix timestamp for current_time_tuple
    if len(current_time_tuple) < 9:
        # Pad with 0s for wday, yday, isdst if needed
        tmp = list(current_time_tuple)
        while len(tmp) < 9:
            tmp.append(0)
        current_time_tuple = tuple(tmp)
        
    unix_now = time.mktime(current_time_tuple)
    
    # Compute Unix timestamp for TLE epoch
    # Start with Jan 1st of epoch year
    epoch_jan1_jd = compute_julian_date(tle_epoch_year, 1, 1, 0, 0, 0)
    # JD 1970 is 2440587.5
    epoch_jan1_unix = int((epoch_jan1_jd - 2440587.5) * 86400.0)
    
    # Add day of year (tle_epoch_day is 1-indexed for Jan 1st)
    epoch_unix = epoch_jan1_unix + int((tle_epoch_day - 1.0) * 86400.0)
    
    # Calculate minutes since epoch using integer subtraction for precision
    t_min = (int(unix_now) - epoch_unix) / 60.0
    
    # Propagate to current time (returns ECI coordinates)
    x_eci, y_eci, z_eci = sgp4_obj.propagate(t_min)
    
    # Calculate GMST using integer-safe approach
    gmst = gmst_from_unix(unix_now)
    
    # Convert ECI to ECEF
    x_ecef, y_ecef, z_ecef = eci_to_ecef(x_eci, y_eci, z_eci, gmst)
    
    # Convert ECEF to Geodetic
    lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)
    
    return {
        'latitude': lat,
        'longitude': lon,
        'altitude': alt,
        't_min': t_min,
        'eci': {'x': x_eci, 'y': y_eci, 'z': z_eci},
        'ecef': {'x': x_ecef, 'y': y_ecef, 'z': z_ecef},
        'gmst': gmst
    }

# Example usage for testing
if __name__ == "__main__":
    # This is just for testing - in production, import this module
    print("Satellite Position Calculator")
    print("Import this module to use compute_satellite_geodetic()")
