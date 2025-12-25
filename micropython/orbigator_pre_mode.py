# Orbigator - Orbital Mechanics Simulator
# Pico 2 | DYNAMIXEL XL330-M288-T motors with orbital parameter computation
# EQX Motor (ID 1): Connected via 11T drive gear to 120T ring gear on globe
# AoV Motor (ID 2): Direct drive
# DYNAMIXEL: UART0 TX=GP0, RX=GP1, DIR=GP2 (via 74HC126 buffer)
# Encoder: A=GP6, B=GP7, SW=GP8 (pull-ups)
# Buttons: Back=GP9, Confirm=GP10 (pull-ups)
# OLED (SH1106/SSD1306 auto): I2C0 SDA=GP4, SCL=GP5

import machine, time, math, json
from machine import Pin, I2C
import framebuf
from ds3231 import DS3231
from dynamixel_motor import DynamixelMotor

# ---------------- Constants ----------------
CONFIG_FILE = "orbigator_config.json"

# Earth parameters
EARTH_RADIUS = 6378.137  # km
EARTH_MU = 398600.4418   # km^3/s^2 (gravitational parameter)
EARTH_J2 = 0.00108263    # J2 perturbation coefficient
SIDEREAL_DAY_SEC = 86164.0905  # seconds (23.934 hours)
EARTH_ROTATION_DEG_DAY = 360.0  # Earth rotates 360° per sidereal day

# Motor IDs
AOV_MOTOR_ID = 2  # Argument of Vehicle (direct drive)
EQX_MOTOR_ID = 1  # Equator crossing (geared)

# Motor gear ratios
EQX_GEAR_RATIO = 120.0 / 11.0  # Ring gear / Drive gear (TBR: verify tooth count)
AOV_GEAR_RATIO = 1.0  # Direct drive

# Encoder settings
DETENT_DIV = 4   # Changed from 4 - makes encoder more responsive
DEBOUNCE_MS = 200

# Altitude range: 200 km to 2000 km
MIN_ALTITUDE_KM = 200
MAX_ALTITUDE_KM = 2000

MAX_AOV_SPEED = 10
MAX_EQX_SPEED = 50 ## unlimited

# ---------------- OLED init ----------------
OLED_W, OLED_H = 128, 64
# Using 100kHz for better reliability with ChronoDot/DS3231
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
addrs = i2c.scan()
if not addrs:
    print("No I2C devices found on I2C0 (GP4/GP5).")
    # Don't exit, might be loose connection, try to proceed
else:
    ADDR = addrs[0]

