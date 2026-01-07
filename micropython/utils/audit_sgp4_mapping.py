
import time
import math
from sgp4 import SGP4
import propagators
import satellite_position

def run_audit():
    print("=== SGP4 Motor Mapping Audit ===")
    print("Objective: Verify that when AoV=0 (Ascending Node), Longitude == EQX")
    
    # 1. Setup SGP4 with ISS TLE
    # Using fixed TLE for consistent testing
    line1 = "1 25544U 98067A   23324.54791667  .00012345  00000-0  00000+0 0  9993"
    line2 = "2 25544  51.6416 245.1234 0006789 123.4567 236.5432 15.50000000999998"
    
    # Parse epoch from TLE manually for the test setup
    epoch_year = 23
    epoch_day = 324.54791667
    
    sgp4_obj = SGP4()
    # bstar, inc, raan, ecc, argp, m, n
    sgp4_obj.init(epoch_year, epoch_day, 0.00012345, 51.6416, 245.1234, 0.0006789, 123.4567, 236.5432, 15.5)
    
    prop = propagators.SGP4Propagator(sgp4_obj)
    
    # 2. Find Ascending Node (AoV = 0)
    # Start at TLE epoch roughly (INTEGER TIMESTAMP for precision safety)
    # 2023-11-20 13:08:40 UTC
    start_time = int(time.mktime((2023, 11, 20, 13, 8, 40, 0, 324)))
    
    print(f"Scanning for Ascending Node (AoV=0)...")
    print(f"Start Unix: {start_time}")
    
    # Coarse search
    found = False
    target_time = 0
    
    prev_aov_wrapped = -180.0
    
    for t_offset in range(0, 7200, 10): # Extended to 120 mins
        current_time = start_time + t_offset
        aov, eqx, lat, lon = prop.get_aov_eqx(current_time)
        
        # Wrapped AoV: -180 to 180 (User request)
        # 0 is the ascending node.
        aov_wrapped = (aov + 180) % 360 - 180
        
        if t_offset % 600 == 0:
            print(f"t+{t_offset}s: AoV={aov:.1f}, Wrapped={aov_wrapped:.1f}, Lon={lon:.1f}")

        # Check for 0 crossing (negative to positive, e.g. -2.0 -> +2.0)
        # Or wrap-around if previously near start
        if prev_aov_wrapped < 0 and aov_wrapped >= 0 and abs(prev_aov_wrapped - aov_wrapped) < 20:
             print(f"Found crossover near t+{t_offset}")
             target_time = current_time
             found = True
             break
             
        prev_aov_wrapped = aov_wrapped
        
    if not found:
        print("Could not find Ascending Node (0-crossing) in search window.")
        return

    # Fine search
    print("Refining...")
    best_time = target_time
    min_dist = 360.0
    
    # Search -20s to +20s around coarse find
    for t_offset in range(-20, 21): 
        test_time = target_time + t_offset
        
        aov, eqx, lat, lon = prop.get_aov_eqx(test_time)
        aov_wrapped = (aov + 180) % 360 - 180
        
        dist_to_0 = abs(aov_wrapped)
        
        if dist_to_0 < min_dist:
            min_dist = dist_to_0
            best_time = test_time
            
    # 3. Validation at Best Time
    aov, eqx, lat, lon = prop.get_aov_eqx(best_time)
    aov_wrapped = (aov + 180) % 360 - 180
    
    print("\n=== RESULTS ===")
    print(f"Unix Time: {best_time}")
    print(f"AoV:       {aov:.4f}°")
    print(f"AoV Wrap:  {aov_wrapped:.4f}° (Target: 0.0000°)")
    print(f"EQX:       {eqx:.4f}°")
    print(f"Longitude: {lon:.4f}°")
    
    # Error Analysis
    # User Hypothesis: When AoV=0, Lon=EQX
    
    # Normalize angles to 0..360 for comparison
    lon_norm = lon % 360.0
    eqx_norm = eqx % 360.0
    
    diff = abs(lon_norm - eqx_norm)
    if diff > 180: diff = abs(diff - 360)
    
    print("-" * 30)
    print(f"Lon (Norm): {lon_norm:.4f}°")
    print(f"EQX (Norm): {eqx_norm:.4f}°")
    print(f"Difference: {diff:.4f}°")
    
    if diff < 1.0:
        print("\n✅ PASS: Longitude matches EQX at Ascending Node!")
    else:
        print("\n❌ FAIL: Significant discrepancy > 1.0°")

if __name__ == "__main__":
    run_audit()
