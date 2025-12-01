# Test script for ChronoDot (DS3231) RTC
from machine import I2C, Pin
from ds3231 import DS3231
import time

# Initialize I2C (same bus as OLED)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)

# Scan for I2C devices
print("Scanning I2C bus...")
devices = i2c.scan()
print("Found devices:", [hex(addr) for addr in devices])

# Initialize RTC
print("\nInitializing DS3231 RTC...")
rtc = DS3231(i2c)

# Uncomment to set the time (adjust to current time)
# Format: (year, month, day, weekday, hour, minute, second, subsecond)
# weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
# rtc.datetime((2025, 12, 1, 0, 14, 30, 0, 0))  # Dec 1, 2025, Monday, 14:30:00
# print("Time set!")

# Read and display current time
print("\nCurrent time from RTC:")
dt = rtc.datetime()
print("  Datetime tuple:", dt)
print("  Formatted:", rtc.get_time_str())

# Read temperature from DS3231
temp = rtc.temperature()
print("  Temperature: {:.2f}°C".format(temp))

# Loop and show time updates
print("\nLive clock (Ctrl+C to stop):")
try:
    while True:
        print(rtc.get_time_str(), "  Temp: {:.2f}°C".format(rtc.temperature()))
        time.sleep(1)
except KeyboardInterrupt:
    print("\nTest complete!")
