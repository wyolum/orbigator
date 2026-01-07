#!/usr/bin/env python3
"""
Detailed Plan13 vs SGP4 comparison
"""

from sgp4.api import Satrec, jday
from datetime import datetime
import math

# ISS TLE
line1 = "1 25544U 98067A   25359.56752749  .00014081  00000-0  25591-3 0  9998"
line2 = "2 25544  51.6318  78.9495 0003224 299.9641  60.1027 15.49813539544848"

# Time: 2025-12-25 23:28:24 UTC (from Plan13 output)
now = datetime(2025, 12, 25, 23, 28, 24)
jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)

# SGP4 calculation
satellite = Satrec.twoline2rv(line1, line2)
e, r, v = satellite.sgp4(jd, fr)

if e == 0:
    # Position and velocity in TEME frame
    sat_r_mag = math.sqrt(r[0]**2 + r[1]**2 + r[2]**2)
    altitude_km = sat_r_mag - 6378.137
    
    # Geodetic coordinates
    lat_rad = math.asin(r[2] / sat_r_mag)
    lon_rad = math.atan2(r[1], r[0])
    
    sat_lat = math.degrees(lat_rad)
    sat_lon = math.degrees(lon_rad)
    
    # Normalize longitude to -180..180
    while sat_lon > 180:
        sat_lon -= 360
    while sat_lon < -180:
        sat_lon += 360
    
    print("="*70)
    print("DETAILED COMPARISON: Plan13 vs SGP4")
    print("="*70)
    print(f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    print("SGP4 (Official Standard):")
    print(f"  Latitude:    {sat_lat:8.3f}°")
    print(f"  Longitude:   {sat_lon:8.3f}°")
    print(f"  Altitude:    {altitude_km:7.1f} km")
    print(f"  Position:    ({r[0]:8.1f}, {r[1]:8.1f}, {r[2]:8.1f}) km (TEME)")
    print()
    
    print("Plan13 (from Pico 2W output):")
    plan13_lat = 35.629
    plan13_lon = 135.502
    plan13_alt = 419.4
    print(f"  Latitude:    {plan13_lat:8.3f}°")
    print(f"  Longitude:   {plan13_lon:8.3f}°")
    print(f"  Altitude:    {plan13_alt:7.1f} km")
    print()
    
    # Calculate differences
    lat_diff = abs(sat_lat - plan13_lat)
    
    # Longitude difference accounting for wraparound
    lon_diff = abs(sat_lon - plan13_lon)
    if lon_diff > 180:
        lon_diff = 360 - lon_diff
    
    alt_diff = abs(altitude_km - plan13_alt)
    
    # Convert lat/lon differences to km (approximate)
    lat_diff_km = lat_diff * 111  # 1 degree latitude ≈ 111 km
    lon_diff_km = lon_diff * 111 * math.cos(math.radians(sat_lat))  # Adjusted for latitude
    
    position_error_km = math.sqrt(lat_diff_km**2 + lon_diff_km**2)
    
    print("="*70)
    print("ACCURACY ANALYSIS:")
    print("="*70)
    print(f"  Latitude error:     {lat_diff:6.3f}° ({lat_diff_km:6.1f} km)")
    print(f"  Longitude error:    {lon_diff:6.3f}° ({lon_diff_km:6.1f} km)")
    print(f"  Altitude error:     {alt_diff:6.1f} km")
    print(f"  Horizontal error:   {position_error_km:6.1f} km")
    print()
    
    # Verdict
    if position_error_km < 10 and alt_diff < 10:
        print("✓ EXCELLENT: Plan13 accuracy is within 10km - suitable for Orbigator!")
    elif position_error_km < 50 and alt_diff < 50:
        print("✓ GOOD: Plan13 accuracy is within 50km - acceptable for demonstration")
    elif position_error_km < 100:
        print("⚠ FAIR: Plan13 has ~100km error - may need SGP4 for precision")
    else:
        print("✗ POOR: Plan13 error >100km - SGP4 recommended")
    
else:
    print(f"SGP4 error code: {e}")
