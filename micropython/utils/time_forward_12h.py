"""
Set RTC clock 12 hours into the future for testing catch-up logic.
"""

import time
from ds323x import DS323x
from machine import Pin, I2C
import pins

# Initialize I2C and RTC
i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400_000)
rtc = DS323x(i2c, addr=0x68)

# Get current time
current = rtc.datetime()
print(f"Current RTC time: {current[0]}-{current[1]:02d}-{current[2]:02d} {current[4]:02d}:{current[5]:02d}:{current[6]:02d}")

# Calculate time 12 hours in the future
current_unix = time.mktime((current[0], current[1], current[2], current[4], current[5], current[6], 0, 0))
future_unix = current_unix + (12 * 3600)  # 12 hours in seconds
future_struct = time.localtime(future_unix)

# Set new time
# DS323x expects: (year, month, day, weekday, hour, minute, second, subsecond)
future_time = (future_struct[0], future_struct[1], future_struct[2], 0, 
               future_struct[3], future_struct[4], future_struct[5], 0)

rtc.datetime(future_time)

# Verify
new_time = rtc.datetime()
print(f"New RTC time:     {new_time[0]}-{new_time[1]:02d}-{new_time[2]:02d} {new_time[4]:02d}:{new_time[5]:02d}:{new_time[6]:02d}")
print(f"\n✓ Clock set 12 hours forward!")
print(f"   Reboot the Pico to test catch-up logic.")
