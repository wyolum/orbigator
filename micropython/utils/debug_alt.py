
import sgp4
import satellite_position
import time
import math

# ISS TLE from user log
line1 = "1 25544U 98067A   26003.53051499  .00010045  00000+0  17992-3 0  9997"
line2 = "2 25544  51.6416 195.4678 0005462 268.0862  41.5164 15.50066223490076"

def debug_calc():
    print("Debugging SGP4 Altitude...")
    
    # Parse
    import orb_utils as utils
    epoch_year, epoch_day = utils.parse_tle_epoch(line1)
    bstar = float(line1[53:59]) * 10.0 ** float(line1[59:61])
    inc = float(line2[8:16])
    raan = float(line2[17:25])
    ecc = float('0.' + line2[26:33])
    argp = float(line2[34:42])
    m = float(line2[43:51])
    n = float(line2[52:63])
    
    print(f"n (revs/day): {n}")
    
    # Init SGP4
    sat = sgp4.SGP4()
    sat.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)
    
    print(f"sat.n (rad/min): {sat.n}")
    print(f"sat.aodp (ER): {sat.aodp}")
    print(f"Typical Earth Radius: 6378.135 km")
    print(f"Expected Semi-Major Axis: {sat.aodp * 6378.135} km")
    
    # Propagate
    t_min = 0 # Epoch
    x, y, z = sat.propagate(t_min)
    r = math.sqrt(x*x + y*y + z*z)
    print(f"Pos @ t=0 (ECI km): {x:.2f}, {y:.2f}, {z:.2f}")
    print(f"Magnitude r: {r:.2f} km")
    print(f"Approx Alt (r - 6378): {r - 6378.135:.2f} km")
    
    # Full Geodetic
    res = satellite_position.compute_satellite_geodetic(sat, epoch_year, epoch_day)
    print(f"Computed Alt: {res['altitude']:.2f} km")
    print(f"Computed Lat: {res['latitude']:.2f}")
    print(f"Computed Lon: {res['longitude']:.2f}")

if __name__ == "__main__":
    debug_calc()
