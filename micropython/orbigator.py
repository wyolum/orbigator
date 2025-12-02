# Orbigator - Orbital Mechanics Simulator
# Pico 2 | LAN & AOV motors with orbital parameter computation
# LAN Motor (DRV8834): STEP=GP14, DIR=GP15, nSLEEP=GP12, nENBL=GP13, M0=GP10, M1=GP11
# AOV Motor (ULN2003): IN1=GP2, IN2=GP3, IN3=GP22, IN4=GP26
# Encoder: A=GP6, B=GP7, SW=GP8 (pull-ups)
# OLED (SH1106/SSD1306 auto): I2C0 SDA=GP4, SCL=GP5

import machine, time, math
from machine import Pin, I2C
import framebuf

# ---------------- Constants ----------------
# Earth parameters
EARTH_RADIUS = 6378.137  # km
EARTH_MU = 398600.4418   # km^3/s^2 (gravitational parameter)
EARTH_J2 = 0.00108263    # J2 perturbation coefficient
SIDEREAL_DAY_SEC = 86164.0905  # seconds (23.934 hours)
EARTH_ROTATION_DEG_DAY = 360.0  # Earth rotates 360° per sidereal day

# Motor settings
LAN_STEPS_PER_REV = 200
LAN_MICROSTEP = 1
LAN_STEP_US = 1500
AOV_STEPS_PER_REV = 4096
AOV_STEP_MS = 10

# Encoder settings
DETENT_DIV = 4
DEBOUNCE_MS = 200

# Altitude range: 200 km to 2000 km
MIN_ALTITUDE_KM = 200
MAX_ALTITUDE_KM = 2000

# ---------------- OLED init ----------------
OLED_W, OLED_H = 128, 64
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
addrs = i2c.scan()
if not addrs:
    raise SystemExit("No I2C OLED on I2C0 (GP4/GP5).")
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
    disp = SH1106_I2C(OLED_W, OLED_H, i2c, addr=ADDR); DRIVER="SH1106"
except Exception:
    from ssd1306 import SSD1306_I2C
    disp = SSD1306_I2C(OLED_W, OLED_H, i2c, addr=ADDR); DRIVER="SSD1306"

# ---------------- LAN Motor (DRV8834) ----------------
LAN_STEP  = Pin(14, Pin.OUT, value=0)
LAN_DIR   = Pin(15, Pin.OUT, value=0)
LAN_SLEEP = Pin(12, Pin.OUT, value=0)
LAN_ENBL  = Pin(13, Pin.OUT, value=1)
LAN_M0 = Pin(10, Pin.OUT, value=0)
LAN_M1 = Pin(11, Pin.OUT, value=0)

lan_enabled = False
lan_last_step_time = time.ticks_ms()

def lan_enable(on=True):
    global lan_enabled
    if on and not lan_enabled:
        LAN_SLEEP.value(1)
        time.sleep_ms(2)
        LAN_ENBL.value(0)
        lan_enabled = True
    elif (not on) and lan_enabled:
        LAN_ENBL.value(1)
        LAN_SLEEP.value(0)
        lan_enabled = False

