"""
Networking Utilities for Orbigator
Handles Wi-Fi bringup and status.
"""

import json
import time

def connect_wifi(ssid, password, display=None, timeout_s=20):
    """
    Connects to the specified Wi-Fi network.
    """
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if display:
            display.fill(0)
            display.text("WiFi Connect", 0, 0)
            display.text(ssid[:15], 0, 16)
            display.show()
            
        print(f"Connecting to WiFi '{ssid}'...")
        wlan.connect(ssid, password)
        
        start = time.time()
        while not wlan.isconnected() and (time.time() - start) < timeout_s:
            time.sleep(1)
            
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print(f"  ✓ Connected! IP: {ip}")
            if display:
                display.fill(0)
                display.text("WiFi OK", 0, 0)
                display.text(ip, 0, 16)
                display.show()
                time.sleep(1)
            return ip
        else:
            print("  ✗ Connection timed out.")
            return None
    except Exception as e:
        print(f"  ✗ WiFi error: {e}")
        return None

def is_connected():
    try:
        import network
        return network.WLAN(network.STA_IF).isconnected()
    except:
        return False

def get_ip():
    try:
        import network
        # Priority 1: Station IP (Client Mode)
        wlan = network.WLAN(network.STA_IF)
        if wlan.active() and wlan.isconnected():
            return wlan.ifconfig()[0]
            
        # Priority 2: Access Point IP
        ap = network.WLAN(network.AP_IF)
        if ap.active():
            return ap.ifconfig()[0]
    except:
        pass
    return None
