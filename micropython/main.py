# main.py - Auto-run on Pico boot
# Launches the Orbigator satellite tracking system
import time
import machine
from machine import Pin, I2C

print("\n\n")
print("====================================")
print("   ORBIGATOR BOOT SEQUENCE")
print("====================================")
print("Waiting 5 seconds for safety interrupt...")
print("Press Ctrl+C NOW to stop auto-run.")

# ------------------------------------------------------------------
# Splash Screen Logic
# ------------------------------------------------------------------
try:
    # Init I2C0 on GP4/GP5
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    
    # Try to init generic SSD1306/SH1106 via shared driver
    start_oled = True
    try:
        import sh1106
        oled = sh1106.SH1106_I2C(128, 64, i2c)
    except Exception as e:
        print(f"Display init failed: {e}")
        start_oled = False

    for i in range(5, 0, -1):
        print(f"{i}...", end=" ")
        
        if start_oled:
            oled.fill(0)
            
            # Header
            oled.text("ORBIGATOR", 28, 5, 1)
            oled.rect(26, 15, 76, 2, 1) # Underline
            
            # Subtitle
            oled.text("Satellite Tracker", 0, 25, 1)
            
            # Countdown Bar
            bar_width = int((i / 5.0) * 128)
            oled.fill_rect(0, 45, bar_width, 8, 1)
            
            # Text below bar
            msg = f"Booting in {i}s"
            x_pos = (128 - (len(msg)*8)) // 2
            oled.text(msg, x_pos, 56, 1)
            
            oled.show()
            
        time.sleep(1)
        
    if start_oled:
        oled.fill(0)
        oled.text("Launching app...", 5, 30, 1)
        oled.show()
    
    # Clean up
    if start_oled:
        pass 
        
except Exception as e:
    print(f"\nSplash screen error: {e}")
    # Fallback delay
    for i in range(5, 0, -1):
        print(f"{i}...", end=" ")
        time.sleep(1)

print("\nLaunching application!\n")

# Import main application
import orbigator
