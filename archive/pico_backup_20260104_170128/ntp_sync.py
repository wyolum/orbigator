import ntptime
import machine
import time
import network
import json

def sync_ntp(ssid=None, password=None):
    """
    Connect to WiFi and sync system clock via NTP.
    Returns True on success, False otherwise.
    """
    wlan = network.WLAN(network.STA_IF)
    
    # Use config if not provided
    if not ssid or not password:
        try:
            with open("wifi_config.json", "r") as f:
                config = json.load(f)
                ssid = ssid or config.get("ssid")
                password = password or config.get("password")
        except:
            print("Error: No wifi_config.json found and no credentials provided.")
            return False

    if not wlan.isconnected():
        print(f"Connecting to {ssid}...")
        wlan.active(True)
        wlan.connect(ssid, password)
        
        # Wait up to 10s
        for _ in range(20):
            if wlan.isconnected(): break
            time.sleep(0.5)
            
    if not wlan.isconnected():
        print("WiFi connection failed.")
        return False
        
    print(f"Connected! IP: {wlan.ifconfig()[0]}")
    
    try:
        print("Syncing time via NTP...")
        ntptime.settime()
        
        # After setting time, time.time() is UTC
        now = time.localtime()
        print(f"Success! Current UTC: {now[0]}-{now[1]:02d}-{now[2]:02d} {now[3]:02d}:{now[4]:02d}:{now[5]:02d}")
        return True
    except Exception as e:
        print(f"NTP sync failed: {e}")
        return False

if __name__ == "__main__":
    sync_ntp()
