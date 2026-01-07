"""
Test SGP4 Integration
Validates SGP4Mode without hardware
"""

import sys
sys.path.append('/home/justin/code/orbigator/micropython')

# Mock hardware dependencies
class MockMotor:
    def __init__(self, name):
        self.name = name
        self.angle = 0.0
    
    def set_nearest_degrees(self, angle):
        self.angle = angle
        print(f"{self.name} -> {angle:.2f}°")
        return True

class MockDisplay:
    def fill(self, c): pass
    def text(self, s, x, y, c=1): 
        print(f"  [{x:3d},{y:2d}] {s}")
    def show(self): 
        print("  [DISPLAY UPDATED]")

# Mock globals
class MockGlobals:
    def __init__(self):
        self.aov_motor = MockMotor("AoV")
        self.eqx_motor = MockMotor("EQX")
        self.rtc = None
        self.disp = MockDisplay()
        self.orbital_altitude_km = 400.0
        self.orbital_inclination_deg = 51.6
        self.orbital_eccentricity = 0.0
        self.orbital_periapsis_deg = 0.0
        self.aov_position_deg = 0.0
        self.eqx_position_deg = 0.0

import orb_globals as g_real
g_mock = MockGlobals()

# Patch globals
for attr in dir(g_mock):
    if not attr.startswith('_'):
        setattr(g_real, attr, getattr(g_mock, attr))

# Now import modes
from modes import SGP4Mode
import time

print("="*60)
print("SGP4 Integration Test")
print("="*60)

# Test 1: Mode initialization
print("\n[TEST 1] Initializing SGP4Mode...")
mode = SGP4Mode()
mode.enter()

print(f"  Satellite count: {mode.sat_count}")
print(f"  Current satellite: {mode.satellite_name}")
print(f"  TLE age: {mode.tle_age}")

# Test 2: Satellite selection
print("\n[TEST 2] Testing satellite selection...")
mode.on_encoder_rotate(1)  # Next satellite
print(f"  Selected: {mode.satellite_name}")

mode.on_encoder_rotate(-1)  # Previous satellite
print(f"  Selected: {mode.satellite_name}")

# Test 3: Start tracking
print("\n[TEST 3] Starting tracking...")
mode.on_encoder_press()
print(f"  Tracking: {mode.tracking}")

# Test 4: Update position
print("\n[TEST 4] Updating satellite position...")
mode.update(0)
print(f"  Lat: {mode.lat_deg:.2f}°")
print(f"  Lon: {mode.lon_deg:.2f}°")
print(f"  Alt: {mode.alt_km:.1f} km")

# Test 5: Render display
print("\n[TEST 5] Rendering display...")
mode.render(g_real.disp)

print("\n" + "="*60)
print("✓ SGP4 Integration Test Complete")
print("="*60)
