# Orbigator - Orbital Mechanics Simulator
# Pico 2 | DYNAMIXEL XL330-M288-T motors
# ------------------------------------------------------------------

import machine, time, math, json
from machine import Pin, I2C
import framebuf
from ds3231 import DS3231
from dynamixel_motor import DynamixelMotor
from dynamixel_extended_utils import set_extended_mode
import orb_globals as g
import orb_utils as utils
import orb_utils as utils
import pins
from modes import MenuMode, OrbitMode, DatetimeEditorMode

# ---------------- Hardware Config ----------------
AOV_MOTOR_ID = 2
EQX_MOTOR_ID = 1
EQX_GEAR_RATIO = 120.0 / 11.0
AOV_GEAR_RATIO = 1.0

DETENT_DIV = 4
DEBOUNCE_MS = 200

# ---------------- OLED Init ----------------
OLED_W, OLED_H = 128, 64
i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=100_000)
addrs = i2c.scan()

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
        disp = SH1106_I2C(OLED_W, OLED_H, i2c, addr=addrs[0])
        g.disp = disp
    else:
        raise Exception("No display")
except Exception:
    class DummyDisp:
        def fill(self,c): pass
        def text(self,s,x,y,c=1): pass
        def show(self): pass
    disp = DummyDisp(); g.disp = disp

# ---------------- RTC Init ----------------
try:
    rtc = DS3231(i2c)
    g.rtc = rtc
    utils.sync_system_time(rtc)
    if rtc.datetime() is not None:
        print("RTC found and initialized.")
except Exception:
    print("RTC init failed.")
    g.rtc = None

# ---------------- Motor Init ----------------
print("\nInitializing DYNAMIXEL motors...")
set_extended_mode(AOV_MOTOR_ID)
set_extended_mode(EQX_MOTOR_ID)

aov_motor = DynamixelMotor(AOV_MOTOR_ID, "AoV", gear_ratio=AOV_GEAR_RATIO)
g.aov_motor = aov_motor
eqx_motor = DynamixelMotor(EQX_MOTOR_ID, "EQX", gear_ratio=EQX_GEAR_RATIO)
g.eqx_motor = eqx_motor

aov_motor.set_speed_limit(3) # Capped at 3 for safety
eqx_motor.set_speed_limit(10) # Capped at 10 for safety

# ---------------- Encoder + Buttons ----------------
# ---------------- Encoder + Buttons ----------------
enc_a = Pin(pins.ENC_A_PIN, Pin.IN, Pin.PULL_UP)
enc_b = Pin(pins.ENC_B_PIN, Pin.IN, Pin.PULL_UP)
enc_btn = Pin(pins.ENC_BTN_PIN, Pin.IN, Pin.PULL_UP)
BACK_BTN = Pin(pins.BACK_BTN_PIN, Pin.IN, Pin.PULL_UP)
CONFIRM_BTN = Pin(pins.CONFIRM_BTN_PIN, Pin.IN, Pin.PULL_UP)

state = (enc_a.value()<<1) | enc_b.value()
raw_count = 0
TRANS = (0,+1,-1,0,  -1,0,0,+1,  +1,0,0,-1,  0,-1,+1,0)

def _enc_isr(_):
    global state, raw_count
    s = (enc_a.value()<<1) | enc_b.value()
    d = TRANS[(state<<2)|s]
    raw_count -= d
    state = s

enc_a.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)
enc_b.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)
sw_irq_configured = False # Debounce logic handles SW manually

# ---------------- State and Loop ----------------
# Check for RTC reset (e.g. battery failure)
if time.time() < 60:
    print("RTC Reset detected! Prompting for time.")
    current_mode = DatetimeEditorMode(next_mode=OrbitMode())
else:
    current_mode = OrbitMode()
current_mode.enter()

last_detent = 0
last_sw_btn = 1
last_back_btn = 1
last_confirm_btn = 1
last_btn_time = 0
last_display_update = 0

print("Orbigator Ready.")

while True:
    time.sleep_ms(10)
    now = time.ticks_ms()
    
    # 1. Poll Encoder Rotation
    irq = machine.disable_irq(); rc = raw_count; machine.enable_irq(irq)
    d = rc // DETENT_DIV
    if d != last_detent:
        delta = d - last_detent
        last_detent = d
        current_mode.on_encoder_rotate(delta)
        
    # 2. Poll Encoder Press (SW)
    sw_val = SW.value()
    if sw_val == 0 and last_sw_btn == 1:
        if time.ticks_diff(now, last_btn_time) > DEBOUNCE_MS:
            last_btn_time = now
            current_mode.on_encoder_press()
    last_sw_btn = sw_val
    
    # 3. Poll Back Button (GP9)
    back_val = BACK_BTN.value()
    if back_val == 0 and last_back_btn == 1:
        if time.ticks_diff(now, last_btn_time) > DEBOUNCE_MS:
            last_btn_time = now
            new_mode = current_mode.on_back()
            if new_mode:
                current_mode.exit()
                current_mode = new_mode
                current_mode.enter()
    last_back_btn = back_val
    
    # 4. Poll Confirm Button (GP10)
    confirm_val = CONFIRM_BTN.value()
    if confirm_val == 0 and last_confirm_btn == 1:
        if time.ticks_diff(now, last_btn_time) > DEBOUNCE_MS:
            last_btn_time = now
            new_mode = current_mode.on_confirm()
            if new_mode:
                current_mode.exit()
                current_mode = new_mode
                current_mode.enter()
    last_confirm_btn = confirm_val
    
    # 5. Update and Render
    current_mode.update(now)
    
    if time.ticks_diff(now, last_display_update) >= 200:
        last_display_update = now
        current_mode.render(disp)
