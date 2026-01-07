#!/usr/bin/env python3
"""
Final Verification: Compare Pico2W result at a specific timestamp with Standard SGP4
"""
from sgp4.api import Satrec, jday
import math

# TLE from cache
line1 = "1 25544U 98067A   26003.53276902  .00013553  00000+0  25297-3 0  9999"
line2 = "2 25544  51.6327  34.5663 0007560 336.0107  24.0528 15.49066978546237"

# Pico result at 21:23:27 UTC
pico_time = (2026, 1, 3, 21, 23, 27)
pico_lat = -15.474
pico_lon = 161.758

# Standard SGP4 at same time
satellite = Satrec.twoline2rv(line1, line2)
jd, fr = jday(pico_time[0], pico_time[1], pico_time[2], pico_time[3], pico_time[4], pico_time[5])

# GMST
T = (jd + fr - 2451545.0) / 36525.0
gmst_sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * T + 0.093104 * T**2 - 6.2e-6 * T**3
gmst = math.radians((gmst_sec / 240.0) % 360.0)

error_code, pos, vel = satellite.sgp4(jd, fr)

# ECI to ECEF to Geodetic
cos_gmst, sin_gmst = math.cos(gmst), math.sin(gmst)
x_ecef = cos_gmst * pos[0] + sin_gmst * pos[1]
y_ecef = -sin_gmst * pos[0] + cos_gmst * pos[1]
z_ecef = pos[2]

a, f, e2 = 6378.137, 1.0/298.257223563, 2*(1.0/298.257223563) - (1.0/298.257223563)**2
lon_rad = math.atan2(y_ecef, x_ecef)
p = math.sqrt(x_ecef**2 + y_ecef**2)
lat_rad = math.atan2(z_ecef, p * (1.0 - e2))

for _ in range(5):
    sin_lat = math.sin(lat_rad)
    N = a / math.sqrt(1.0 - e2 * sin_lat**2)
    alt = p / math.cos(lat_rad) - N
    lat_rad = math.atan2(z_ecef, p * (1.0 - e2 * N / (N + alt)))

std_lat = math.degrees(lat_rad)
std_lon = math.degrees(lon_rad)

print(f"Time: 2026-01-03 21:23:27 UTC")
print()
print(f"Standard SGP4: Lat: {std_lat:>8.3f}° Lon: {std_lon:>9.3f}°")
print(f"Pico2W Result: Lat: {pico_lat:>8.3f}° Lon: {pico_lon:>9.3f}°")
print()

diff_lat = std_lat - pico_lat
diff_lon = std_lon - pico_lon

lat_km = diff_lat * 111.0
lon_km = diff_lon * 111.0 * math.cos(math.radians(std_lat))
dist = math.sqrt(lat_km**2 + lon_km**2)

print(f"Error: {dist:.1f} km")
