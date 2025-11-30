import machine
import time
import math
from sgp4 import SGP4, DE2RA, PI, TWOPI

# --- Pin Definitions (Pico 2) ---
# Adjust these to match your wiring!
BASE_STEP_PIN = 14
BASE_DIR_PIN  = 15
BASE_EN_PIN   = 13

ARM_STEP_PIN  = 2
ARM_DIR_PIN   = 3
ARM_EN_PIN    = 4

# --- Constants ---
# Gear Ratios (Approximate - need calibration)
BASE_STEPS_PER_REV = 200.0 * 17.14 
ARM_STEPS_PER_REV  = 200.0 * 60.0 

class Stepper:
    def __init__(self, step_pin, dir_pin, en_pin, steps_per_rev, invert=False):
        self.step = machine.Pin(step_pin, machine.Pin.OUT)
        self.dir = machine.Pin(dir_pin, machine.Pin.OUT)
        self.en = machine.Pin(en_pin, machine.Pin.OUT)
        self.steps_per_rev = steps_per_rev
        self.invert = invert
        self.current_steps = 0
        self.disable()

    def enable(self):
        self.en.value(0) # Active LOW

    def disable(self):
        self.en.value(1)

    def move_to_angle(self, angle_deg):
        # Normalize 0-360
        angle_deg %= 360.0
        
        target_steps = int(angle_deg * self.steps_per_rev / 360.0)
        delta = target_steps - self.current_steps
        
        if delta == 0: return

        self.enable()
        
        direction = 1 if delta > 0 else -1
        if self.invert: direction *= -1
        
        self.dir.value(1 if direction > 0 else 0)
        
        count = abs(delta)
        for _ in range(count):
            self.step.value(1)
            time.sleep_us(1000)
            self.step.value(0)
            time.sleep_us(1000)
            
        self.current_steps = target_steps
        # self.disable() # Optional power save

# --- Setup ---
base_motor = Stepper(BASE_STEP_PIN, BASE_DIR_PIN, BASE_EN_PIN, BASE_STEPS_PER_REV)
arm_motor = Stepper(ARM_STEP_PIN, ARM_DIR_PIN, ARM_EN_PIN, ARM_STEPS_PER_REV)

propagator = SGP4()

# ISS TLE (Example)
epoch_year = 23
epoch_day = 324.54791667
bstar = 0.00012345
inc = 51.6416
raan = 245.1234
ecc = 0.0006789
argp = 123.4567
m = 236.5432
n = 15.5

propagator.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)

print("Orbigator Initialized")

# --- Main Loop ---
current_time_min = 0.0
last_update = time.ticks_ms()

while True:
    now = time.ticks_ms()
    if time.ticks_diff(now, last_update) > 1000:
        last_update = now
        
        # Advance time (1x speed)
        current_time_min += (1.0 / 60.0)
        
        # Propagate
        x, y, z = propagator.propagate(current_time_min)
        
        # GMST (Simplified)
        gmst = 0.0 
        
        # Geodetic
        lat, lon, alt = propagator.eci_to_geodetic(x, y, z, gmst)
        
        lat_deg = lat * 180.0 / PI
        lon_deg = lon * 180.0 / PI
        
        print(f"T:{current_time_min:.2f} Lat:{lat_deg:.2f} Lon:{lon_deg:.2f}")
        
        # Move Motors
        # Base Ring = Longitude (Ring at South Pole, rotates to match Lon)
        base_motor.move_to_angle(lon_deg)
        
        # Arm = Latitude (0 = Equator, 90 = North Pole)
        # Map -90..90 to motor angle? Or is 0 at South Pole?
        # Assuming Arm 0 is Equator for now.
        arm_motor.move_to_angle(lat_deg)
