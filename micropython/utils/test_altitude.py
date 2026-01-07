
import math
import sgp4
import orb_utils as utils

# ISS TLE (from user logs)
name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   25360.74358509  .00010427  00000-0  18897-3 0  9993"
line2 = "2 25544  51.6425 158.5524 0005705  78.6811  68.4947 15.49864295535606"

# Parse manually to verify inputs
epoch_year = int(line1[18:20]) # 25
if epoch_year < 57: epoch_year += 2000
else: epoch_year += 1900
epoch_day = float(line1[20:32]) # 360.74358509

bstar_str = line1[53:59]
bstar_exp = line1[59:61]
bstar = float(bstar_str) * 10.0 ** float(bstar_exp)

inc = float(line2[8:16])
raan = float(line2[17:25])
ecc = float('0.' + line2[26:33])
argp = float(line2[34:42])
m = float(line2[43:51])
n = float(line2[52:63])

print(f"Inputs: Epoch={epoch_year}/{epoch_day}, Inc={inc}, Ecc={ecc}, N={n}")

# Init SGP4
sat = sgp4.SGP4()
sat.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)

# Actually just print aodp (semi-major axis in ER)
print(f"AoDP (ER): {sat.aodp}")
print(f"XKMPER: {sgp4.XKMPER}")

# Propagate at t=0 (Epoch)
x, y, z = sat.propagate(0.0)
print(f"Pos (km): {x:.2f}, {y:.2f}, {z:.2f}")

r = math.sqrt(x*x + y*y + z*z)
print(f"Magnitude R (km): {r:.2f}")
expected_alt = r - 6378.137
print(f"Simple Alt (R - Re): {expected_alt:.2f}")

# Geodetic
lat, lon, alt = sat.eci_to_geodetic(x, y, z, 0.0)
print(f"Geodetic Alt: {alt:.2f} km")