class SH1106_I2C:
    def __init__(self, w,h,i2c,addr=0x3C):
        self.width,self.height,self.i2c,self.addr = w,h,i2c,addr
        self.buffer = bytearray(w*h//8)
        self.fb = framebuf.FrameBuffer(self.buffer, w, h, framebuf.MONO_VLSB)
        def cmd(*cs):
            for c in cs: self.i2c.writeto(self.addr, b'\x00'+bytes([c]))
        cmd(0xAE,0x20,0x00,0x40,0xA1,0xC8,0x81,0x7F,0xA6,0xA8,0x3F,
            0xAD,0x8B,0xD3,0x00,0xD5,0x80,0xD9,0x22,0xDA,0x12,0xDB,0x35,0xAF)
        self.fill(0); self.show()
    def fill(self,c): self.fb.fill(c)
    def text(self,s,x,y,c=1): self.fb.text(s,x,y,c)
    def show(self):
        for p in range(self.height//8):
            self.i2c.writeto(self.addr, b'\x00'+bytes([0xB0+p,0x02,0x10]))
            s = self.width*p; e = s+self.width
            self.i2c.writeto(self.addr, b'\x40'+self.buffer[s:e])

try:
    if addrs:
        disp = SH1106_I2C(OLED_W, OLED_H, i2c, addr=ADDR); DRIVER="SH1106"
    else:
        raise Exception("No display")
except Exception:
    try:
        if addrs:
            from ssd1306 import SSD1306_I2C
            disp = SSD1306_I2C(OLED_W, OLED_H, i2c, addr=ADDR); DRIVER="SSD1306"
    except:
        # Dummy display class if init fails
        class DummyDisp:
            def fill(self, c): pass
            def text(self, s, x, y, c=1): pass
            def show(self): pass
        disp = DummyDisp()

# ---------------- RTC Init ----------------
try:
    rtc = DS3231(i2c)
    print("RTC found and initialized.")
    # Check for valid year
    t = rtc.datetime()
    if t is not None and t[0] < 2020:
        print("RTC year < 2020, resetting to default.")
        # Set to 2020-01-01 00:00:00
        rtc.datetime((2020, 1, 1, 2, 0, 0, 0, 0)) # Wed
    elif t is None:
        print("RTC communication failed during init.")
except Exception as e:
    print("RTC init failed:", str(e))
    rtc = None

def get_timestamp():
    """Get current unix timestamp from RTC or system time."""
    try:
        if rtc:
            t = rtc.datetime()
            if t is None:
                # I2C communication failed, fall back to system time
                return time.time()
            # Check year again just in case
            if t[0] < 2020:
                 rtc.datetime((2020, 1, 1, 2, 0, 0, 0, 0))
                 t = rtc.datetime()
                 if t is None:
                     return time.time()
            # DS3231: (year, month, day, weekday, hour, minute, second, subsecond)
            # Calculate Unix timestamp manually (seconds since 1970-01-01)
            # Simple approximation - good enough for relative time tracking
            year, month, day, weekday, hour, minute, second, subsec = t
            
            # Days since epoch (1970-01-01)
            # Simplified calculation - assumes 365.25 days/year average
            days = (year - 1970) * 365 + (year - 1969) // 4  # Account for leap years
            
            # Add days for months (approximate - doesn't account for exact month lengths)
            month_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
            if month > 0 and month <= 12:
                days += month_days[month - 1]
            
            # Add current day
            days += day - 1
            
            # Convert to seconds and add time of day
            timestamp = days * 86400 + hour * 3600 + minute * 60 + second
            return timestamp
        else:
            return time.time()
    except Exception as e:
        print("RTC read error:", str(e))
        return time.time()

def get_time_string():
    """Return formatted time string YY-MM-DD HH:MM:SS"""
    if rtc:
        t = rtc.datetime()
        if t is not None:
            return "{:02d}{:02d}{:02d} {:02d}:{:02d}:{:02d}z".format(
                t[0]%100, t[1], t[2], t[4], t[5], t[6])
    # Fall back to system time if RTC fails or returns None
    t = time.localtime()
    return "{:02d}{:02d}{:02d} {:02d}:{:02d}:{:02d}z".format(
        t[0]%100, t[1], t[2], t[3], t[4], t[5])

def setup_datetime():
    """Prompt user to set date and time on startup."""
    global last_detent, raw_count
    
    if not rtc:
        print("No RTC found, skipping time setup.")
        return

    print("Entering Date/Time Setup...")
    print("Press button immediately to skip...")
    
    # Give user 2 seconds to skip
    skip_start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), skip_start) < 2000:
        if SW.value() == 0:  # Button pressed
            print("Skipping date/time setup")
            time.sleep_ms(200)
            while SW.value() == 0: time.sleep_ms(10)  # Wait for release
            return
        time.sleep_ms(50)
    
    # Get current time or default
    t = rtc.datetime()
    if t is None:
        # I2C communication failed, use defaults
        print("RTC communication failed, using defaults.")
        t = (2020, 1, 1, 0, 0, 0, 0, 0)
    # (year, month, day, weekday, hour, minute, second, subsecond)
    # Mutable list for editing: [year, month, day, hour, minute, second]
    dt = [t[0], t[1], t[2], t[4], t[5], t[6]]
    
    fields = [
        ("Year",   2020, 2099),
        ("Month",  1, 12),
        ("Day",    1, 31),
        ("Hour",   0, 23),
        ("Minute", 0, 59),
        ("Second", 0, 59)
    ]
    
    # Reset encoder for setup
    raw_count = 0
    last_detent = 0
    
    for i, (name, min_val, max_val) in enumerate(fields):
        # Reset encoder for each field to avoid jumps
        raw_count = 0
        last_detent = 0
        current_val = dt[i]
        
        while True:
            # Encoder handling
            irq = machine.disable_irq(); rc = raw_count; machine.enable_irq(irq)
            d = rc // DETENT_DIV
            
            if d != last_detent:
                delta = d - last_detent
                last_detent = d
                current_val += delta
                # Wrap or clamp? Let's clamp for Year, wrap for others maybe?
                # Simple clamping is safer for UI
                current_val = max(min_val, min(max_val, current_val))
            
            # Display
            try:
                disp.fill(0)
                disp.text("Set " + name + ":", 0, 0)
                disp.text("{}".format(current_val), 0, 16)
                disp.text("Click to Next", 0, 50)
                disp.show()
            except OSError as e:
                # OLED timeout - continue without display
                print(f"Display error (continuing): {e}")
            
            # Button handling
            if SW.value() == 0: # Pressed
                time.sleep_ms(DEBOUNCE_MS) # Debounce
                while SW.value() == 0: time.sleep_ms(10) # Wait for release
                dt[i] = current_val
                break # Next field
            
            time.sleep_ms(20)
            
    # Save to RTC
    # (year, month, day, weekday, hour, minute, second, subsecond)
    # We need to calculate weekday. simple approach or just set to 0 (Mon)
    # DS3231 calculates weekday automatically if running, but setting it might be needed.
    # Let's use a dummy weekday 0.
    new_t = (dt[0], dt[1], dt[2], 0, dt[3], dt[4], dt[5], 0)
    rtc.datetime(new_t)
    print("Time set to:", get_time_string())
    
    # Clear display
    try:
        disp.fill(0)
        disp.show()
    except OSError:
        pass  # Ignore display errors

