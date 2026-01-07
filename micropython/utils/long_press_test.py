# Long Press Test - Diagnose button long press detection
# Encoder: SW=GP8 (pull-up)
# OLED: I2C0 SDA=GP4, SCL=GP5

import machine, time
from machine import Pin, I2C
import framebuf

# ---------------- OLED init ----------------
OLED_W, OLED_H = 128, 64
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
addrs = i2c.scan()
if not addrs:
    print("No I2C devices found.")
ADDR = addrs[0] if addrs else 0x3C

class SH1106_I2C:
    def __init__(self, w,h,i2c,addr=0x3C):
        self.width,self.height,self.i2c,self.addr = w,h,i2c,addr
        self.buffer = bytearray(w*h//8)
        self.fb = framebuf.FrameBuffer(self.buffer, w, h, framebuf.MONO_VLSB)
        def cmd(*cs):
            for c in cs: self.i2c.writeto(self.addr, b'\\x00'+bytes([c]))
        cmd(0xAE,0x20,0x00,0x40,0xA1,0xC8,0x81,0x7F,0xA6,0xA8,0x3F,
            0xAD,0x8B,0xD3,0x00,0xD5,0x80,0xD9,0x22,0xDA,0x12,0xDB,0x35,0xAF)
        self.fill(0); self.show()
    def fill(self,c): self.fb.fill(c)
    def text(self,s,x,y,c=1): self.fb.text(s,x,y,c)
    def show(self):
        for p in range(self.height//8):
            self.i2c.writeto(self.addr, b'\\x00'+bytes([0xB0+p,0x02,0x10]))
            s = self.width*p; e = s+self.width
            self.i2c.writeto(self.addr, b'\\x40'+self.buffer[s:e])

try:
    disp = SH1106_I2C(OLED_W, OLED_H, i2c, addr=ADDR)
except:
    class DummyDisp:
        def fill(self, c): pass
        def text(self, s, x, y, c=1): pass
        def show(self): pass
    disp = DummyDisp()

# ---------------- Button ----------------
SW = Pin(8, Pin.IN, Pin.PULL_UP)

DEBOUNCE_MS = 200
LONG_PRESS_MS = 1000

last_button_time = 0
press_start_time = 0
button_down = False
short_press_count = 0
long_press_count = 0
last_press_duration = 0

print("Long Press Test - Press button short or long")

while True:
    time.sleep_ms(20)
    now = time.ticks_ms()
    
    # Detect button press (transition from released to pressed)
    if SW.value() == 0 and not button_down:
        # Button just pressed
        if time.ticks_diff(now, last_button_time) > DEBOUNCE_MS:
            button_down = True
            press_start_time = now
            print("Button pressed at", now)
    
    # Detect button release
    elif SW.value() == 1 and button_down:
        # Button just released
        button_down = False
        press_duration = time.ticks_diff(now, press_start_time)
        last_press_duration = press_duration
        last_button_time = now
        
        if press_duration >= LONG_PRESS_MS:
            long_press_count += 1
            print("LONG PRESS detected! Duration:", press_duration, "ms")
        else:
            short_press_count += 1
            print("Short press. Duration:", press_duration, "ms")
    
    # Display
    disp.fill(0)
    disp.text("Long Press Test", 0, 0)
    disp.text("Short: {}".format(short_press_count), 0, 16)
    disp.text("Long: {}".format(long_press_count), 0, 28)
    
    if button_down:
        hold_time = time.ticks_diff(now, press_start_time)
        disp.text("Holding: {}ms".format(hold_time), 0, 40)
    else:
        disp.text("Last: {}ms".format(last_press_duration), 0, 40)
    
    disp.text("SW: {}".format(SW.value()), 0, 52)
    disp.show()
