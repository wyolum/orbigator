# Pico 2 | Encoder +/-1 per detent | OLED (auto SH1106/SSD1306)
# I2C0: SDA=GP4, SCL=GP5 | Encoder: A=GP6, B=GP7, SW=GP8 (COM wired accordingly)

import machine, time
from machine import Pin, I2C
import framebuf

# --- user options ---
DETENT_DIV     = 4        # edges per detent (most encoders = 4)
REVERSE        = False    # flip rotation direction
ZERO_HOLD_MS   = 300      # require >= this many ms pressed to zero
SW_ACTIVE_LOW  = False    # <-- set False if your button is active-HIGH (pressed==1)

# --- OLED detect (SH1106 preferred, SSD1306 fallback) ---
OLED_W, OLED_H = 128, 64
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
addrs = i2c.scan()
if not addrs: raise SystemExit("No I2C OLED on I2C0.")
ADDR = addrs[0]

class SH1106_I2C:
    def __init__(self, w,h,i2c,addr=0x3C):
        self.width, self.height, self.i2c, self.addr = w,h,i2c,addr
        self.buffer = bytearray(w*h//8)
        self.fb = framebuf.FrameBuffer(self.buffer, w, h, framebuf.MONO_VLSB)
        def cmd(*cs):
            for c in cs: self.i2c.writeto(self.addr, b'\x00'+bytes([c]))
        cmd(0xAE,0x20,0x00,0x40,0xA1,0xC8,0x81,0x7F,0xA6,0xA8,0x3F,
            0xAD,0x8B,0xD3,0x00,0xD5,0x80,0xD9,0x22,0xDA,0x12,0xDB,0x35,0xAF)
        self.fill(0); self.show()
    def fill(self,c): self.fb.fill(c)
    def text(self,s,x,y,c=1): self.fb.text(s,x,y,c)
    def fill_rect(self,x,y,w,h,c=1): self.fb.fill_rect(x,y,w,h,c)
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

# --- encoder (4x quadrature) ---
A  = Pin(6, Pin.IN, Pin.PULL_UP)
B  = Pin(7, Pin.IN, Pin.PULL_UP)
# Configure button pull & logic based on SW_ACTIVE_LOW
SW = Pin(8, Pin.IN, Pin.PULL_UP if SW_ACTIVE_LOW else Pin.PULL_DOWN)

state = (A.value()<<1) | B.value()
raw = 0; pos = 0; last_det = 0

TRANS = (0,+1,-1,0,  -1,0,0,+1,  +1,0,0,-1,  0,-1,+1,0)

def _enc_isr(_):
    global state, raw
    s = (A.value()<<1) | B.value()
    d = TRANS[(state<<2)|s]
    if REVERSE: d = -d
    raw += d
    state = s

A.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)
B.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)

# --- button polling with debounce & hold-to-zero ---
sw_last = SW.value()
sw_press_start = None

def sw_pressed_now():
    v = SW.value()
    return (v == 0) if SW_ACTIVE_LOW else (v == 1)

def poll_button_and_maybe_zero():
    global sw_last, sw_press_start, raw, pos, last_det
    v = SW.value()
    if v != sw_last:
        sw_last = v
        if sw_pressed_now():
            sw_press_start = time.ticks_ms()
        else:
            sw_press_start = None
    if sw_press_start is not None:
        if time.ticks_diff(time.ticks_ms(), sw_press_start) >= ZERO_HOLD_MS:
            raw = 0; pos = 0; last_det = 0
            sw_press_start = None

# --- main loop ---
t0 = time.ticks_ms()
prev_raw = 0
while True:
    time.sleep_ms(40)
         poll_button_and_maybe_zero()

    now = time.ticks_ms()
    dt = max(1, time.ticks_diff(now,t0))/1000.0
    irq = machine.disable_irq(); r = raw; machine.enable_irq(irq)

    det  = r // DETENT_DIV
    step = det - last_det
    if step:
        pos += step
        last_det = det

    cps = (r - prev_raw)/dt
    prev_raw = r; t0 = now

    disp.fill(0)
    disp.text("Orbigator", 0, 0)
    disp.text("Raw: {}".format(r), 0, 12)
    disp.text("Det: {}".format(det), 0, 24)
    disp.text("CPS:{:.1f}".format(cps), 0, 36)
    s = str(pos); x0 = max(0, (OLED_W - len(s)*8)//2)
    disp.text(s, x0, 48); disp.text(s, x0+1, 48)
    disp.show()
