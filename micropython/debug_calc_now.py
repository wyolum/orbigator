
import sys
import time
import math

# Use current directory
sys.path.append(".")

try:
    from sgp4 import SGP4
    from satellite_position import compute_satellite_geodetic
    import orb_utils
except ImportError as e:
    print(f"Error imports: {e}")
    sys.exit(1)

# TLE from Jan 5 2026
TLE1 = "1 25544U 98067A   26005.53262344  .00012388  00000+0  23158-3 0  9995"
TLE2 = "2 25544  51.6326  24.6699 0007562 343.7680  16.3066 15.49114570546545"

# Target Time: 2026-01-06 11:34:12 UTC
TARGET_Tuple = (2026, 1, 6, 11, 34, 12, 0, 0, 0)

def solve():
    # Helper to parse TLE Line 1 Epoch
    # orb_utils.parse_tle_epoch might exist or might not (based on 'no attribute' error I might have misread or it's restricted)
    # But modes.py uses it. Let's assume utils.parse_tle_epoch exists because I saw it in view_file orb_utils.py line 591!
    # "def parse_tle_epoch(line1):"
    
    epoch_year, epoch_day = orb_utils.parse_tle_epoch(TLE1)
    
    # Manual Parsing of Line 1/2
    # BSTAR
    try:
        bstar_str = TLE1[53:59]
        bstar_exp = TLE1[59:61]
        bstar = float(bstar_str) * 10.0 ** float(bstar_exp)
    except:
        bstar = 0.0
        
    line2 = TLE2
    inc = float(line2[8:16])
    raan = float(line2[17:25])
    ecc = float('0.' + line2[26:33])
    argp = float(line2[34:42])
    m = float(line2[43:51])
    n = float(line2[52:63])
    
    # Init SGP4
    sat = SGP4()
    sat.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)
    
    result = compute_satellite_geodetic(sat, sat.epoch_year, sat.epoch_day, TARGET_Tuple)
    t_min = result['t_min']
    gmst = result['gmst']
    
    # Replicate J2 Logic from propagators.py
    theta2 = sat.cosio * sat.cosio
    eosq = sat.ecc * sat.ecc
    betao2 = 1.0 - eosq
    CK2 = 5.413080e-4 
    
    # RAAN Precession
    rdot = -1.5 * CK2 * sat.cosio / (sat.aodp * sat.aodp * betao2 * betao2) * sat.n
    raan_curr = (sat.raan + rdot * t_min)
    
    # Arg of Perigee Precession
    pdot = 0.75 * CK2 * (5.0 * theta2 - 1.0) / (sat.aodp * sat.aodp * betao2 * betao2) * sat.n
    argp_curr = (sat.argp + pdot * t_min)
    
    # Mean Anomaly
    m_curr = (sat.m + sat.xmdot * t_min)
    
    # Solve Kepler
    e_anom = m_curr
    for i in range(10):
        d_e = (m_curr - e_anom + sat.ecc * math.sin(e_anom)) / (1.0 - sat.ecc * math.cos(e_anom))
        e_anom += d_e
        if abs(d_e) < 1e-6: break
    
    sin_e = math.sin(e_anom)
    cos_e = math.cos(e_anom)
    nu = math.atan2(math.sqrt(1.0 - sat.ecc * sat.ecc) * sin_e, cos_e - sat.ecc)
    
    # Outputs
    # AoV = Arg Latitude = nu + argp
    aov_rad = (nu + argp_curr) % (2*math.pi)
    aov_deg = math.degrees(aov_rad)
    
    # EQX = RAAN - GMST
    eqx_rad = (raan_curr - gmst) % (2*math.pi)
    eqx_deg = math.degrees(eqx_rad)
    
    print(f"Time: 2026-01-06 11:34:12 UTC")
    print(f"AoV: {aov_deg:.2f}")
    print(f"EQX: {eqx_deg:.2f}")
    print(f"Lat: {result['latitude']:.2f}")
    print(f"Lon: {result['longitude']:.2f}")
    print(f"Parameters for manual setup:")
    print(f"  Period: {1440.0/sat.n * 2*math.pi:.4f} min") # sat.n is rad/min? No, init takes revs/day, converts to rad/min. SGP4.init line 33: self.n = n*TWOPI/1440.
    # So sat.n is rad/min. Period = 2PI/n
    print(f"  Inc: {math.degrees(sat.inc):.4f} deg")

solve()
