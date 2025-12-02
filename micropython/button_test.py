# Pico 2 | Button Test for Encoder Board
# Simple test - displays encoder rotation and button press
# Encoder (COM/CON -> GND): A=GP6, B=GP7, SW=GP8 (pull-ups)
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

# ---------------- Encoder pins ----------------
ENC_A = Pin(6, Pin.IN, Pin.PULL_UP)
ENC_B = Pin(7, Pin.IN, Pin.PULL_UP)
ENC_SW = Pin(8, Pin.IN, Pin.PULL_UP)

# ---------------- Encoder state tracking ----------------
state = (ENC_A.value()<<1) | ENC_B.value()
encoder_count = 0
TRANS = (0,+1,-1,0,  -1,0,0,+1,  +1,0,0,-1,  0,-1,+1,0)

def enc_isr(_):
    global state, encoder_count
    s = (ENC_A.value()<<1) | ENC_B.value()
    d = TRANS[(state<<2)|s]
    encoder_count += d
    state = s

ENC_A.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=enc_isr)
ENC_B.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=enc_isr)

# ---------------- Main loop ----------------
print("Button Test - Rotate encoder and press button")

last_count = 0
button_pressed = False
button_display_time = 0

while True:
    time.sleep_ms(20)
    
    now = time.ticks_ms()
    
    # Check for encoder rotation
    enc_left = False
    enc_right = False
    if encoder_count > last_count:
        enc_right = True
        last_count = encoder_count
    elif encoder_count < last_count:
        enc_left = True
        last_count = encoder_count
    
    # Check button
    if ENC_SW.value() == 0:  # pressed
        button_pressed = True
        button_display_time = now
    
    # Clear button display after 500ms
    if button_pressed and time.ticks_diff(now, button_display_time) > 500:
        button_pressed = False
    
    # Display
    disp.fill(0)
    disp.text("{} Button Test".format(DRIVER), 0, 0)
    
    # Show encoder count
    disp.text("Count: {}".format(encoder_count), 0, 16)
    
    # Show rotation direction
    if enc_left:
        disp.text("> Encoder-Left", 0, 28)
    if enc_right:
        disp.text("> Encoder-Right", 0, 28)
    
    # Show button press
    if button_pressed:
        disp.text("> Button Press", 0, 40)
    
    # Show raw pin values
    disp.text("A:{} B:{} SW:{}".format(
        ENC_A.value(),
        ENC_B.value(),
        ENC_SW.value()
    ), 0, 52)
    
    disp.show()
