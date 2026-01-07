"""
Back and Confirm Button Test
Tests GP9 (Back) and GP10 (Confirm) buttons with OLED feedback
"""

from machine import Pin, I2C
import time
import framebuf

print("=" * 50)
print("Button Test - Back & Confirm")
print("=" * 50)

# Initialize I2C and OLED
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)

# SH1106 OLED driver
class SH1106_I2C:
    def __init__(self, w, h, i2c, addr=0x3C):
        self.width, self.height, self.i2c, self.addr = w, h, i2c, addr
        self.buffer = bytearray(w * h // 8)
        self.fb = framebuf.FrameBuffer(self.buffer, w, h, framebuf.MONO_VLSB)
        def cmd(*cs):
            for c in cs: self.i2c.writeto(self.addr, b'\x00' + bytes([c]))
        cmd(0xAE, 0x20, 0x00, 0x40, 0xA1, 0xC8, 0x81, 0x7F, 0xA6, 0xA8, 0x3F,
            0xAD, 0x8B, 0xD3, 0x00, 0xD5, 0x80, 0xD9, 0x22, 0xDA, 0x12, 0xDB, 0x35, 0xAF)
        self.fill(0)
        self.show()
    def fill(self, c): self.fb.fill(c)
    def text(self, s, x, y, c=1): self.fb.text(s, x, y, c)
    def show(self):
        for p in range(self.height // 8):
            self.i2c.writeto(self.addr, b'\x00' + bytes([0xB0 + p, 0x02, 0x10]))
            s = self.width * p; e = s + self.width
            self.i2c.writeto(self.addr, b'\x40' + self.buffer[s:e])

display = SH1106_I2C(128, 64, i2c, addr=0x3C)
print("✓ OLED initialized")

# Initialize buttons with pull-ups
back_btn = Pin(9, Pin.IN, Pin.PULL_UP)
confirm_btn = Pin(10, Pin.IN, Pin.PULL_UP)
encoder_btn = Pin(8, Pin.IN, Pin.PULL_UP)

print("✓ Buttons initialized:")
print(f"  Back (GP9): {back_btn.value()}")
print(f"  Confirm (GP10): {confirm_btn.value()}")
print(f"  Encoder (GP8): {encoder_btn.value()}")
print("\nAll should read 1 (pulled high)")
print("\nPress buttons to test...")
print("Press Ctrl+C to exit")

# Button state tracking
back_count = 0
confirm_count = 0
encoder_count = 0

def update_display():
    """Update OLED with button states"""
    display.fill(0)
    display.text("Button Test", 16, 0)
    display.text("-" * 16, 0, 10)
    
    # Show button states
    back_state = "PRESSED" if back_btn.value() == 0 else "Released"
    confirm_state = "PRESSED" if confirm_btn.value() == 0 else "Released"
    encoder_state = "PRESSED" if encoder_btn.value() == 0 else "Released"
    
    display.text(f"Back: {back_state}", 0, 20)
    display.text(f"Conf: {confirm_state}", 0, 32)
    display.text(f"Enc:  {encoder_state}", 0, 44)
    
    # Show counts
    display.text(f"B:{back_count} C:{confirm_count} E:{encoder_count}", 0, 56)
    
    display.show()

# Initial display
update_display()

# Button state tracking for edge detection
last_back = back_btn.value()
last_confirm = confirm_btn.value()
last_encoder = encoder_btn.value()

try:
    while True:
        # Check back button
        current_back = back_btn.value()
        if current_back == 0 and last_back == 1:  # Pressed (falling edge)
            back_count += 1
            print(f"← BACK pressed (count: {back_count})")
            update_display()
            time.sleep_ms(200)  # Debounce
        last_back = current_back
        
        # Check confirm button
        current_confirm = confirm_btn.value()
        if current_confirm == 0 and last_confirm == 1:  # Pressed (falling edge)
            confirm_count += 1
            print(f"✓ CONFIRM pressed (count: {confirm_count})")
            update_display()
            time.sleep_ms(200)  # Debounce
        last_confirm = current_confirm
        
        # Check encoder button
        current_encoder = encoder_btn.value()
        if current_encoder == 0 and last_encoder == 1:  # Pressed (falling edge)
            encoder_count += 1
            print(f"⊙ ENCODER pressed (count: {encoder_count})")
            update_display()
            time.sleep_ms(200)  # Debounce
        last_encoder = current_encoder
        
        # Update display if any button state changed
        if (current_back != last_back or 
            current_confirm != last_confirm or 
            current_encoder != last_encoder):
            update_display()
        
        time.sleep_ms(50)

except KeyboardInterrupt:
    print("\n" + "=" * 50)
    print("Test Complete!")
    print(f"Back button presses: {back_count}")
    print(f"Confirm button presses: {confirm_count}")
    print(f"Encoder button presses: {encoder_count}")
    print("=" * 50)
    
    # Final display
    display.fill(0)
    display.text("Test Complete", 8, 16)
    display.text(f"Back: {back_count}", 8, 32)
    display.text(f"Confirm: {confirm_count}", 8, 40)
    display.text(f"Encoder: {encoder_count}", 8, 48)
    display.show()
