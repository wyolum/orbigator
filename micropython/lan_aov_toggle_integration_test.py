# Pico 2 | Encoder toggles between LAN & AOV motors | OLED display
# LAN Motor (DRV8834): STEP=GP14, DIR=GP15, nSLEEP=GP12, nENBL=GP13, M0=GP10, M1=GP11
# AOV Motor (ULN2003): IN1=GP2, IN2=GP3, IN3=GP22, IN4=GP26
# Encoder (COM/CON -> GND): A=GP6, B=GP7, SW=GP8  (pull-ups)
# OLED (SH1106/SSD1306 auto): I2C0 SDA=GP4, SCL=GP5

import machine, time
from machine import Pin, I2C
import framebuf

# ---------------- User settings ----------------
# LAN motor (DRV8834)
LAN_STEPS_PER_REV = 200          # 1.8° stepper
LAN_MICROSTEP = 1                # FULL-STEP
LAN_STEP_US = 1500               # µs per step

# AOV motor (ULN2003)
AOV_STEPS_PER_REV = 4096         # 28BYJ-48 half-steps per rev
AOV_STEP_MS = 10                 # ms per half-step

# Encoder
DETENT_DIV = 4                   # edges per detent
LAN_STEPS_PER_DETENT = 1         # LAN: steps per detent click
AOV_STEPS_PER_DETENT = 6         # AOV: 6 half-steps = ~0.527° per click
REVERSE_ENCODER = False

# Motor control
MOTOR_IDLE_TIMEOUT_MS = 500      # disable after inactivity
DEBOUNCE_MS = 200                # button debounce time

# ---------------- OLED detect & init ----------------
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

# ---------------- LAN Motor (DRV8834) pins ----------------
LAN_STEP  = Pin(14, Pin.OUT, value=0)
LAN_DIR   = Pin(15, Pin.OUT, value=0)
LAN_SLEEP = Pin(12, Pin.OUT, value=0)   # 0=sleep, 1=awake
LAN_ENBL  = Pin(13, Pin.OUT, value=1)   # active-LOW: 1=disabled
LAN_M0 = Pin(10, Pin.OUT, value=0)      # LOW for full-step
LAN_M1 = Pin(11, Pin.OUT, value=0)      # LOW for full-step

lan_enabled = False
lan_last_step_time = time.ticks_ms()

def lan_set_fullstep():
    LAN_M0.value(0); LAN_M1.value(0)
    time.sleep_ms(2)

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
    """Move LAN motor by steps (positive or negative)."""
    if steps == 0:
        return
    lan_enable(True)
    LAN_DIR.value(1 if steps > 0 else 0)
    for _ in range(abs(steps)):
        lan_step_pulse()

# ---------------- AOV Motor (ULN2003) pins ----------------
AOV_IN1 = Pin(2, Pin.OUT)
AOV_IN2 = Pin(3, Pin.OUT)
AOV_IN3 = Pin(22, Pin.OUT)
AOV_IN4 = Pin(26, Pin.OUT)

# 28BYJ-48 half-step sequence
aov_half_step = [
    (1,0,0,0),
    (1,1,0,0),
    (0,1,0,0),
    (0,1,1,0),
    (0,0,1,0),
    (0,0,1,1),
    (0,0,0,1),
    (1,0,0,1),
]
aov_step_index = 0
aov_last_step_time = time.ticks_ms()

def aov_output_step(seq):
    AOV_IN1.value(seq[0])
    AOV_IN2.value(seq[1])
    AOV_IN3.value(seq[2])
    AOV_IN4.value(seq[3])

def aov_move_steps(steps):
    """Move AOV motor by steps (half-steps, positive or negative)."""
    global aov_step_index, aov_last_step_time
    if steps == 0:
        return

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
    """Release AOV motor coils."""
    AOV_IN1.value(0)
    AOV_IN2.value(0)
    AOV_IN3.value(0)
    AOV_IN4.value(0)

# ---------------- Encoder pins (COM/CON -> GND => pull-ups) ----------------
A  = Pin(6, Pin.IN, Pin.PULL_UP)
B  = Pin(7, Pin.IN, Pin.PULL_UP)
SW = Pin(8, Pin.IN, Pin.PULL_UP)

# Encoder state (4x quadrature)
state = (A.value()<<1) | B.value()
raw_count = 0
detents = 0
last_det = 0

TRANS = (0,+1,-1,0,  -1,0,0,+1,  +1,0,0,-1,  0,-1,+1,0)

def _enc_isr(_):
    global state, raw_count
    s = (A.value()<<1) | B.value()
    d = TRANS[(state<<2)|s]
    if REVERSE_ENCODER: d = -d
    raw_count += d
    state = s

A.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)
B.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)

# ---------------- Button handling (3-state system) ----------------
# State 0: Encoder controls LAN motor
# State 1: Encoder controls AOV motor  
# State 2: Continuous motion (AOV: 1 rev/90min, LAN: 2°/9min)
current_state = 0
last_button_time = 0

# Continuous motion settings for State 2
# AOV: 1 rev per 90 minutes = 4096 steps per 5400 seconds = 0.758 steps/sec
# LAN: 2 deg per 9 minutes = (2/360)*200 steps per 540 sec = 0.00206 steps/sec
AOV_CONTINUOUS_STEPS_PER_SEC = 4096.0 / 5400.0  # ~0.758 steps/sec
LAN_CONTINUOUS_STEPS_PER_SEC = (2.0 / 360.0) * 200.0 / 540.0  # ~0.00206 steps/sec

