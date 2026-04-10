import machine, time
from machine import Pin, I2C
from ds323x import DS323x
import pins

# --- Hardware Setup ---
i2c = I2C(0, scl=Pin(pins.I2C_SCL_PIN), sda=Pin(pins.I2C_SDA_PIN), freq=400000)
rtc = DS323x(i2c, has_sram=True)

print("----------------------------------------")
print("DS3232 SRAM CLEAR UTILITY")
print("----------------------------------------")

# Verify device presence
try:
    with machine.RTC() as pico_rtc:
        pass # Just checking I2C/UART/etc
except:
    pass

print("Clearing battery-backed SRAM...")
if rtc.clear_sram():
    print("✓ SRAM wiped successfully.")
    print("The system will now boot from scratch on the next run.")
else:
    print("✗ SRAM clear failed. Is the DS3232 battery connected?")
print("----------------------------------------")
