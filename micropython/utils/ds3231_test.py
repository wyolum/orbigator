from machine import I2C, Pin
from ds3231 import DS3231

# Use same I2C bus as your OLED
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)  # Lower freq for reliability

# Scan to verify both devices
print("I2C devices:", [hex(addr) for addr in i2c.scan()])
# Should show: ['0x3c', '0x68'] or similar

# Initialize RTC
rtc = DS3231(i2c)

# Set time (year, month, day, weekday, hour, minute, second, subsecond)
# rtc.datetime((2025, 12, 1, 1, 14, 30, 0, 0))  # Dec 1, 2025, 14:30:00

# Read time
print(rtc.datetime())