# ---------------- Motor Initialization ----------------
print("="*60)
print("Initializing DYNAMIXEL motors...")
print("="*60)

# Import Extended Mode utilities
from dynamixel_extended_utils import set_extended_mode

try:
    # Configure motors for Extended Position Mode (Mode 4)
    # This must be done before creating DynamixelMotor instances
    print("\nConfiguring motors for Extended Position Mode...")
    
    print(f"\n1. Configuring AoV motor (ID {AOV_MOTOR_ID})...")
    if not set_extended_mode(AOV_MOTOR_ID):
        raise RuntimeError(f"Failed to configure AoV motor (ID {AOV_MOTOR_ID}) for Extended Position Mode")
    
    print(f"\n2. Configuring EQX motor (ID {EQX_MOTOR_ID})...")
    if not set_extended_mode(EQX_MOTOR_ID):
        raise RuntimeError(f"Failed to configure EQX motor (ID {EQX_MOTOR_ID}) for Extended Position Mode")
    
    print("\n✓ Motors configured for Extended Position Mode\n")
    
    # Now initialize motor objects
    print(f"3. Initializing AoV motor object...")
    aov_motor = DynamixelMotor(AOV_MOTOR_ID, "AoV", gear_ratio=AOV_GEAR_RATIO)
    print("   ✓ AoV motor ready")
    
    print(f"\n4. Initializing EQX motor object...")
    eqx_motor = DynamixelMotor(EQX_MOTOR_ID, "EQX", gear_ratio=EQX_GEAR_RATIO)
    print("   ✓ EQX motor ready")
    
    print("\n✓ Motors initialized successfully\n")
    
    # Set speed limits to prevent satellite from moving too fast
    print("Setting speed limits...")
    print("  (Higher values = slower, safer movement)")
    aov_motor.set_speed_limit(velocity=MAX_AOV_SPEED)  # Slower for AoV (visible pointer)
    eqx_motor.set_speed_limit(velocity=MAX_EQX_SPEED)  # Moderate for EQX (geared, slower anyway)
    print()
    
    # LED Flash Test - Visual motor identification without movement
    print("="*60)
    print("MOTOR ID TEST - LED Flash")
    print("="*60)
    disp.fill(0)
    disp.text("MOTOR TEST", 0, 0)
    disp.text("LED Flash...", 0, 16)
    disp.show()
    
    print("\nFlashing LEDs for motor identification...")
    print(f"  EQX Motor (ID {EQX_MOTOR_ID}): 1 flash")
    print(f"  AoV Motor (ID {AOV_MOTOR_ID}): 2 flashes")
    
    # Flash EQX motor LED once
    disp.fill(0)
    disp.text("MOTOR TEST", 0, 0)
    disp.text(f"EQX (ID {EQX_MOTOR_ID})", 0, 16)
    disp.text("Flash x1", 0, 32)
    disp.show()
    
    success = eqx_motor.flash_led(count=1, on_time_ms=50, off_time_ms=50)
    if success:
        print(f"  ✓ EQX motor LED flashed")
    else:
        print(f"  ✗ EQX motor LED flash failed")
    
    time.sleep_ms(500)  # Pause between motors
    
    # Flash AoV motor LED twice
    disp.fill(0)
    disp.text("MOTOR TEST", 0, 0)
    disp.text(f"AoV (ID {AOV_MOTOR_ID})", 0, 16)
    disp.text("Flash x2", 0, 32)
    disp.show()
    
    success = aov_motor.flash_led(count=2, on_time_ms=50, off_time_ms=50)
    if success:
        print(f"  ✓ AoV motor LED flashed")
    else:
        print(f"  ✗ AoV motor LED flash failed")
    
    time.sleep_ms(500)
    
    print("\n✓ Motor ID test complete\n")
    print("="*60)
    disp.fill(0)
    disp.text("MOTOR TEST", 0, 0)
    disp.text("Complete!", 0, 16)
    disp.show()
    time.sleep(1)
    