continuous_start_time = 0
continuous_aov_accumulator = 0.0
continuous_lan_accumulator = 0.0

def poll_button():
    """Check for button press and cycle through states."""
    global current_state, last_button_time
    global continuous_start_time, continuous_aov_accumulator, continuous_lan_accumulator
    
    if SW.value() == 0:  # pressed (pull-up)
        now = time.ticks_ms()
        if time.ticks_diff(now, last_button_time) > DEBOUNCE_MS:
            # Cycle to next state
            current_state = (current_state + 1) % 3
            
            if current_state == 2:
                # Entering continuous motion state
                continuous_start_time = time.ticks_ms()
                continuous_aov_accumulator = 0.0
                continuous_lan_accumulator = 0.0
            
            last_button_time = now
            # wait for release
            while SW.value() == 0:
                time.sleep_ms(10)

# ---------------- Motor position tracking ----------------
lan_position = 0
aov_position = 0
lan_target = 0
aov_target = 0

def update_target_from_encoder():
    """Read encoder and update target for active motor based on current state."""
    global detents, last_det, lan_target, aov_target
    irq = machine.disable_irq(); rc = raw_count; machine.enable_irq(irq)
    d = rc // DETENT_DIV
    if d != last_det:
        step_det = d - last_det
        last_det = d
        detents = d
        if current_state == 0:  # LAN control
            lan_target += step_det * LAN_STEPS_PER_DETENT
        elif current_state == 1:  # AOV control
            aov_target += step_det * AOV_STEPS_PER_DETENT
        # State 2 (continuous motion) ignores encoder input

def move_towards_targets(max_steps=40):
    """Move motors toward their targets."""
    global lan_position, aov_position

    # LAN motor
    delta = lan_target - lan_position
    if delta != 0:
        steps = min(abs(delta), max_steps) if abs(delta) > max_steps else abs(delta)
        direction = 1 if delta > 0 else -1
        lan_move_steps(direction * steps)
        lan_position += direction * steps

    # AOV motor
    delta = aov_target - aov_position
    if delta != 0:
        steps = min(abs(delta), max_steps) if abs(delta) > max_steps else abs(delta)
        direction = 1 if delta > 0 else -1
        aov_move_steps(direction * steps)
        aov_position += direction * steps

# ---------------- Main loop ----------------
lan_set_fullstep()
lan_enable(False)
aov_release()

print("LAN/AOV 3-State Integration Test")
print("State 0: Encoder controls LAN motor")
print("State 1: Encoder controls AOV motor")
print("State 2: Continuous motion (AOV: 1rev/90min, LAN: 2deg/9min)")
print("Button press cycles through states")


while True:
    time.sleep_ms(20)

    poll_button()
    
    if current_state == 2:
        # State 2: Continuous motion - move both motors at specified rates
        now = time.ticks_ms()
        elapsed_sec = time.ticks_diff(now, continuous_start_time) / 1000.0
        
        # Calculate how many steps should have been taken by now
        target_aov_steps = elapsed_sec * AOV_CONTINUOUS_STEPS_PER_SEC
        target_lan_steps = elapsed_sec * LAN_CONTINUOUS_STEPS_PER_SEC
        
        # Calculate steps to take this iteration (using accumulators for fractional steps)
        continuous_aov_accumulator += AOV_CONTINUOUS_STEPS_PER_SEC * 0.02  # 20ms loop
        continuous_lan_accumulator += LAN_CONTINUOUS_STEPS_PER_SEC * 0.02
        
        # Take integer steps when accumulator >= 1
        if continuous_aov_accumulator >= 1.0:
            steps_to_take = int(continuous_aov_accumulator)
            aov_move_steps(steps_to_take)
            aov_position += steps_to_take
            continuous_aov_accumulator -= steps_to_take
        
        if continuous_lan_accumulator >= 1.0:
            steps_to_take = int(continuous_lan_accumulator)
            lan_move_steps(steps_to_take)
            lan_position += steps_to_take
            continuous_lan_accumulator -= steps_to_take
    else:
        # State 0 or 1: Encoder control mode
        update_target_from_encoder()
        move_towards_targets()

        # Auto-disable LAN motor if idle
        if lan_enabled and time.ticks_diff(time.ticks_ms(), lan_last_step_time) > MOTOR_IDLE_TIMEOUT_MS:
            lan_enable(False)

        # Auto-release AOV motor if idle
        if time.ticks_diff(time.ticks_ms(), aov_last_step_time) > MOTOR_IDLE_TIMEOUT_MS:
            aov_release()

    # Display
    disp.fill(0)
    disp.text("{} LAN/AOV".format(DRIVER), 0, 0)

    # Show state
    if current_state == 0:
        state_name = "State 0: LAN"
    elif current_state == 1:
        state_name = "State 1: AOV"
    else:
        state_name = "State 2: AUTO"
    disp.text(state_name, 0, 12)

    # Show LAN position
    lan_rev = lan_position / (LAN_STEPS_PER_REV * LAN_MICROSTEP)
    disp.text("LAN: {:.2f} rev".format(lan_rev), 0, 24)

    # Show AOV position
    aov_deg = (aov_position / AOV_STEPS_PER_REV) * 360
    disp.text("AOV: {:.1f} deg".format(aov_deg), 0, 36)

    # Show motor status
    status = "ON" if (lan_enabled or (time.ticks_diff(time.ticks_ms(), aov_last_step_time) < MOTOR_IDLE_TIMEOUT_MS)) else "OFF"
    disp.text("Motor: {}".format(status), 0, 48)

    disp.show()

