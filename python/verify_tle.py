"""
Verify both implementations use the same TLE data
"""

import json

# Load TLE from cache
with open('/home/justin/code/orbigator/micropython/tle_cache.json', 'r') as f:
    cache = json.load(f)

print("=" * 70)
print("TLE Data Verification")
print("=" * 70)
print()

for sat_name in ["ISS", "HUBBLE"]:
    print(f"{sat_name}:")
    print(f"  Line 1: {cache[sat_name]['line1']}")
    print(f"  Line 2: {cache[sat_name]['line2']}")
    print()