except RuntimeError as e:
    print(f"\n✗ Motor initialization failed: {e}")
    print("Cannot proceed without motors. Halting.")
    print("\nTroubleshooting:")
    print("  1. Check UART connections (GP0=TX, GP1=RX, GP2=DIR)")
    print("  2. Verify 74HC126 buffer wiring")
    print("  3. Check motor power (5V supply)")
    print(f"  4. Verify motor IDs (should be {AOV_MOTOR_ID} and {EQX_MOTOR_ID})")
    print("  5. Run test_two_motors.py to verify communication")
    while True:
        disp.fill(0)
        disp.text("MOTOR ERROR", 0, 0)
        disp.text("Check wiring", 0, 16)
        disp.text(str(e)[:16], 0, 32)
        disp.text("See console", 0, 48)
        disp.show()
        time.sleep(1)
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    print(f"   Type: {type(e).__name__}")
    import sys
    sys.print_exception(e)
    while True:
        disp.fill(0)
        disp.text("ERROR", 0, 0)
        disp.text(str(e)[:16], 0, 16)
        disp.text("See console", 0, 32)
        disp.show()
        time.sleep(1)

# ---------------- Encoder + Buttons ----------------
A  = Pin(6, Pin.IN, Pin.PULL_UP)
B  = Pin(7, Pin.IN, Pin.PULL_UP)
SW = Pin(8, Pin.IN, Pin.PULL_UP)
BACK_BTN = Pin(9, Pin.IN, Pin.PULL_UP)
CONFIRM_BTN = Pin(10, Pin.IN, Pin.PULL_UP)

state = (A.value()<<1) | B.value()
raw_count = 0
TRANS = (0,+1,-1,0,  -1,0,0,+1,  +1,0,0,-1,  0,-1,+1,0)

def _enc_isr(_):
    global state, raw_count
    s = (A.value()<<1) | B.value()
    d = TRANS[(state<<2)|s]
    raw_count -= d  # Reverse direction
    state = s

A.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)
B.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)

