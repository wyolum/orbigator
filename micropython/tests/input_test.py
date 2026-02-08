"""
Interactive Input Test
======================
Shows button presses and encoder changes on OLED and serial.
Press Ctrl+C to exit.
"""

from machine import Pin, I2C
import time

# Initialize I2C and display
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

from oled_display import OledDisplay
from rotary_encoder import RotaryEncoder
from buttons import Buttons

display = OledDisplay(i2c)
encoder = RotaryEncoder(6, 7, 8)
buttons = Buttons(9, 10)

print("Interactive Input Test")
print("=" * 30)
print("Turn encoder, press buttons...")
print("Ctrl+C to exit")
print()

last_enc = encoder.value
last_back = False
last_confirm = False
last_enc_btn = False

try:
    while True:
        # Check encoder
        enc = encoder.value
        enc_btn = encoder.button_pressed
        back = buttons.back_pressed
        confirm = buttons.confirm_pressed
        
        # Detect changes
        changed = False
        
        if enc != last_enc:
            delta = enc - last_enc
            print(f"Encoder: {enc} ({'+' if delta > 0 else ''}{delta})")
            last_enc = enc
            changed = True
        
        if enc_btn != last_enc_btn:
            if enc_btn:
                print("Encoder Button: PRESSED")
            last_enc_btn = enc_btn
            changed = True
        
        if back != last_back:
            if back:
                print("Back Button: PRESSED")
            last_back = back
            changed = True
        
        if confirm != last_confirm:
            if confirm:
                print("Confirm Button: PRESSED")
            last_confirm = confirm
            changed = True
        
        # Update display
        display.clear()
        display.text("INPUT TEST", 20, 0)
        display.text("-" * 16, 0, 10)
        display.text(f"Encoder: {enc}", 0, 24)
        
        # Show button states
        btn_line = ""
        if enc_btn:
            btn_line += "[ENC]"
        if back:
            btn_line += "[BACK]"
        if confirm:
            btn_line += "[OK]"
        if not btn_line:
            btn_line = "(no buttons)"
        
        display.text(btn_line, 0, 40)
        display.show()
        
        time.sleep_ms(50)

except KeyboardInterrupt:
    display.clear()
    display.text("Test ended", 20, 28)
    display.show()
    print("\nTest ended.")
