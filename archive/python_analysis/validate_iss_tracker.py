#!/usr/bin/env python3
"""
Compare MicroPython SGP4 output to reference ISS tracker
Reference: 28.80°N, 126.42°E, 265 miles (426.5 km) at 21:08:17 UTC
"""

import sys
sys.path.insert(0, '/home/justin/code/orbigator/micropython')

from sgp4 import SGP4
import tle_parser
import satellite_position
import math

# Reference data from tracker (converted to km)
REF_LAT = 28.80  # degrees North
REF_LON = 126.42  # degrees East
REF_ALT = 265 * 1.60934  # miles to km = 426.5 km
REF_TIME = (2026, 1, 3, 21, 8, 17)  # UTC

# Current TLE from CelesTrak (same as in cache)
line1 = "1 25544U 98067A   26003.53276902  .00013553  00000+0  25297-3 0  9999"
line2 = "2 25544  51.6327  34.5663 0007560 336.0107  24.0528 15.49066978546237"

def parse_tle_skip_checksum(line1, line2):
    """Parse TLE without checksum validation"""
    original_verify = tle_parser._verify_checksum
    tle_parser._verify_checksum = lambda x: True
    try:
        result = tle_parser.parse_tle(line1, line2)
    finally:
        tle_parser._verify_checksum = original_verify
    return result

def main():
    print("=" * 70)
    print("ISS Position Validation - MicroPython SGP4 vs Reference Tracker")
    print("=" * 70)
    print()
    
    # Parse TLE
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
    
    # Compute position at reference time
    result = satellite_position.compute_satellite_geodetic(
        sgp4, tle['epoch_year'], tle['epoch_day'], REF_TIME
    )
    
    print("Reference Tracker (21:08:17 UTC):")
    print(f"  Latitude:  {REF_LAT:>9.4f}°N")
    print(f"  Longitude: {REF_LON:>9.4f}°E")
    print(f"  Altitude:  {REF_ALT:>9.3f} km (265 miles)")
    print()
    
    print("MicroPython SGP4 Calculation:")
    print(f"  Latitude:  {result['latitude']:>9.4f}°")
    print(f"  Longitude: {result['longitude']:>9.4f}°")
    print(f"  Altitude:  {result['altitude']:>9.3f} km")
    print()
    
    # Calculate differences
    diff_lat = result['latitude'] - REF_LAT
    diff_lon = result['longitude'] - REF_LON
    diff_alt = result['altitude'] - REF_ALT
    
    print("Differences (MicroPython - Reference):")
    print(f"  ΔLatitude:  {diff_lat:>9.4f}°")
    print(f"  ΔLongitude: {diff_lon:>9.4f}°")
    print(f"  ΔAltitude:  {diff_alt:>9.3f} km")
    print()
    
    # Calculate distance error
    # Convert lat/lon difference to km
    lat_km = diff_lat * 111.0  # 1 degree latitude ≈ 111 km
    lon_km = diff_lon * 111.0 * math.cos(math.radians(REF_LAT))  # longitude varies with latitude
    
    horizontal_error = math.sqrt(lat_km**2 + lon_km**2)
    total_error = math.sqrt(horizontal_error**2 + diff_alt**2)
    
    print("Error Estimates:")
    print(f"  Horizontal: {horizontal_error:>9.3f} km")
    print(f"  Vertical:   {abs(diff_alt):>9.3f} km")
    print(f"  Total 3D:   {total_error:>9.3f} km")
    print()
    
    print("=" * 70)
    
    # Determine accuracy
    if total_error < 10:
        print("✓ EXCELLENT: Total error < 10 km")
    elif total_error < 50:
        print("✓ GOOD: Total error < 50 km")
    elif total_error < 100:
        print("⚠ ACCEPTABLE: Total error < 100 km")
    else:
        print("✗ POOR: Total error > 100 km")
    
    print("=" * 70)
    print()
    
    # Show ECI coordinates for debugging
    print("Debug Info:")
    print(f"  ECI X: {result['eci']['x']:>12.3f} km")
    print(f"  ECI Y: {result['eci']['y']:>12.3f} km")
    print(f"  ECI Z: {result['eci']['z']:>12.3f} km")
    print(f"  GMST:  {math.degrees(result['gmst']):>9.4f}°")
    print()

if __name__ == "__main__":
    main()
