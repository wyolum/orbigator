#!/usr/bin/env python3
"""
ECI to Geodetic Conversion using Standard Python Libraries
Uses sgp4 library for satellite propagation and coordinate conversion
"""

from sgp4.api import Satrec, jday
from sgp4 import earth_gravity
from datetime import datetime, timezone
import json
import math

def load_tle_from_cache(satellite_name="ISS"):
    """Load TLE data from the cache file"""
    with open('/home/justin/code/orbigator/micropython/tle_cache.json', 'r') as f:
        cache = json.load(f)
    
    if satellite_name not in cache:
        raise ValueError(f"Satellite {satellite_name} not found in cache")
    
    tle_data = cache[satellite_name]
    return tle_data['line1'], tle_data['line2']

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

def compute_satellite_position(satellite_name="ISS"):
    """
    Compute satellite position in both ECI and geodetic coordinates
    
    Returns:
        dict with ECI position, ECEF position, and geodetic coordinates
    """
    # Load TLE
    line1, line2 = load_tle_from_cache(satellite_name)
    
    # Create satellite object
    satellite = Satrec.twoline2rv(line1, line2)
    
    # Get current time
    dt = datetime.now(timezone.utc)
    
    # Convert to Julian date
    jd, fr = jday(dt.year, dt.month, dt.day, 
                  dt.hour, dt.minute, dt.second + dt.microsecond/1e6)
    
    # Propagate satellite to current time
    error_code, position, velocity = satellite.sgp4(jd, fr)
    
    if error_code != 0:
        raise RuntimeError(f"SGP4 propagation error: {error_code}")
    
    x_eci, y_eci, z_eci = position
    
    # Calculate GMST
    gmst = gmst_from_jd(jd + fr)
    
    # Convert ECI to ECEF
    x_ecef, y_ecef, z_ecef = eci_to_ecef(x_eci, y_eci, z_eci, gmst)
    
    # Convert ECEF to Geodetic
    lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)
    
    # Calculate magnitudes
    eci_magnitude = math.sqrt(x_eci**2 + y_eci**2 + z_eci**2)
    ecef_magnitude = math.sqrt(x_ecef**2 + y_ecef**2 + z_ecef**2)
    
    return {
        'satellite': satellite_name,
        'datetime': dt.isoformat(),
        'julian_date': jd + fr,
        'gmst_rad': gmst,
        'gmst_deg': math.degrees(gmst),
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
        'velocity_eci': {
            'x': velocity[0],
            'y': velocity[1],
            'z': velocity[2]
        },
        'tle_line1': line1,
        'tle_line2': line2
    }

def main():
    print("=" * 70)
    print("ECI to Geodetic Conversion - Standard Python Libraries")
    print("=" * 70)
    print()
    
    satellites = ["ISS", "HUBBLE"]
    
    for sat_name in satellites:
        try:
            print("=" * 70)
            print(f"Satellite: {sat_name}")
            print("=" * 70)
            
            result = compute_satellite_position(sat_name)
            
            print(f"\nTime: {result['datetime']}")
            print(f"Julian Date: {result['julian_date']:.6f}")
            print(f"GMST: {result['gmst_deg']:.4f}° ({result['gmst_rad']:.6f} rad)")
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
            
            print("ECI Velocity (km/s):")
            vel = result['velocity_eci']
            vel_mag = math.sqrt(vel['x']**2 + vel['y']**2 + vel['z']**2)
            print(f"  X: {vel['x']:>12.6f}")
            print(f"  Y: {vel['y']:>12.6f}")
            print(f"  Z: {vel['z']:>12.6f}")
            print(f"  Magnitude: {vel_mag:>12.6f}")
            print()
            
            print("TLE Data:")
            print(f"  Line 1: {result['tle_line1']}")
            print(f"  Line 2: {result['tle_line2']}")
            print()
            
        except Exception as e:
            print(f"Error processing {sat_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 70)

if __name__ == "__main__":
    main()
