"""
Reset RTC clock to real time using NTP.
Run this after testing catch-up logic to restore accurate time.
"""

import network
import ntptime
import time
import json
from ds323x import DS323x
from machine import Pin, I2C, RTC
import pins

# Initialize I2C and RTC
i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400_000)
rtc = DS323x(i2c, addr=0x68)

print("Current RTC time (before sync):")
current = rtc.datetime()
print(f"  {current[0]}-{current[1]:02d}-{current[2]:02d} {current[4]:02d}:{current[5]:02d}:{current[6]:02d}")

# Connect to WiFi
try:
    with open("wifi_config.json", "r") as f:
        config = json.load(f)
    ssid = config["ssid"]
    password = config["password"]
except:
    print("Error: wifi_config.json not found")
    print("Please configure WiFi first or manually set the time")
    import sys
    sys.exit(1)

print(f"\nConnecting to {ssid}...")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for connection
timeout = 10
while not wlan.isconnected() and timeout > 0:
    time.sleep(1)
    timeout -= 1

if not wlan.isconnected():
    print("WiFi connection failed!")
    print("Please check your wifi_config.json or manually set the time")
    import sys
    sys.exit(1)

print(f"Connected! IP: {wlan.ifconfig()[0]}")

# Sync with NTP
print("\nSyncing with NTP...")
time.sleep(2)  # Give network stack a moment

for attempt in range(5):
    try:
        ntptime.host = "pool.ntp.org"
        ntptime.settime()
        
        # Get the synced time
        t = RTC().datetime()
        
        # Update both Pico RTC and DS323x
        rtc.datetime(t)
        
        print(f"\n✓ Time synced successfully!")
        print(f"  New time: {t[0]}-{t[1]:02d}-{t[2]:02d} {t[4]:02d}:{t[5]:02d}:{t[6]:02d}")
        break
    except Exception as e:
        if attempt < 4:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)
        else:
            print(f"\n✗ NTP sync failed after 5 attempts: {e}")
            print("  Please manually set the time")

wlan.disconnect()
wlan.active(False)
print("\nWiFi disconnected. You can now reboot the Pico.")