# ---------------- Orbital Mechanics ----------------
def compute_period_from_altitude(altitude_km):
    """Compute orbital period from altitude using Kepler's third law."""
    a = altitude_km + EARTH_RADIUS  # semi-major axis
    # T = 2π√(a³/μ)
    period_sec = 2 * math.pi * math.sqrt(a**3 / EARTH_MU)
    period_min = period_sec / 60.0
    return period_min

def compute_altitude_from_period(period_min):
    """Compute orbital altitude from period using Kepler's third law."""
    period_sec = period_min * 60.0
    # T = 2π√(a³/μ) => a = (μT²/4π²)^(1/3)
    a = (EARTH_MU * period_sec**2 / (4 * math.pi**2)) ** (1.0/3.0)
    altitude = a - EARTH_RADIUS
    return altitude, a

def compute_eqx_rate_j2(altitude_km, inclination_deg=51.6):
    """Compute EQX rate in Earth-fixed frame (deg/day).
    
    The Orbigator operates in an almost-ECI (Earth-Centered Inertial) frame:
    - The globe rotates at 360°/sidereal day (Earth's rotation)
    - The orbital plane precesses due to J2 (~5°/day for ISS)
    
    Total EQX rate ≈ 360°/sidereal day + J2 precession
    Motor position is wrapped modulo 360° to keep within one revolution.
    """
    a = altitude_km + EARTH_RADIUS
    inc_rad = math.radians(inclination_deg)
    
    # Mean motion (rad/s)
    n = math.sqrt(EARTH_MU / (a**3))
    
    # J2 precession rate (rad/s) - nodal precession of orbital plane
    # dΩ/dt = -1.5 * n * J2 * (Re/a)² * cos(i)
    eqx_rate_rad_s = -1.5 * n * EARTH_J2 * (EARTH_RADIUS / a)**2 * math.cos(inc_rad)
    
    # Convert to deg/day
    eqx_j2_deg_day = math.degrees(eqx_rate_rad_s) * 86400
    
    # Add Earth's rotation (360° per sidereal day)
    # Total rate in Earth-fixed frame
    # NEGATED: Motor horn faces down, so positive rotation = west (wrong!)
    # We want eastward rotation (sun rises in east), so negate the rate
    eqx_total_deg_day = -(eqx_j2_deg_day + EARTH_ROTATION_DEG_DAY)
    
    return eqx_total_deg_day

def compute_motor_rates(altitude_km):
    """Compute motor rotation rates for given altitude."""
    # Compute period from altitude
    period_min = compute_period_from_altitude(altitude_km)
    
    # AOV: 1 revolution per orbital period (in degrees per second)
    aov_deg_per_sec = 360.0 / (period_min * 60.0)
    
    # EQX: rate from J2 effect + Earth rotation (in degrees per second)
    eqx_rate_deg_day = compute_eqx_rate_j2(altitude_km)
    eqx_deg_per_sec = eqx_rate_deg_day / 86400.0
    
    return aov_deg_per_sec, eqx_deg_per_sec, eqx_rate_deg_day, period_min

def wrap_aov_position(current_deg, target_deg):
    """
    Wrap AoV target position to stay within ±180° of current position.
    
    CRITICAL: AoV motor should NEVER move more than one revolution!
    The pointer arm is mechanically constrained, so we must always
    take the shortest path to the target position.
    
    Args:
        current_deg: Current AoV position in degrees
        target_deg: Desired AoV position in degrees
    
    Returns:
        Wrapped target position that's within ±180° of current position
    """
    # Calculate the difference
    diff = target_deg - current_deg
    
    # Normalize difference to -180 to +180 range
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
    
    # Return current position + shortest path
    wrapped_target = current_deg + diff
    
    return wrapped_target

