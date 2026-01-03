"""
ISS Position Test for Pico2W
Prints datetime and ISS lat/lon using the IMPROVED geodetic conversion
Run this on the Pico2W to compare with live ISS tracker
"""

import time
import json
from sgp4 import SGP4
import satellite_position

# Load TLE from cache
with open('tle_cache.json', 'r') as f:
    cache = json.load(f)

line1 = cache['ISS']['line1']
line2 = cache['ISS']['line2']

# Parse TLE (simplified - skip full parser)
# Extract key values from TLE
epoch_year = int(line1[18:20])
if epoch_year < 57:
    epoch_year += 2000
else:
    epoch_year += 1900
epoch_day = float(line1[20:32])

inclination = float(line2[8:16])
raan = float(line2[17:25])
eccentricity = float('0.' + line2[26:33])
arg_perigee = float(line2[34:42])
mean_anomaly = float(line2[43:51])
mean_motion = float(line2[52:63])
bstar_str = line1[53:61].strip()
# Simple bstar parsing
if '-' in bstar_str[1:]:
    parts = bstar_str.split('-')
    bstar = float(parts[0]) * (10.0 ** -int(parts[1]))
else:
    bstar = 0.0

# Initialize SGP4
sgp4 = SGP4()
sgp4.init(
    epoch_year=epoch_year,
    epoch_day=epoch_day,
    bstar=bstar,
    inc=inclination,
    raan=raan,
    ecc=eccentricity,
    argp=arg_perigee,
    m=mean_anomaly,
    n=mean_motion
)

print("ISS Position Monitor - Press Ctrl+C to stop")
print("=" * 60)

try:
    while True:
        # Get current time (9-tuple)
        t = time.gmtime()
        
        # Compute position using IMPROVED geodetic conversion
        result = satellite_position.compute_satellite_geodetic(
            sgp4, epoch_year, epoch_day, t
        )
        
        # Print in easy-to-compare format
        eci = result.get('eci', {})
        print(f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d} UTC | "
              f"Lat: {result['latitude']:>7.3f}° | "
              f"Lon: {result['longitude']:>8.3f}° | "
              f"t_min: {result.get('t_min', 0):>8.2f}")
        print(f"ECI: ({eci.get('x',0):>9.3f}, {eci.get('y',0):>9.3f}, {eci.get('z',0):>9.3f}) | Alt: {result['altitude']:>6.1f} km")
        
        # Update every 5 seconds
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\nStopped")
