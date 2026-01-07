"""
Compare existing SGP4 implementation against python-sgp4 reference
"""

from sgp4 import SGP4
import math
from datetime import datetime

# Also compare with reference
from sgp4.api import Satrec, jday

# ISS TLE
line1 = "1 25544U 98067A   25359.56752749  .00014081  00000-0  25591-3 0  9998"
line2 = "2 25544  51.6318  78.9495 0003224 299.9641  60.1027 15.49813539544848"

def calculate_gmst(year, month, day, hour, minute, second):
    """Calculate Greenwich Mean Sidereal Time in radians."""
    # Julian Date
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12*a - 3
    jdn = day + (153*m + 2)//5 + 365*y + y//4 - y//100 + y//400 - 32045
    jd = jdn + (hour - 12)/24 + minute/1440 + second/86400
    
    # GMST calculation
    T = (jd - 2451545.0) / 36525.0
    gmst_deg = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T**2 - T**3 / 38710000.0
    gmst_rad = math.radians(gmst_deg % 360)
    
    return gmst_rad

print("="*70)
print("SGP4 COMPARISON: Our Implementation vs Reference")
print("="*70)

# Current time
now = datetime.utcnow()
year, month, day = now.year, now.month, now.day
hour, minute, second = now.hour, now.minute, now.second

print(f"\nTime: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d} UTC")

# Calculate GMST
gmst = calculate_gmst(year, month, day, hour, minute, second)
print(f"GMST: {math.degrees(gmst):.2f}°")

# Parse TLE for our implementation
epoch_year = int(line1[18:20])
if epoch_year < 57:
    epoch_year += 2000
else:
    epoch_year += 1900

epoch_day = float(line1[20:32])
bstar = float(line1[53:59]) * 10.0 ** float(line1[59:61])
inc = float(line2[8:16])
raan = float(line2[17:25])
ecc = float('0.' + line2[26:33])
argp = float(line2[34:42])
m = float(line2[43:51])
n = float(line2[52:63])

# Our SGP4
sgp = SGP4()
sgp.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)

# Calculate time since epoch in minutes
# Simplified: assume epoch is close to now
t_min = 0.0  # At epoch for now

x, y, z = sgp.propagate(t_min)
lat, lon, alt = sgp.eci_to_geodetic(x, y, z, gmst)

print("\n" + "="*70)
print("OUR SGP4:")
print("="*70)
print(f"  ECI Position: ({x:.1f}, {y:.1f}, {z:.1f}) km")
print(f"  Latitude:     {math.degrees(lat):7.3f}°")
print(f"  Longitude:    {math.degrees(lon):8.3f}°")
print(f"  Altitude:     {alt:6.1f} km")

# Reference SGP4
jd, fr = jday(year, month, day, hour, minute, second)
satellite = Satrec.twoline2rv(line1, line2)
e, r, v = satellite.sgp4(jd, fr)

if e == 0:
    sat_r_mag = math.sqrt(r[0]**2 + r[1]**2 + r[2]**2)
    altitude_km = sat_r_mag - 6378.137
    lat_rad = math.asin(r[2] / sat_r_mag)
    lon_rad = math.atan2(r[1], r[0])
    sat_lat = math.degrees(lat_rad)
    sat_lon = math.degrees(lon_rad)
    
    print("\n" + "="*70)
    print("REFERENCE SGP4 (python-sgp4):")
    print("="*70)
    print(f"  ECI Position: ({r[0]:.1f}, {r[1]:.1f}, {r[2]:.1f}) km")
    print(f"  Latitude:     {sat_lat:7.3f}°")
    print(f"  Longitude:    {sat_lon:8.3f}°")
    print(f"  Altitude:     {altitude_km:6.1f} km")
    
    # Calculate errors
    print("\n" + "="*70)
    print("ACCURACY ANALYSIS:")
    print("="*70)
    
    pos_error = math.sqrt((x-r[0])**2 + (y-r[1])**2 + (z-r[2])**2)
    lat_error = abs(math.degrees(lat) - sat_lat)
    lon_error = abs(math.degrees(lon) - sat_lon)
    if lon_error > 180:
        lon_error = 360 - lon_error
    alt_error = abs(alt - altitude_km)
    
    print(f"  Position error: {pos_error:.1f} km")
    print(f"  Latitude error:  {lat_error:.3f}° ({lat_error*111:.1f} km)")
    print(f"  Longitude error: {lon_error:.3f}° ({lon_error*111*math.cos(lat_rad):.1f} km)")
    print(f"  Altitude error:  {alt_error:.1f} km")
    
    if pos_error < 10:
        print("\n✓ EXCELLENT: Our SGP4 matches reference within 10km!")
    elif pos_error < 50:
        print("\n✓ GOOD: Our SGP4 matches reference within 50km")
    elif pos_error < 100:
        print("\n⚠ FAIR: Our SGP4 has ~100km error")
    else:
        print(f"\n✗ POOR: Our SGP4 has {pos_error:.0f}km error")
else:
    print(f"\nReference SGP4 error code: {e}")
