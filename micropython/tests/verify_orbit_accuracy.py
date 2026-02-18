
import sys
import os
import math
import time

# Add micropython directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import satellite_position
from sgp4 import SGP4

# TLE from orbit.dat header
TLE_LINE1 = "1 25544U 98067A   26046.56961129  .00012237  00000+0  23255-3 0  9991"
TLE_LINE2 = "2 25544  51.6318 181.6982 0010992 101.7612 258.4610 15.48625638552905"

def parse_tle_epoch(line1):
    """Parse epoch year and day from line 1."""
    epoch_str = line1[18:32]
    year = int(epoch_str[:2])
    day = float(epoch_str[2:])
    return 2000 + year, day

def run_verification():
    orbit_dat_path = os.path.join(os.path.dirname(__file__), "orbit.dat")
    
    if not os.path.exists(orbit_dat_path):
        print(f"Error: {orbit_dat_path} not found.")
        return

    print(f"Verifying against {orbit_dat_path}...")
    
    # Initialize SGP4/Propagator
    # We need to manually initialize the SGP4 object as per propagate.py/modes.py logic
    # But satellite_position.compute_satellite_geodetic takes an ALLOW_SGP4 object and does the rest.
    # Wait, compute_satellite_geodetic expects an initialized sgp4 object.
    
    # Parse TLE
    # Assuming standard sgp4 lib is available (as it is in micropython/)
    # But wait, the micropython environment uses a stripped down sgp4.py usually. 
    # Let's check satellite_position.py's expectations.
    # It imports `from sgp4 import SGP4`.
    
    year, day = parse_tle_epoch(TLE_LINE1)
    
    # Initialize SGP4 model
    # We use the structure expected by user's SGP4 class. 
    # Let's verify how modes.py initializes it.
    # modes.py:
    #   self.sgp4 = sgp4.SGP4()
    #   self.sgp4.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)
    
    # We'll use the 'sgp4' module in micropython/ which seems to be the minimal one.
    # We need to parse all orbital elements to init it.
    
    # Parse TLE Helper (roughly from modes.py logic or manual parse)
    # L1: 18-32 Epoch, 33-43 1st Deriv, 44-52 2nd Deriv, 53-61 BSTAR
    # L2: 08-16 Inc, 17-25 RAAN, 26-33 Ecc, 34-42 ArgP, 43-51 MeanAnom, 52-63 MeanMotion
    
    def parse_float(s): 
        # Handle implicit decimal for BSTAR/ECC
        if '-' in s[1:]: # handle 12345-5 -> 12345e-5
             return float(s.replace('-', 'e-'))
        return float(s)

    # Line 1
    # epoch_year = int(TLE_LINE1[18:20]) + 2000 (Already have year)
    # epoch_day = float(TLE_LINE1[20:32]) (Already have day)
    # BSTAR: Cols 53-61 (0-based index)
    # Format: MMMMM-E -> 0.MMMMM * 10^-E
    bstar_str = TLE_LINE1[53:61] # " 23255-3"
    
    # Remove leading spaces which might shift indices if we split naively
    # Strict TLE format:
    # 53: always space? No, can be minus. 
    # 54-58: Mantissa
    # 59-60: Exponent (starts with + or - usually?) 
    # In " 23255-3": index 0 is space. 
    # Let's clean it.
    
    value_str = bstar_str.strip()
    # If empty or 00000-0
    if not value_str or value_str == "00000-0":
        bstar = 0.0
    else:
        # Last 2 chars are exponent? Or last 1 if no sign?
        # Standard: +/- at 59, digit at 60.
        # "23255-3" -> Mantissa 23255, Exp -3
        # Find where exponent starts (last +/-)
        exp_idx = -1
        if value_str[-2] in ('+', '-'):
            exp_idx = -2
        elif value_str[-1] in ('+', '-'): # Should not happen at end
            pass 
        
        # Simpler approach: TLE BSTAR is always XXXXX-Y or XXXXX+Y
        # Where XXXXX is mantissa (0.XXXXX) and Y is exponent
        # But wait, index 53 might be a sign for the mantissa itself?
        # Usually BSTAR is positive.
        
        # Let's rely on string format:
        # " 23255-3" -> 0.23255e-3
        # Remove space
        s = value_str
        # Last character is exponent digit. 
        # Second to last is exponent sign.
        exponent = int(s[-2:])
        mantissa = float(s[:-2])
        
        # Decimal point is before the mantissa digits.
        # But `mantissa` above treats "23255" as 23255.0
        # We need to divide by 10^len(mantissa_digits)? 
        # No, standard is 0.XXXXX
        # So we divide mantissa integer by 10^5 is the simplified rule usually.
        # But wait, if s[:-2] is " 23255", len is 6.
        # Let's just blindly follow the sgp4.cpp convention or similar.
        
        # "23255-3"
        # Mantissa: 23255 -> 0.23255
        # Exp: -3
        
        # Safer parse:
        # Take everything except last 2 chars as mantissa string
        man_str = s[:-2]
        exp_str = s[-2:]
        
        # Note: Man_str might have leading sign
        
        bstar = float(man_str) * 1e-5 * math.pow(10, float(exp_str))

    # Line 2
    inc = float(TLE_LINE2[8:16])
    raan = float(TLE_LINE2[17:25])
    ecc = float("." + TLE_LINE2[26:33])
    argp = float(TLE_LINE2[34:42])
    m = float(TLE_LINE2[43:51])
    n = float(TLE_LINE2[52:63])
    
    sgp4_obj = SGP4()
    sgp4_obj.init(year, day, bstar, inc, raan, ecc, argp, m, n)
    
    errors_lat = []
    errors_lon = []
    
    with open(orbit_dat_path, 'r') as f:
        count = 0
        max_error = 0.0
        
        for line in f:
            if line.startswith("#"):
                continue
                
            parts = line.split()
            if not parts: continue
            
            ts = int(parts[0])
            truth_lat = float(parts[2])
            truth_lon = float(parts[3])
            
            # Run calculation
            # satellite_position expects current_time_tuple
            t_struct = time.gmtime(ts)
            # (Y, M, D, H, M, S)
            t_tuple = t_struct[0:6]
            
            result = satellite_position.compute_satellite_geodetic(
                sgp4_obj, year, day, unix_timestamp=ts
            )
            
            calc_lat = result['latitude']
            calc_lon = result['longitude']
            
            # Calc errors
            err_lat = abs(calc_lat - truth_lat)
            
            # Longitude wrap around handling
            diff_lon = abs(calc_lon - truth_lon)
            if diff_lon > 180:
                diff_lon = 360 - diff_lon
            err_lon = diff_lon
            
            errors_lat.append(err_lat)
            errors_lon.append(err_lon)
            
            current_max = max(err_lat, err_lon)
            if current_max > max_error:
                max_error = current_max
            
            count += 1
            if count <= 10:
                print(f"Sample {count}: Time={ts}, LatErr={err_lat:.4f}, LonErr={err_lon:.4f}")
            
            if count % 100 == 0:
                pass

    avg_lat = sum(errors_lat) / len(errors_lat)
    avg_lon = sum(errors_lon) / len(errors_lon)
    max_lat = max(errors_lat)
    max_lon = max(errors_lon)
    
    print("-" * 40)
    print(f"Verified {count} samples.")
    print(f"Lat Error: Avg={avg_lat:.6f}°, Max={max_lat:.6f}°")
    print(f"Lon Error: Avg={avg_lon:.6f}°, Max={max_lon:.6f}°")
    print("-" * 40)
    
    if max_lat < 1.0 and max_lon < 1.0:
        print("PASS: Errors are under 1.0 degree.")
    else:
        print("FAIL: Errors exceed 1.0 degree.")

if __name__ == "__main__":
    run_verification()
