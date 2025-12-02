# Pico 2 | Confirm and Back Button Test
# Tests the CONFIRM and BACK buttons from encoder board
# CONFIRM: GP26 (Active LOW, PULL_UP)
# BACK: GP27 (Active LOW, PULL_UP)
# OLED (SH1106/SSD1306 auto): I2C0 SDA=GP4, SCL=GP5

import machine, time
from machine import Pin, I2C
import framebuf

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

# ---------------- Button pins ----------------
BTN_CONFIRM = Pin(26, Pin.IN, Pin.PULL_UP)
BTN_BACK = Pin(27, Pin.IN, Pin.PULL_UP)

# ---------------- Main loop ----------------
print("Confirm/Back Button Test")
print("Press CONFIRM (GP26) or BACK (GP27)")

confirm_pressed = False
back_pressed = False
confirm_display_time = 0
back_display_time = 0
confirm_count = 0
back_count = 0

DEBOUNCE_MS = 200
last_confirm_time = 0
last_back_time = 0

while True:
    time.sleep_ms(20)
    
    now = time.ticks_ms()
    
    # Check CONFIRM button
    if BTN_CONFIRM.value() == 0:  # pressed
        if time.ticks_diff(now, last_confirm_time) > DEBOUNCE_MS:
            confirm_pressed = True
            confirm_display_time = now
            confirm_count += 1
            last_confirm_time = now
    
    # Check BACK button
    if BTN_BACK.value() == 0:  # pressed
        if time.ticks_diff(now, last_back_time) > DEBOUNCE_MS:
            back_pressed = True
            back_display_time = now
            back_count += 1
            last_back_time = now
    
    # Clear button displays after 500ms
    if confirm_pressed and time.ticks_diff(now, confirm_display_time) > 500:
        confirm_pressed = False
    if back_pressed and time.ticks_diff(now, back_display_time) > 500:
        back_pressed = False
    
    # Display
    disp.fill(0)
    disp.text("Confirm/Back Test", 0, 0)
    
    # Show raw pin values
    disp.text("Confirm(26): {}".format(BTN_CONFIRM.value()), 0, 16)
    disp.text("Back(27):    {}".format(BTN_BACK.value()), 0, 28)
    
    # Show button press indicators
    if confirm_pressed:
        disp.text("> CONFIRM", 0, 40)
    disp.text("  Count: {}".format(confirm_count), 0, 48)
    
    if back_pressed:
        disp.text("> BACK", 64, 40)
    disp.text("  Count: {}".format(back_count), 64, 48)
    
    disp.show()
