#!/usr/bin/env python3
"""
SGP4 Desktop Test - Compute ECI coordinates using standard sgp4 library
Run with: conda activate the_basics && python sgp4_desktop_test.py
"""

from sgp4.api import Satrec, jday
from datetime import datetime, timezone
import json
import math

def load_tle_from_cache(satellite_name="ISS"):
    """Load TLE data from the cache file"""
    with open('micropython/tle_cache.json', 'r') as f:
        cache = json.load(f)
    
    if satellite_name not in cache:
        raise ValueError(f"Satellite {satellite_name} not found in cache")
    
    tle_data = cache[satellite_name]
    return tle_data['line1'], tle_data['line2']

def compute_eci_position(satellite_name="ISS", use_current_time=True, custom_datetime=None):
    """
    Compute ECI coordinates for a satellite using SGP4
    
    Args:
        satellite_name: Name of satellite in TLE cache
        use_current_time: If True, use current UTC time
        custom_datetime: Optional datetime object to use instead
    
    Returns:
        dict with position (km), velocity (km/s), and time info
    """
    # Load TLE
    line1, line2 = load_tle_from_cache(satellite_name)
    
    # Create satellite object
    satellite = Satrec.twoline2rv(line1, line2)
    
    # Get time
    if custom_datetime:
        dt = custom_datetime
    elif use_current_time:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    
    # Convert to Julian date
    jd, fr = jday(dt.year, dt.month, dt.day, 
                  dt.hour, dt.minute, dt.second + dt.microsecond/1e6)
    
    # Propagate satellite to current time
    error_code, position, velocity = satellite.sgp4(jd, fr)
    
    if error_code != 0:
        raise RuntimeError(f"SGP4 propagation error: {error_code}")
    
    # Calculate magnitude
    pos_magnitude = math.sqrt(position[0]**2 + position[1]**2 + position[2]**2)
    vel_magnitude = math.sqrt(velocity[0]**2 + velocity[1]**2 + velocity[2]**2)
    
    return {
        'satellite': satellite_name,
        'datetime': dt.isoformat(),
        'julian_date': jd + fr,
        'position_eci_km': {
            'x': position[0],
            'y': position[1],
            'z': position[2],
            'magnitude': pos_magnitude
        },
        'velocity_eci_km_s': {
            'x': velocity[0],
            'y': velocity[1],
            'z': velocity[2],
            'magnitude': vel_magnitude
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
    r = math.sqrt(x**2 + y**2 + z**2)
    
    # Altitude
    altitude = r - EARTH_RADIUS
    
    # Latitude (geocentric)
    latitude = math.degrees(math.asin(z / r))
    
    # Longitude (this is ECI longitude, not geographic!)
    longitude = math.degrees(math.atan2(y, x))
    
    return latitude, longitude, altitude

def main():
    print("=" * 70)
    print("SGP4 Desktop Test - ECI Coordinate Calculation")
    print("=" * 70)
    print()
    
    # Test with ISS
    satellites = ["ISS", "HUBBLE"]
    
    for sat_name in satellites:
        try:
            print(f"\n{'=' * 70}")
            print(f"Satellite: {sat_name}")
            print(f"{'=' * 70}")
            
            result = compute_eci_position(sat_name)
            
            print(f"\nTime: {result['datetime']}")
            print(f"Julian Date: {result['julian_date']:.6f}")
            print()
            
            print("ECI Position (km):")
            print(f"  X: {result['position_eci_km']['x']:>12.3f}")
            print(f"  Y: {result['position_eci_km']['y']:>12.3f}")
            print(f"  Z: {result['position_eci_km']['z']:>12.3f}")
            print(f"  Magnitude: {result['position_eci_km']['magnitude']:>12.3f}")
            print()
            
            print("ECI Velocity (km/s):")
            print(f"  X: {result['velocity_eci_km_s']['x']:>12.6f}")
            print(f"  Y: {result['velocity_eci_km_s']['y']:>12.6f}")
            print(f"  Z: {result['velocity_eci_km_s']['z']:>12.6f}")
            print(f"  Magnitude: {result['velocity_eci_km_s']['magnitude']:>12.6f}")
            print()
            
            # Convert to lat/lon (simplified - ECI frame)
            lat, lon, alt = eci_to_lat_lon_alt(
                result['position_eci_km']['x'],
                result['position_eci_km']['y'],
                result['position_eci_km']['z']
            )
            
            print("Approximate Geodetic (ECI frame - not accounting for Earth rotation):")
            print(f"  Latitude:  {lat:>8.3f}°")
            print(f"  Longitude: {lon:>8.3f}° (ECI, not geographic!)")
            print(f"  Altitude:  {alt:>8.3f} km")
            print()
            
            print("TLE Data:")
            print(f"  Line 1: {result['tle_line1']}")
            print(f"  Line 2: {result['tle_line2']}")
            
        except Exception as e:
            print(f"Error processing {sat_name}: {e}")
    
    print("\n" + "=" * 70)
    print("Note: For accurate geographic lat/lon, you need to convert ECI to ECEF")
    print("using GMST (Greenwich Mean Sidereal Time) to account for Earth's rotation.")
    print("=" * 70)

if __name__ == "__main__":
    main()
