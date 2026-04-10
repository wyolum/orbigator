from machine import Pin, I2C
import pins
import time
import sys

print("--- Map Display Test ---")

# 1. Init I2C
i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400000)
devices = i2c.scan()
if not devices:
    print("No I2C devices found!")
    sys.exit()

# 2. Init Display Directly (Bypassing OledDisplay wrapper)
try:
    from sh1106 import SH1106_I2C
    disp = SH1106_I2C(128, 64, i2c, addr=0x3C)
    print("SH1106 initialized.")
except ImportError:
    try:
        from ssd1306 import SSD1306_I2C
        disp = SSD1306_I2C(128, 64, i2c, addr=0x3C)
        print("SSD1306 initialized.")
    except ImportError:
        print("No display driver found!")
        sys.exit()

print("Clearing display...")
disp.fill(0)
disp.text("Map Test Init..", 0, 0)
disp.show()
time.sleep_ms(500)

# 3. Test Map Generation / Load
import world_map
print("Attempting to get world mask...")
try:
    mask = world_map.get_world_mask()
    print(f"Mask obtained! Type: {type(mask)}")
    
    # Check if mask is completely blank
    # For a framebuf, the buffer is stored in .buffer if it inherits from one of the drivers, 
    # but world_mask returns a pure framebuf.FrameBuffer object.
    # Wait, pure framebuf doesn't have .buffer property natively, we can just blind copy it.
except Exception as e:
    print(f"Failed to get mask: {e}")
    sys.print_exception(e)
    sys.exit()

# 4. Draw Map
print("Drawing equirectangular map...")
disp.fill(0)
try:
    # We pass disp directly because world_map.draw_equirectangular expects 'disp.fb.blit'
    # BUT wait! SH1106_I2C has self.fb! SSD1306_I2C does NOT have self.fb! (It is the fb).
    # If the Orbigator code assumes disp.fb.blit, let's see which it uses.
    if hasattr(disp, 'fb'):
        print("Using disp.fb.blit...")
        disp.fb.blit(mask, 0, 0)
    else:
        print("Using disp.blit directly...")
        disp.blit(mask, 0, 0)
    
    # For the circle/lines
    # Just draw the map and a dot.
    disp.text("MAP OK?", 0, 56)
    disp.show()
    print("Map rendered to display!")
except Exception as e:
    print(f"Failed to draw map: {e}")
    sys.print_exception(e)
