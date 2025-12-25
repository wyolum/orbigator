"""
Simple button integration test for Orbigator
Tests that back and confirm buttons work with the existing code
"""

from machine import Pin
import time

# Initialize buttons
BACK_BTN = Pin(9, Pin.IN, Pin.PULL_UP)
CONFIRM_BTN = Pin(10, Pin.IN, Pin.PULL_UP)

# State tracking
back_btn_last = 1
confirm_btn_last = 1
last_back_time = 0
last_confirm_time = 0
DEBOUNCE_MS = 200

print("=" * 50)
print("Orbigator Button Integration Test")
print("=" * 50)
print("Press Back or Confirm buttons")
print("Press Ctrl+C to exit")
print()

try:
    while True:
        now = time.ticks_ms()
        
        # Check back button
        current_back = BACK_BTN.value()
        if current_back == 0 and back_btn_last == 1:
            if time.ticks_diff(now, last_back_time) > DEBOUNCE_MS:
                last_back_time = now
                print("← BACK button pressed")
        back_btn_last = current_back
        
        # Check confirm button
        current_confirm = CONFIRM_BTN.value()
        if current_confirm == 0 and confirm_btn_last == 1:
            if time.ticks_diff(now, last_confirm_time) > DEBOUNCE_MS:
                last_confirm_time = now
                print("✓ CONFIRM button pressed")
        confirm_btn_last = current_confirm
        
        time.sleep_ms(20)

except KeyboardInterrupt:
    print("\nTest complete!")
