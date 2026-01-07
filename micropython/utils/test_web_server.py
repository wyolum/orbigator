"""
Test script to connect WiFi and start web server
"""
import wifi_setup
import json

# Load WiFi config
try:
    with open("wifi_config.json", "r") as f:
        config = json.load(f)
    ssid = config["ssid"]
    password = config["password"]
    
    print(f"Connecting to {ssid}...")
    ip = wifi_setup.connect_wifi(ssid, password)
    
    if ip:
        print(f"Connected! IP: {ip}")
        
        # Start web server
        import web_server
        web_server.start_server(port=80)
    else:
        print("WiFi connection failed")
except Exception as e:
    print(f"Error: {e}")