def lan_step_pulse(us=LAN_STEP_US):
    global lan_last_step_time
    hi = max(2, us//2); lo = max(2, us - hi)
    LAN_STEP.value(1); time.sleep_us(hi)
    LAN_STEP.value(0); time.sleep_us(lo)
    lan_last_step_time = time.ticks_ms()

def lan_move_steps(steps):
    if steps == 0: return
    lan_enable(True)
    LAN_DIR.value(1 if steps > 0 else 0)
    for _ in range(abs(steps)):
        lan_step_pulse()

# ---------------- AOV Motor (ULN2003) ----------------
AOV_IN1 = Pin(2, Pin.OUT)
AOV_IN2 = Pin(3, Pin.OUT)
AOV_IN3 = Pin(22, Pin.OUT)
AOV_IN4 = Pin(26, Pin.OUT)

aov_half_step = [
    (1,0,0,0), (1,1,0,0), (0,1,0,0), (0,1,1,0),
    (0,0,1,0), (0,0,1,1), (0,0,0,1), (1,0,0,1),
]
aov_step_index = 0
aov_last_step_time = time.ticks_ms()

def aov_output_step(seq):
    AOV_IN1.value(seq[0])
    AOV_IN2.value(seq[1])
    AOV_IN3.value(seq[2])
    AOV_IN4.value(seq[3])

def aov_move_steps(steps):
    global aov_step_index, aov_last_step_time
    if steps == 0: return
    steps = -steps  # Reverse direction
    direction = 1 if steps > 0 else -1
    n = len(aov_half_step)
    for _ in range(abs(steps)):
        aov_output_step(aov_half_step[aov_step_index])
        time.sleep_ms(AOV_STEP_MS)
        if direction > 0:
            aov_step_index = (aov_step_index + 1) % n
        else:
            aov_step_index = (aov_step_index - 1 + n) % n
    aov_last_step_time = time.ticks_ms()

def aov_release():
    AOV_IN1.value(0); AOV_IN2.value(0)
    AOV_IN3.value(0); AOV_IN4.value(0)

# ---------------- Encoder ----------------
A  = Pin(6, Pin.IN, Pin.PULL_UP)
B  = Pin(7, Pin.IN, Pin.PULL_UP)
SW = Pin(8, Pin.IN, Pin.PULL_UP)

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

def compute_lan_rate_j2(altitude_km, inclination_deg=51.6):
    """Compute LAN rate including J2 precession and Earth rotation (deg/day)."""
    a = altitude_km + EARTH_RADIUS
    inc_rad = math.radians(inclination_deg)
    
    # Mean motion (rad/s)
    n = math.sqrt(EARTH_MU / (a**3))
    
    # J2 precession rate (rad/s) in inertial frame
    # dΩ/dt = -1.5 * n * J2 * (Re/a)² * cos(i)
    lan_rate_rad_s = -1.5 * n * EARTH_J2 * (EARTH_RADIUS / a)**2 * math.cos(inc_rad)
    
    # Convert to deg/day
    lan_j2_deg_day = math.degrees(lan_rate_rad_s) * 86400
    
    # Add Earth's rotation (360° per sidereal day)
    # Total apparent rate in Earth-fixed frame
    lan_total_deg_day = lan_j2_deg_day + EARTH_ROTATION_DEG_DAY
    
    return lan_total_deg_day

def compute_motor_rates(altitude_km):
    """Compute motor step rates for given altitude."""
    # Compute period from altitude
    period_min = compute_period_from_altitude(altitude_km)
    
    # AOV: 1 revolution per orbital period
    aov_steps_per_sec = AOV_STEPS_PER_REV / (period_min * 60.0)
    
    # LAN: rate from J2 effect + Earth rotation
    lan_rate_deg_day = compute_lan_rate_j2(altitude_km)
    lan_deg_per_sec = lan_rate_deg_day / 86400.0
    lan_steps_per_sec = (lan_deg_per_sec / 360.0) * LAN_STEPS_PER_REV
    
    return aov_steps_per_sec, lan_steps_per_sec, lan_rate_deg_day, period_min

# ---------------- State Machine ----------------
# State 0: Set altitude
# State 1: Set LAN position
# State 2: Set AOV position
# State 3: Run simulation
current_state = 0
last_button_time = 0

# Orbital parameters
orbital_altitude_km = 400.0  # Start at ISS altitude
orbital_period_min = 0.0  # Computed from altitude
lan_position_deg = 0.0
aov_position_deg = 0.0

# Motor positions (steps)
lan_position = 0
aov_position = 0

# Computed rates
aov_rate = 0.0
lan_rate = 0.0
lan_rate_deg_day = 0.0
orbital_period_min = 0.0

# Continuous motion accumulators
continuous_start_time = 0
continuous_aov_accumulator = 0.0
continuous_lan_accumulator = 0.0

# Encoder tracking
last_detent = 0

def poll_button():
    """Check for button press and advance state."""
    global current_state, last_button_time
    global continuous_start_time, continuous_aov_accumulator, continuous_lan_accumulator
    global aov_rate, lan_rate, lan_rate_deg_day
    
    if SW.value() == 0:  # pressed
        now = time.ticks_ms()
        if time.ticks_diff(now, last_button_time) > DEBOUNCE_MS:
            # Advance to next state
            current_state = (current_state + 1) % 4
            
            if current_state == 3:
                # Entering run state - compute motor rates
                aov_rate, lan_rate, lan_rate_deg_day, orbital_period_min = compute_motor_rates(orbital_altitude_km)
                continuous_start_time = time.ticks_ms()
                continuous_aov_accumulator = 0.0
                continuous_lan_accumulator = 0.0
            
            last_button_time = now
            # wait for release
            while SW.value() == 0:
                time.sleep_ms(10)

def update_from_encoder():
    """Update current parameter based on encoder and state."""
    global last_detent, orbital_altitude_km, lan_position_deg, aov_position_deg
    global lan_position, aov_position
    
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
            # Adjust LAN (1 degree per detent)
            lan_position_deg += delta * 1.0
            lan_position_deg = lan_position_deg % 360.0
            # Update motor position - take shortest path
            target_steps = int((lan_position_deg / 360.0) * LAN_STEPS_PER_REV)
            delta_steps = target_steps - lan_position
            # Wrap to shortest path: if delta > half revolution, go the other way
            if delta_steps > LAN_STEPS_PER_REV // 2:
                delta_steps -= LAN_STEPS_PER_REV
            elif delta_steps < -(LAN_STEPS_PER_REV // 2):
                delta_steps += LAN_STEPS_PER_REV
            if delta_steps != 0:
                lan_move_steps(delta_steps)
                lan_position = target_steps
        
        elif current_state == 2:
            # Adjust AOV (1 degree per detent)
            aov_position_deg += delta * 1.0
            aov_position_deg = aov_position_deg % 360.0
            # Update motor position - take shortest path
            target_steps = int((aov_position_deg / 360.0) * AOV_STEPS_PER_REV)
            delta_steps = target_steps - aov_position
            # Wrap to shortest path: if delta > half revolution, go the other way
            if delta_steps > AOV_STEPS_PER_REV // 2:
                delta_steps -= AOV_STEPS_PER_REV
            elif delta_steps < -(AOV_STEPS_PER_REV // 2):
                delta_steps += AOV_STEPS_PER_REV
            if delta_steps != 0:
                aov_move_steps(delta_steps)
                aov_position = target_steps

# ---------------- Main Loop ----------------
LAN_M0.value(0); LAN_M1.value(0)  # Full-step mode
lan_enable(False)
aov_release()

print("Orbigator - Orbital Mechanics Simulator")
print("State 0: Set Altitude | State 1: Set LAN")
print("State 2: Set AOV | State 3: Run")

# Motor idle timeout for running mode
MOTOR_IDLE_TIMEOUT_MS = 250

while True:
    time.sleep_ms(20)
    
    poll_button()
    
    if current_state == 3:
        # State 3: Run simulation with continuous motion
        continuous_aov_accumulator += aov_rate * 0.02  # 20ms loop
        continuous_lan_accumulator += lan_rate * 0.02
        
        if continuous_aov_accumulator >= 1.0:
            steps = int(continuous_aov_accumulator)
            aov_move_steps(steps)
            aov_position += steps
            continuous_aov_accumulator -= steps
        
        if continuous_lan_accumulator >= 1.0:
            steps = int(continuous_lan_accumulator)
            lan_move_steps(steps)
            lan_position += steps
            continuous_lan_accumulator -= steps
        
        # Auto-disable motors after idle timeout to save power
        now = time.ticks_ms()
        if lan_enabled and time.ticks_diff(now, lan_last_step_time) > MOTOR_IDLE_TIMEOUT_MS:
            lan_enable(False)
        if time.ticks_diff(now, aov_last_step_time) > MOTOR_IDLE_TIMEOUT_MS:
            aov_release()
    else:
        # States 0-2: Encoder control
        update_from_encoder()
    
    # Display
    disp.fill(0)
    disp.text("Orbigator", 0, 0)
    
    if current_state == 0:
        disp.text("Set Altitude:", 0, 12)
        disp.text("{:.0f} km".format(orbital_altitude_km), 0, 24)
        period = compute_period_from_altitude(orbital_altitude_km)
        disp.text("T: {:.1f}min".format(period), 0, 36)
    
    elif current_state == 1:
        disp.text("Set LAN:", 0, 12)
        disp.text("{:.1f} deg".format(lan_position_deg), 0, 24)
        disp.text("Alt: {:.0f}km".format(orbital_altitude_km), 0, 36)
    
    elif current_state == 2:
        disp.text("Set AOV:", 0, 12)
        disp.text("{:.1f} deg".format(aov_position_deg), 0, 24)
        disp.text("LAN: {:.1f}d".format(lan_position_deg), 0, 36)
    
    else:  # State 3: Running
        disp.text("RUNNING", 0, 12)
        disp.text("T:{:.0f}m".format(orbital_period_min), 0, 24)
        aov_deg = (aov_position / AOV_STEPS_PER_REV) * 360
        lan_deg = (lan_position / LAN_STEPS_PER_REV) * 360
        disp.text("A:{:.0f} L:{:.0f}".format(aov_deg, lan_deg), 0, 36)
        disp.text("dL:{:.2f}d/d".format(lan_rate_deg_day), 0, 48)
    
    disp.show()

