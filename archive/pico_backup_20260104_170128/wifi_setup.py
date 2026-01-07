"""
WiFi Configuration via Access Point and Web Interface
Creates a temporary AP, serves a config page, then connects to the configured network
"""

import network
import socket
import time
import json

CONFIG_FILE = "wifi_config.json"
AP_SSID = "Orbigator-Setup"
AP_PASSWORD = "orbigator123"

HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>Orbigator WiFi Setup</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 40px; background: #f0f0f0; }
        .container { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: auto; }
        h1 { color: #333; }
        input, select { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
        button { background: #4CAF50; color: white; padding: 15px; border: none; width: 100%; font-size: 16px; cursor: pointer; }
        button:hover { background: #45a049; }
        .info { background: #e7f3fe; padding: 10px; border-left: 4px solid #2196F3; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Orbigator WiFi Setup</h1>
        <div class="info">
            <strong>Available Networks:</strong><br>
            %NETWORKS%
        </div>
        <form action="/configure" method="POST">
            <label>WiFi Network:</label>
            <select name="ssid" id="ssid">
                %OPTIONS%
            </select>
            <label>Password:</label>
            <input type="password" name="password" placeholder="Enter WiFi password">
            <button type="submit">Connect</button>
        </form>
    </div>
</body>
</html>
"""

SUCCESS_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>Orbigator - Connected!</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 40px; background: #f0f0f0; text-align: center; }
        .container { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: auto; }
        h1 { color: #4CAF50; }
        .success { background: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Connected!</h1>
        <div class="success">
            <p><strong>SSID:</strong> %SSID%</p>
            <p><strong>IP Address:</strong> %IP%</p>
        </div>
        <p>WiFi configuration saved. Orbigator will now use this network.</p>
        <p>You can close this page.</p>
    </div>
</body>
</html>
"""

def scan_networks():
    """Scan for WiFi networks and return list of SSIDs."""
    print("Scanning for networks...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    networks = wlan.scan()
    
    # Deduplicate by SSID and sort by signal strength
    seen = {}
    for net in networks:
        ssid = net[0].decode('utf-8')
        rssi = net[3]
        if ssid not in seen or rssi > seen[ssid]:
            seen[ssid] = rssi
    
    return sorted(seen.keys(), key=lambda s: seen[s], reverse=True)

def create_ap():
    """Create WiFi Access Point."""
    print(f"Creating AP: {AP_SSID}")
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASSWORD)
    
    while not ap.active():
        time.sleep(0.1)
    
    print(f"AP active: {AP_SSID}")
    print(f"Password: {AP_PASSWORD}")
    print(f"IP: {ap.ifconfig()[0]}")
    return ap

def connect_wifi(ssid, password):
    """Connect to WiFi network."""
    print(f"Connecting to {ssid}...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    timeout = 10
    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            return None
        time.sleep(0.5)
    
    return wlan.ifconfig()[0]

def save_config(ssid, password):
    """Save WiFi config to file."""
    config = {"ssid": ssid, "password": password}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def web_server(ap):
    """Run web server for configuration."""
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    
    print(f"Web server running on http://{ap.ifconfig()[0]}")
    print("Connect to the AP and navigate to http://192.168.4.1")
    
    networks = scan_networks()
    
    while True:
        cl, addr = s.accept()
        print(f"Client connected from {addr}")
        request = cl.recv(1024).decode('utf-8')
        
        if "POST /configure" in request:
            # Parse form data
            try:
                body = request.split('\r\n\r\n')[1]
                params = {}
                for param in body.split('&'):
                    key, value = param.split('=')
                    params[key] = value.replace('+', ' ').replace('%40', '@')
                
                ssid = params['ssid']
                password = params['password']
                
                print(f"Configuring: {ssid}")
                
                # Try to connect
                ip = connect_wifi(ssid, password)
                
                if ip:
                    save_config(ssid, password)
                    response = SUCCESS_PAGE.replace('%SSID%', ssid).replace('%IP%', ip)
                    cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                    cl.send(response)
                    cl.close()
                    print("✓ WiFi configured successfully!")
                    time.sleep(2)
                    return True
                else:
                    cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                    cl.send('<h1>Connection Failed</h1><p>Check password and try again.</p>')
            except Exception as e:
                print(f"Error: {e}")
                cl.send('HTTP/1.1 500 Error\r\n\r\n')
        else:
            # Serve config page
            network_list = '<br>'.join([f"• {ssid}" for ssid in networks[:10]])
            options = '\n'.join([f'<option value="{ssid}">{ssid}</option>' for ssid in networks])
            
            page = HTML_PAGE.replace('%NETWORKS%', network_list).replace('%OPTIONS%', options)
            
            cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            cl.send(page)
        
        cl.close()

def setup_wifi_ap():
    """Main setup function using AP mode."""
    print("="*60)
    print("Orbigator WiFi Setup (AP Mode)")
    print("="*60)
    
    ap = create_ap()
    
    print("\n" + "="*60)
    print("SETUP INSTRUCTIONS:")
    print("1. Connect your phone/laptop to WiFi:")
    print(f"   Network: {AP_SSID}")
    print(f"   Password: {AP_PASSWORD}")
    print("2. Open browser and go to: http://192.168.4.1")
    print("3. Select your WiFi network and enter password")
    print("="*60 + "\n")
    
    success = web_server(ap)
    
    if success:
        ap.active(False)
        print("AP shut down. WiFi configured!")
        return True
    return False

if __name__ == "__main__":
    setup_wifi_ap()
