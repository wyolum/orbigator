"""
Simple SGP4 test for Pico 2W
"""

from sgp4 import SGP4
import math

# ISS TLE
line1 = "1 25544U 98067A   25359.56752749  .00014081  00000-0  25591-3 0  9998"
line2 = "2 25544  51.6318  78.9495 0003224 299.9641  60.1027 15.49813539544848"

print("="*60)
print("SGP4 Test on Pico 2W")
print("="*60)

# Parse TLE
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

print(f"\nISS TLE:")
print(f"  Epoch: {epoch_year} day {epoch_day:.2f}")
print(f"  Inclination: {inc:.4f}°")
print(f"  Mean Motion: {n:.8f} rev/day")

# Initialize SGP4
sgp = SGP4()
sgp.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)

# Propagate (at epoch for now)
t_min = 0.0
x, y, z = sgp.propagate(t_min)

r_mag = math.sqrt(x**2 + y**2 + z**2)
alt = r_mag - 6378.137

print(f"\nPosition at epoch:")
print(f"  X = {x:.1f} km")
print(f"  Y = {y:.1f} km")
print(f"  Z = {z:.1f} km")
print(f"  Altitude: {alt:.1f} km")

# Convert to lat/lon (simplified GMST=0)
gmst = 0.0
lat, lon, alt_geo = sgp.eci_to_geodetic(x, y, z, gmst)

print(f"\nGeodetic (GMST=0):")
print(f"  Lat: {math.degrees(lat):.3f}°")
print(f"  Lon: {math.degrees(lon):.3f}°")
print(f"  Alt: {alt_geo:.1f} km")

print("\n✓ SGP4 working on Pico 2W!")
