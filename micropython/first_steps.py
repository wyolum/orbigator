from machine import Pin
import time

PI = 3.14159

# ---- CORE PINS (Pico 2) ----
STEP  = Pin(14, Pin.OUT, value=0)
DIR   = Pin(15, Pin.OUT, value=0)
ENBL  = Pin(13, Pin.OUT, value=1)   # active-LOW: 1=disabled, 0=enabled
SLEEP = Pin(12, Pin.OUT, value=0)   # 0=sleep, 1=awake
LED   = Pin("LED", Pin.OUT, value=0)

# ---- MICROSTEP CONTROL (wire GP10->M0, GP11->M1) ----
M0 = Pin(10, Pin.IN)                # hi-Z = FLOAT
M1 = Pin(11, Pin.OUT, value=1)      # start HIGH (paired w/ M0 FLOAT => 1/32)

MOTOR_STEPS_PER_REV = 200                 # your motor (1.8°)
GEAR_RATIO = 60/7
GLOBE_STEPS_PER_REV = GEAR_RATIO * MOTOR_STEPS_PER_REV
GLOBE_ROTATION_PER_STEP = 2 * PI / GLOBE_STEPS_PER_REV

ORBIT_PERIOD = 90 * 60 ### 90 minutes per rev roughly
EARTH_ROTATION_PER_ORBIT = ORBIT_PERIOD * 2 * PI/86400
STEPS_PER_ORBIT = EARTH_ROTATION_PER_ORBIT / GLOBE_ROTATION_PER_STEP
STEP_INTERVAL =  ORBIT_PERIOD / STEPS_PER_ORBIT

# ---- DRV8834 microstep helpers (Pico 2) ----
class DRV8834Microstep:
    """Control DRV8834 microstepping via M0/M1."""
    def __init__(self, m0_pin=10, m1_pin=11, settle_ms=2):
        self.m0 = Pin(m0_pin, Pin.IN)             # hi-Z (FLOAT)
        self.m1 = Pin(m1_pin, Pin.OUT, value=0)   # LOW
        self.settle_ms = settle_ms
        self._factor = 4                          # M0 FLOAT + M1 LOW = 1/4-step

    # --- low-level pin states ---
    def _m0_float(self): self.m0.init(Pin.IN)                 # hi-Z (FLOAT)
    def _m0_low(self):   self.m0.init(Pin.OUT); self.m0.value(0)
    def _m0_high(self):  self.m0.init(Pin.OUT); self.m0.value(1)
    def _m1_low(self):   self.m1.init(Pin.OUT); self.m1.value(0)
    def _m1_high(self):  self.m1.init(Pin.OUT); self.m1.value(1)

    def _apply(self, m0, m1, factor):
        {"float": self._m0_float, "low": self._m0_low, "high": self._m0_high}[m0]()
        {"low": self._m1_low,     "high": self._m1_high}[m1]()
        time.sleep_ms(self.settle_ms)
        self._factor = factor
        return factor

    # --- ready-made modes ---
    def full(self):         return self._apply("low",   "low",  1)   # 1/1
    def half(self):         return self._apply("high",  "low",  2)   # 1/2
    def quarter(self):      return self._apply("float", "low",  4)   # 1/4
    def eighth(self):       return self._apply("low",   "high", 8)   # 1/8
    def sixteenth(self):    return self._apply("high",  "high", 16)  # 1/16
    def thirtysecond(self): return self._apply("float", "high", 32)  # 1/32

    # one-call convenience
    def set(self, mode):
        s = str(mode).lower()
        if s in ("full","1","1/1"):            return self.full()
        if s in ("half","1/2"):                return self.half()
        if s in ("quarter","1/4"):             return self.quarter()
        if s in ("eighth","1/8"):              return self.eighth()
        if s in ("sixteenth","1/16"):          return self.sixteenth()
        if s in ("thirtysecond","1/32"):       return self.thirtysecond()
        raise ValueError("Use: full, 1/2, 1/4, 1/8, 1/16, or 1/32")

    @property
    def factor(self): return self._factor

    def pulses_per_rev(self, motor_steps=200):
        """Return pulses for one shaft revolution."""
        return motor_steps * self._factor

def set_microstep_132():
    """DRV8834: M0 = FLOAT, M1 = HIGH -> 1/32 step (smallest)."""
    M0.init(Pin.IN)                 # FLOAT (no pull) = hi-Z
    M1.init(Pin.OUT); M1.value(1)   # force HIGH
    time.sleep_ms(2)                # let the driver settle

def blink(n, on_ms=120, off_ms=120):
    for _ in range(n):
        LED.value(1); time.sleep_ms(on_ms)
        LED.value(0); time.sleep_ms(off_ms)

def driver_enable(on=True):
    if on:
        SLEEP.value(1)              # wake
        time.sleep_ms(2)
        ENBL.value(0)               # enable outputs
        #blink(2, 120, 120)          # cue
    else:
        ENBL.value(1)
        SLEEP.value(0)
        #blink(1, 200, 200)

def step_pulse(delay_us=1500):
    # DRV8834 needs ~≥1.9 us HIGH and LOW. Keep delay_us >= 4 to be safe.
    hi = max(2, delay_us // 2)
    lo = max(2, delay_us - hi)
    STEP.value(1); time.sleep_us(hi)
    STEP.value(0); time.sleep_us(lo)

def move(steps, delay_us=1500):
    if steps > 0:
        direction = 1
    else:
        direction = -1
        steps = abs(int(steps))
    DIR.value(1 if direction > 0 else 0)
    LED.value(1)                    # solid during motion
    for _ in range(abs(int(steps))):
        step_pulse(delay_us)
    LED.value(0)

def pulses_per_rev(microstep=32):
    return MOTOR_STEPS_PER_REV * microstep

# after you define ENBL/SLEEP etc.

if __name__ == "__main__":
    blink(3, 100, 100)
    ms = DRV8834Microstep()           # GP10/GP11 by default
    ENBL.value(1)                     # disable driver (active-LOW)
    ms.thirtysecond()                 # 1/32-step (smallest)
    ENBL.value(0)                     # re-enable
    ppr = ms.pulses_per_rev(200)      # e.g., 200 * 32 = 6400
    count = 0
    while True:
        ms.thirtysecond()
        driver_enable(True)
        #move(-ms._factor, delay_us=1000)
        ms.eighth()
        print(count); count+=1
        move(-800, delay_us=1500)
        move(800, delay_us=1500)
        driver_enable(False)
        #time.sleep_ms(STEP_INTERVAL)
        time.sleep(1)