# ---------------- Persistence ----------------
def save_state():
    """Save current orbital parameters to config file."""
    try:
        config = {
            "altitude_km": orbital_altitude_km,
            "eqx_deg": eqx_position_deg,
            "aov_deg": aov_position_deg,
            "timestamp": get_timestamp()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        print("State saved:", config)
    except Exception as e:
        print("Error saving state:", e)

def load_state():
    """Load orbital parameters from config file."""
    global orbital_altitude_km, eqx_position_deg, aov_position_deg
    global orbital_period_min
    
    # CRITICAL: Read current motor positions BEFORE any commands
    # This prevents motors from jumping on startup
    print("\nReading current motor positions...")
    current_eqx_deg = eqx_motor.get_angle_degrees()
    current_aov_deg = aov_motor.get_angle_degrees()
    
    if current_eqx_deg is None or current_aov_deg is None:
        print("✗ Failed to read motor positions!")
        # Use defaults if we can't read
        eqx_position_deg = 0.0
        aov_position_deg = 0.0
        orbital_period_min = compute_period_from_altitude(orbital_altitude_km)
        return
    
    print(f"  Current EQX: {current_eqx_deg:.2f}°")
    print(f"  Current AoV: {current_aov_deg:.2f}°")
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            
        orbital_altitude_km = config.get("altitude_km", 400.0)
        eqx_position_deg = config.get("eqx_deg", 0.0)
        aov_position_deg = config.get("aov_deg", 0.0)
        saved_timestamp = config.get("timestamp", 0)
        
        # Update computed values
        orbital_period_min = compute_period_from_altitude(orbital_altitude_km)
        
        # Calculate catch-up if we have a valid timestamp
        current_timestamp = get_timestamp()
        delta_t = current_timestamp - saved_timestamp
        
        if delta_t > 0 and saved_timestamp > 0:
            print("Catching up {} seconds...".format(delta_t))
            
            # Compute rates for catch-up
            _, _, eqx_rate_deg_day, period_min = compute_motor_rates(orbital_altitude_km)
            
            # EQX catch-up (can be any amount - continuous rotation)
            eqx_rate_deg_sec = eqx_rate_deg_day / 86400.0
            eqx_delta = eqx_rate_deg_sec * delta_t
            target_eqx_deg = eqx_position_deg + eqx_delta
            
            # AOV catch-up
            aov_rate_deg_sec = 360.0 / (period_min * 60.0)
            aov_delta = aov_rate_deg_sec * delta_t
            target_aov_deg = aov_position_deg + aov_delta
            
            # CRITICAL: Wrap AoV to prevent multi-revolution movement
            # AoV should NEVER move more than ±180° from current position
            target_aov_deg = wrap_aov_position(current_aov_deg, target_aov_deg)
            aov_diff = target_aov_deg - current_aov_deg
            
            # Move motors to catch-up positions using shortest path
            target_eqx_wrapped = target_eqx_deg % 360.0
            target_aov_wrapped = target_aov_deg % 360.0
            
            print(f"Moving EQX: {current_eqx_deg:.2f}° → target: {target_eqx_wrapped:.2f}°")
            eqx_motor.set_nearest_degrees(target_eqx_wrapped)
            time.sleep(0.5)
            
            print(f"Moving AoV: {current_aov_deg:.2f}° → target: {target_aov_wrapped:.2f}° (Δ={aov_diff:+.2f}°)")
            aov_motor.set_nearest_degrees(target_aov_wrapped)
            time.sleep(0.5)
            
            # Update positions (wrapped for display)
            eqx_position_deg = target_eqx_wrapped
            aov_position_deg = target_aov_deg % 360.0
            
            print("✓ Catch-up complete")
        else:
            # No catch-up needed - use current motor positions as baseline
            print("No catch-up needed (no saved timestamp or delta_t <= 0)")
            eqx_position_deg = current_eqx_deg
            aov_position_deg = current_aov_deg
        
        print("State loaded:", config)
    except OSError:
        print("No config file found, using defaults.")
        # Use current motor positions as baseline
        eqx_position_deg = current_eqx_deg
        aov_position_deg = current_aov_deg
    except Exception as e:
        print("Error loading state:", e)

# ---------------- State Machine ----------------
# State 0: Set altitude
# State 1: Set EQX position
# State 2: Set AOV position
# State 3: Run simulation
current_state = 3  # Start in running state for debugging (normally 0)
last_button_time = 0

# Orbital parameters
orbital_altitude_km = 400.0  # Start at ISS altitude
orbital_period_min = 0.0  # Computed from altitude
eqx_position_deg = 0.0
aov_position_deg = 0.0

# Computed rates
aov_rate_deg_sec = 0.0
eqx_rate_deg_sec = 0.0
eqx_rate_deg_day = 0.0
orbital_period_min = 0.0

# RTC motion tracking
run_start_time = 0
run_start_eqx_deg = 0.0
run_start_aov_deg = 0.0

# Run mode sub-state (0 = nudge AoV, 1 = nudge EQX)
run_sub_mode = 0

# Encoder tracking
last_detent = 0

# Button state tracking for long press detection
button_down = False
button_press_start = 0

# Back and Confirm button state tracking
back_btn_last = 1  # Released (pull-up)
confirm_btn_last = 1  # Released (pull-up)
last_back_time = 0
last_confirm_time = 0

# Display error tracking
display_consecutive_failures = 0

# Display update timing - update once per second
last_display_update = 0

def poll_button():
    """Check for button press and advance state (non-blocking state machine)."""
    global current_state, last_button_time
    global run_start_time, run_start_eqx_deg, run_start_aov_deg
    global aov_rate_deg_sec, eqx_rate_deg_sec, eqx_rate_deg_day, orbital_period_min
    global button_down, button_press_start, run_sub_mode
    
    now = time.ticks_ms()
    
    # Detect button press (transition from released to pressed)
    if SW.value() == 0 and not button_down:
        # Button just pressed
        if time.ticks_diff(now, last_button_time) > DEBOUNCE_MS:
            button_down = True
            button_press_start = now
    
    # Detect button release (transition from pressed to released)
    elif SW.value() == 1 and button_down:
        # Button just released
        button_down = False
        press_duration = time.ticks_diff(now, button_press_start)
        last_button_time = now
        
        # Check if it was a long press (>= 1 second)
        if press_duration >= 1000:
            # Long press - trigger date/time setup
            setup_datetime()
            return
        
        # Short press behavior depends on current state
        if current_state == 3:
            # In run state - toggle sub-mode (don't advance state)
            run_sub_mode = (run_sub_mode + 1) % 2
            print(f"Run sub-mode: {'Nudge EQX' if run_sub_mode == 1 else 'Nudge AoV'}")
        else:
            # In setup states (0-2) - advance state
            # Save state before changing (persists user adjustments)
            save_state()
            
            # Advance to next state
            current_state = (current_state + 1) % 4
            
            if current_state == 3:
                # Entering run state - compute motor rates
                _, _, eqx_rate_deg_day, orbital_period_min = compute_motor_rates(orbital_altitude_km)
                
                # Calculate rates in deg/sec for RTC loop
                eqx_rate_deg_sec = eqx_rate_deg_day / 86400.0
                aov_rate_deg_sec = 360.0 / (orbital_period_min * 60.0)
                
                # Initialize RTC tracking
                run_start_time = get_timestamp()
                run_start_eqx_deg = eqx_position_deg
                run_start_aov_deg = aov_position_deg
                
                # Initialize sub-mode to nudge AoV
                run_sub_mode = 0

def update_from_encoder():
    """Update current parameter based on encoder and state."""
    global last_detent, orbital_altitude_km, eqx_position_deg, aov_position_deg
    
    irq = machine.disable_irq(); rc = raw_count; machine.enable_irq(irq)
    d = rc // DETENT_DIV
    
    if d != last_detent:
        delta = d - last_detent
        last_detent = d
        
        if current_state == 0:
            # Adjust altitude (10 km per detent)
            orbital_altitude_km += delta * 10.0
            orbital_altitude_km = max(MIN_ALTITUDE_KM, min(MAX_ALTITUDE_KM, orbital_altitude_km))
        
        elif current_state == 1:
            # Adjust EQX (1 degree per detent)
            eqx_position_deg += delta * 1.0
            eqx_position_deg = eqx_position_deg % 360.0
            # Update motor position using shortest path
            eqx_motor.set_nearest_degrees(eqx_position_deg)
        
        elif current_state == 2:
            # Adjust AOV (1 degree per detent)
            aov_position_deg += delta * 1.0
            aov_position_deg = aov_position_deg % 360.0
            # Update motor position using shortest path
            aov_motor.set_nearest_degrees(aov_position_deg)

# ---------------- Main Loop ----------------
# Setup Date/Time on startup (commented out for debugging)
# setup_datetime()

# Load saved state on startup
load_state()

# Initialize motor rates if starting in state 3
if current_state == 3:
    _, _, eqx_rate_deg_day, orbital_period_min = compute_motor_rates(orbital_altitude_km)
    eqx_rate_deg_sec = eqx_rate_deg_day / 86400.0
    aov_rate_deg_sec = 360.0 / (orbital_period_min * 60.0)
    run_start_time = get_timestamp()
    run_start_eqx_deg = eqx_position_deg
    run_start_aov_deg = aov_position_deg
    print(f"Motor rates initialized: AoV={aov_rate_deg_sec:.6f}°/s, EQX={eqx_rate_deg_sec:.6f}°/s")

print("Orbigator - Orbital Mechanics Simulator")
print("State 0: Set Altitude | State 1: Set EQX")
print("State 2: Set AOV | State 3: Run")

while True:
    time.sleep_ms(20)
    
    poll_button()
    
    if current_state == 3:
        # State 3: Run simulation with RTC-based motion
        now = get_timestamp()
        elapsed = now - run_start_time
        
        # Check for encoder input to nudge motor (based on sub-mode)
        irq = machine.disable_irq(); rc = raw_count; machine.enable_irq(irq)
        d = rc // DETENT_DIV
        
        if d != last_detent:
            delta = d - last_detent
            last_detent = d
            
            if run_sub_mode == 0:
                # Nudge AoV by 1 degree per detent
                # This adjusts the baseline, so the nudge persists
                run_start_aov_deg += delta * 1.0
                print(f"AoV nudged: {delta:+.0f}° (new baseline: {run_start_aov_deg:.1f}°)")
            else:
                # Nudge EQX by 1 degree per detent
                # This adjusts the baseline, so the nudge persists
                run_start_eqx_deg += delta * 1.0
                print(f"EQX nudged: {delta:+.0f}° (new baseline: {run_start_eqx_deg:.1f}°)")
        
        # Calculate target positions based on elapsed time (AFTER nudging)
        target_eqx_deg = run_start_eqx_deg + (eqx_rate_deg_sec * elapsed)
        target_aov_deg = run_start_aov_deg + (aov_rate_deg_sec * elapsed)
        
        # Update global positions for display/saving
        eqx_position_deg = target_eqx_deg % 360.0  # Wrap to 0-360 for display
        aov_position_deg = target_aov_deg % 360.0  # Keep in 0-360 for display
        
        # Send motor commands using shortest path
        eqx_motor.set_nearest_degrees(eqx_position_deg)
        aov_motor.set_nearest_degrees(aov_position_deg)
    else:
        # States 0-2: Encoder control
        update_from_encoder()
    
    # Display - update once per second
    now_ms = time.ticks_ms()
    if time.ticks_diff(now_ms, last_display_update) >= 1000:
        last_display_update = now_ms
        
        disp.fill(0)
        disp.text(get_time_string(), 0, 0)
        
        if current_state == 3:  # Running (always active for debugging)
            sub_mode_indicator = "A>" if run_sub_mode == 0 else "X>"
            disp.text("RUN " + sub_mode_indicator, 0, 12)
            disp.text("T:{:.0f}m".format(orbital_period_min), 0, 24)
            disp.text("A:{:.1f} X:{:.1f}".format(aov_position_deg % 360, eqx_position_deg % 360), 0, 36)
            disp.text("dL:{:.2f}d/d".format(eqx_rate_deg_day), 0, 48)
        
        disp.show()


