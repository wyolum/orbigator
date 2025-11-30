# Pico 2 | Encoder-jogs-Stepper + OLED | FULL-STEP @ 1500 us
# Stepper (DRV8834): STEP=GP14, DIR=GP15, nSLEEP=GP12, nENBL=GP13, M0=GP10, M1=GP11
# Encoder (COM/CON -> GND): A=GP6, B=GP7, SW=GP8  (pull-ups)
# OLED (SH1106/SSD1306 auto): I2C0 SDA=GP4, SCL=GP5

import machine, time
from machine import Pin, I2C
import framebuf

# ---------------- User settings ----------------
STEPS_PER_REV     = 200          # 1.8° stepper
MICROSTEP_FACTOR  = 1            # FULL-STEP
DETENT_DIV        = 4            # edges per detent (most encoders = 4)
STEPS_PER_DETENT  = 1            # jog size per detent (in FULL steps)
STEP_US_MIN       = 1500         # µs per step at speed (>=2)
STEP_US_MAX       = 1500         # µs per step when starting/stopping (>=2) — no ramp
ZERO_HOLD_MS      = 300          # hold button >= this to zero
MOTOR_IDLE_TIMEOUT_MS = 500      # disable driver after this much inactivity
REVERSE_ENCODER   = False        # flip knob direction if needed

# ---------------- OLED detect ----------------
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

# ---------------- Stepper pins ----------------
STEP  = Pin(14, Pin.OUT, value=0)
DIR   = Pin(15, Pin.OUT, value=0)
SLEEP = Pin(12, Pin.OUT, value=0)   # 0=sleep, 1=awake
ENBL  = Pin(13, Pin.OUT, value=1)   # active-LOW: 1=disabled

# Microstep mode lines (force FULL-STEP)
M0 = Pin(10, Pin.OUT, value=0)      # LOW
M1 = Pin(11, Pin.OUT, value=0)      # LOW
def set_fullstep():
    M0.value(0); M1.value(0)
    time.sleep_ms(2)

# ---------------- Encoder pins (COM/CON -> GND => pull-ups) ----------------
A  = Pin(6, Pin.IN, Pin.PULL_UP)
B  = Pin(7, Pin.IN, Pin.PULL_UP)
SW = Pin(8, Pin.IN, Pin.PULL_UP)

# ---------------- Encoder state (4x quadrature) ----------------
state = (A.value()<<1) | B.value()
raw_count = 0        # edges
detents   = 0        # edges // DETENT_DIV
abs_pos   = 0        # absolute detent count (+/-)
last_det  = 0

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

# ---------------- Button (polled, long-press to zero) ----------------
sw_last = SW.value()
sw_down_start = None
def poll_button():
    """Zero once on long-press; returns True if zeroed."""
    global sw_last, sw_down_start, abs_pos, raw_count, last_det, detents, target_pulses
    v = SW.value()  # 0 = pressed (pull-up)
    now = time.ticks_ms()
    if v != sw_last:
        sw_last = v
        if v == 0:
            sw_down_start = now
        else:
            sw_down_start = None
    if sw_down_start is not None and time.ticks_diff(now, sw_down_start) >= ZERO_HOLD_MS:
        abs_pos = 0
        raw_count = 0
        last_det = 0
        detents = 0
        target_pulses = 0
        sw_down_start = None
        return True
    return False

# ---------------- Stepper helpers with auto-enable/disable ----------------
last_step_time = time.ticks_ms()
motor_enabled = False

def driver_enable(on=True):
    """Gate the DRV8834 power. Wake before first step; sleep when idle."""
    global motor_enabled
    if on and not motor_enabled:
        SLEEP.value(1)
        time.sleep_ms(2)   # wake time
        ENBL.value(0)
        motor_enabled = True
    elif (not on) and motor_enabled:
        ENBL.value(1)
        SLEEP.value(0)
        motor_enabled = False

def step_pulse(us=STEP_US_MIN):
    """One STEP pulse (>= ~2 us high & low)."""
    global last_step_time
    hi = max(2, us//2); lo = max(2, us - hi)
    STEP.value(1); time.sleep_us(hi)
    STEP.value(0); time.sleep_us(lo)
    last_step_time = time.ticks_ms()

# motor position bookkeeping (in pulses; here pulses == FULL steps)
PULSES_PER_REV = STEPS_PER_REV * MICROSTEP_FACTOR  # = 200 in full-step
target_pulses = 0
current_pulses = 0

def jog_from_encoder():
    """Read encoder detents and update target pulses."""
    global detents, last_det, abs_pos, target_pulses
    irq = machine.disable_irq(); rc = raw_count; machine.enable_irq(irq)
    d = rc // DETENT_DIV
    if d != last_det:
        step_det = d - last_det
        last_det = d
        detents = d
        abs_pos += step_det
        target_pulses += step_det * STEPS_PER_DETENT

def move_towards_target(max_pulses_per_loop=40):
    """Walk a few pulses toward target each loop (keeps UI responsive)."""
    global current_pulses
    delta = target_pulses - current_pulses
    if delta == 0:
        return

    # ensure driver is awake/enabled before stepping
    driver_enable(True)

    direction = 1 if delta > 0 else -1
    DIR.value(1 if direction > 0 else 0)

    steps = min(abs(delta), max_pulses_per_loop)
    for _ in range(steps):
        step_pulse(STEP_US_MIN)   # fixed 1500 us full-step
        current_pulses += direction

# ---------------- Main ----------------
set_fullstep()            # force FULL-STEP on M0/M1
driver_enable(False)      # start disabled (cool & quiet)

t0 = time.ticks_ms()
while True:
    time.sleep_ms(20)

    poll_button()
    jog_from_encoder()
    move_towards_target()

    # auto-disable if idle long enough
    if motor_enabled and time.ticks_diff(time.ticks_ms(), last_step_time) > MOTOR_IDLE_TIMEOUT_MS:
        driver_enable(False)

    # UI
    disp.fill(0)
    disp.text("{} ENC+STEP".format(DRIVER), 0, 0)
    disp.text("Det:{} Abs:{}".format(detents, abs_pos), 0, 12)
    disp.text("Tgt:{:d}  Pos:{:d}".format(target_pulses, current_pulses), 0, 24)
    disp.text("Rev:{:.3f}".format(current_pulses / PULSES_PER_REV), 0, 36)
    disp.text("Mode: FULL  1.5ms", 0, 48)
    disp.text("Motor: {}".format("ON" if motor_enabled else "OFF"), 0, 56)

    disp.show()
