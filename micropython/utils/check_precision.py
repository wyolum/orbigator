
import time
import sys

print(f"Float Info: {sys.float_info}")

# Mock satellite_position logic for verification
def compute_epoch_diff(tle_year, tle_day, current_time_tuple):
    # Handle year
    year = tle_year
    if year < 100: year += 2000
    
    # Epoch Jan 1
    epoch_jan1 = time.mktime((year, 1, 1, 0, 0, 0, 0, 0, 0))
    
    # Split TLE day
    day_int = int(tle_day)
    day_frac = tle_day - day_int
    
    # Current time
    current_unix = time.mktime(current_time_tuple)
    
    # Calc diff (High Precision)
    diff_sec_int = int(current_unix) - int(epoch_jan1) - (day_int - 1) * 86400
    diff_sec_total = diff_sec_int - (day_frac * 86400.0)
    
    return diff_sec_total / 60.0

# Scenario: TLE Epoch is Jan 1.0 (00:00:00). Current time is Jan 1 00:00:01
# Expected diff: 1 second = 1/60 min
year = 2024
day = 1.0
cur_time = (2024, 1, 1, 0, 0, 1, 0, 0, 0)
diff_min = compute_epoch_diff(year, day, cur_time)

expected_min = 1.0/60.0
error = abs(diff_min - expected_min)

print(f"Diff Min: {diff_min}")
print(f"Expected: {expected_min}")
print(f"Error: {error}")

if error < 1e-7:
    print("PASS: High precision maintained.")
else:
    print("FAIL: Precision loss detected.")
