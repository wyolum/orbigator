"""
Orbigator Web Server
Provides HTTP server and REST API for web-based control
"""

import socket
import json
import time
import gc
import os

# Import Orbigator globals and utilities
import orb_globals as g
import orb_utils as utils
from satellite_catalog import get_satellite_count, get_satellite_name, get_satellite_norad

class WebServer:
    def __init__(self, port=80):
        self.port = port
        self.routes = {}
        self.current_mode_name = "menu"
        self.seen_ips = set()
        import network
        self.wlan = network.WLAN(network.STA_IF)
        self.ap = network.WLAN(network.AP_IF)
        self._setup_routes()
    
    def _setup_routes(self):
        """Register all API routes"""
        # API endpoints
        self.routes['/api/status'] = self.api_status
        self.routes['/api/satellites'] = self.api_satellites
        self.routes['/api/mode'] = self.api_mode
        self.routes['/api/satellite'] = self.api_satellite
        self.routes['/api/tracking'] = self.api_tracking
        self.routes['/api/sync'] = self.api_sync
        self.routes['/api/orbit/params'] = self.api_orbit_params
        self.routes['/api/tle/refresh'] = self.api_tle_refresh
        self.routes['/api/motors'] = self.api_motors
        self.routes['/api/motors/nudge'] = self.api_motors_nudge
        self.routes['/api/tle/manual'] = self.api_tle_manual
        self.routes['/api/wifi/scan'] = self.api_wifi_scan
        self.routes['/api/wifi/config'] = self.api_wifi_config
    
    def api_status(self, method, body):
        """GET /api/status - Current system status"""
        if method != 'GET':
            return {'error': 'Method not allowed'}, 405
        
        # Get actual WiFi status
        wifi_connected = self.wlan.isconnected()
        wifi_ssid = ""
        if wifi_connected:
            wifi_ssid = self.wlan.config('essid')
        elif self.ap.active():
            wifi_ssid = "AP MODE"
            
        status = {
            'mode': g.current_mode_id.lower(),
            'motors': {
                'aov': round(g.aov_position_deg % 360, 2),
                'eqx': round(g.eqx_position_deg % 360, 2)
            },
            'wifi': {
                'connected': wifi_connected,
                'ssid': wifi_ssid
            },
            'rtc': {
                'synced': time.localtime()[0] >= 2024,
                'time': self._get_rtc_time()
            }
        }
        
        # Add mode-specific status
        if g.current_mode_id == 'SGP4' and hasattr(g, 'current_mode'):
            m = g.current_mode
            status['tracking'] = getattr(m, 'tracking', False)
            status['satellite'] = getattr(m, 'satellite_name', "none")
            status['position'] = {
                'lat': round(getattr(m, 'lat_deg', 0.0), 4),
                'lon': round(getattr(m, 'lon_deg', 0.0), 4),
                'alt': round(getattr(m, 'alt_km', 0.0), 1),
                'inc': round(getattr(m, 'inclination', 0.0), 1)
            }
            status['tle_age'] = getattr(m, 'tle_age', "N/A")
        elif g.current_mode_id == 'ORBIT':
            status['orbital_params'] = {
                'altitude_km': g.orbital_altitude_km,
                'period_min': g.orbital_period_min,
                'eccentricity': g.orbital_eccentricity,
                'inclination_deg': g.orbital_inclination_deg
            }
        
        return status, 200
    
    def api_satellites(self, method, body):
        """GET /api/satellites - List available satellites"""
        if method != 'GET':
            return {'error': 'Method not allowed'}, 405
        
        satellites = []
        tle_cache = utils.load_tle_cache()
        
        for i in range(get_satellite_count()):
            sat_name = get_satellite_name(i)
            norad_id = get_satellite_norad(i)
            tle_data = tle_cache.get(sat_name, {})
            last_fetch = tle_data.get('last_fetch', 0)
            
            satellites.append({
                'name': sat_name,
                'norad_id': norad_id,
                'tle_age': utils.get_tle_age_str(last_fetch) if last_fetch > 0 else 'none',
                'has_tle': sat_name in tle_cache
            })
        
        return {'satellites': satellites}, 200
    
    def api_mode(self, method, body):
        """POST /api/mode - Switch mode"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
        
        mode = body.get('mode', '').lower()
        if mode not in ['menu', 'orbit', 'sgp4']:
            return {'error': 'Invalid mode'}, 400
        
        # Request mode change in main thread
        from modes import MenuMode, OrbitMode, SGP4Mode
        if mode == 'menu':
            g.next_mode = MenuMode()
        elif mode == 'orbit':
            g.next_mode = OrbitMode()
        elif mode == 'sgp4':
            g.next_mode = SGP4Mode()
            
        self.current_mode_name = mode
        return {'success': True, 'mode': mode}, 200
    
    def api_satellite(self, method, body):
        """POST /api/satellite - Select satellite"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
        
        satellite = body.get('satellite', '')
        if hasattr(g, 'current_mode') and g.current_mode and g.current_mode_id == "SGP4":
            if g.current_mode.select_satellite_by_name(satellite):
                return {'success': True, 'satellite': satellite}, 200
            else:
                return {'error': f'Satellite {satellite} not found'}, 404
        else:
             return {'error': 'Not in Sentry/SGP4 mode'}, 409
    
    def api_sync(self, method, body):
        """POST /api/sync - Manually trigger time sync and TLE refresh"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
        
        try:
            import ntptime, machine
            ntptime.settime()
            t = machine.RTC().datetime()
            utils.set_datetime(t[0], t[1], t[2], t[4], t[5], t[6], g.rtc)
            # Re-fetch TLEs if requested
            if body.get('tle', False):
                import tle_fetch
                tle_fetch.fetch_all()
            return {'success': True, 'time': utils.get_timestamp()}, 200
        except Exception as e:
            return {'error': str(e)}, 500

    def api_tracking(self, method, body):
        """POST /api/tracking - Start/stop tracking"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
        
        tracking = body.get('tracking', False)
        if hasattr(g, 'current_mode') and g.current_mode and g.current_mode_id == "SGP4":
            g.current_mode.tracking = tracking
            return {'success': True, 'tracking': tracking}, 200
        else:
             return {'error': 'Not in Sentry/SGP4 mode'}, 409
    
    def api_orbit_params(self, method, body):
        """POST /api/orbit/params - Update orbital parameters"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
        
        # Update global parameters
        if 'altitude_km' in body:
            g.orbital_altitude_km = float(body['altitude_km'])
        if 'period_min' in body:
            g.orbital_period_min = float(body['period_min'])
        if 'eccentricity' in body:
            g.orbital_eccentricity = float(body['eccentricity'])
        if 'inclination_deg' in body:
            g.orbital_inclination_deg = float(body['inclination_deg'])
        
        # Recalculate rates
        aov_rate, eqx_rate_sec, eqx_rate_day, period_min = utils.compute_motor_rates(g.orbital_altitude_km)
        g.aov_rate_deg_sec = aov_rate
        g.eqx_rate_deg_sec = eqx_rate_sec
        
        return {
            'success': True,
            'params': {
                'altitude_km': g.orbital_altitude_km,
                'period_min': g.orbital_period_min,
                'aov_rate': round(aov_rate, 6),
                'eqx_rate': round(eqx_rate_sec, 6)
            }
        }, 200
    
    def api_tle_refresh(self, method, body):
        """POST /api/tle/refresh - Force TLE refresh"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
        
        satellite = body.get('satellite', '')
        # TODO: Trigger TLE fetch
        
        return {'success': True, 'satellite': satellite}, 200
    
    def api_tle_manual(self, method, body):
        """POST /api/tle/manual - Set manual TLE"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
            
        name = body.get('name', 'Custom Sat')
        line1 = body.get('line1', '').strip()
        line2 = body.get('line2', '').strip()
        
        if not line1 or not line2:
            return {'error': 'Missing TLE lines'}, 400
            
        # Check logic
        if hasattr(g, 'current_mode') and g.current_mode and g.current_mode_id == "SGP4":
            success, msg = g.current_mode.set_manual_tle(name, line1, line2)
            if success:
                return {'success': True, 'message': msg}, 200
            else:
                return {'error': msg}, 400
        else:
             return {'error': 'System must be in Track Satellite mode'}, 409
    
    def api_motors(self, method, body):
        """GET /api/motors - Motor status"""
        if method != 'GET':
            return {'error': 'Method not allowed'}, 405
        
        return {
            'aov': {
                'position': round(g.aov_position_deg % 360, 2),
                'rate': round(g.aov_rate_deg_sec, 6),
                'p_gain': g.aov_motor.p_gain if g.aov_motor else None,
                'i_gain': g.aov_motor.i_gain if g.aov_motor else None,
                'd_gain': g.aov_motor.d_gain if g.aov_motor else None,
                'velocity_limit': g.aov_motor.current_velocity_limit if g.aov_motor else None,
                'health': 'ok'
            },
            'eqx': {
                'position': round(g.eqx_position_deg % 360, 2),
                'rate': round(g.eqx_rate_deg_sec, 6),
                'p_gain': g.eqx_motor.p_gain if g.eqx_motor else None,
                'i_gain': g.eqx_motor.i_gain if g.eqx_motor else None,
                'd_gain': g.eqx_motor.d_gain if g.eqx_motor else None,
                'velocity_limit': g.eqx_motor.current_velocity_limit if g.eqx_motor else None,
                'health': 'ok'
            }
        }, 200
    
    def api_motors_nudge(self, method, body):
        """POST /api/motors/nudge - Nudge motor position"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
        
        motor = body.get('motor', '').lower()
        delta = float(body.get('delta', 0))

        # Check current mode - Nudging disabled in SGP4 mode
        if hasattr(g, 'current_mode_id') and g.current_mode_id == "SGP4":
            return {'error': 'Nudging disabled in SGP4 mode'}, 400
        
        if motor == 'aov' and g.aov_motor:
            g.aov_position_deg += delta
            g.run_start_aov_deg += delta  # Shift reference to prevent snap-back
            g.aov_motor.set_nearest_degrees(g.aov_position_deg % 360)
        elif motor == 'eqx' and g.eqx_motor:
            g.eqx_position_deg += delta
            g.run_start_eqx_deg += delta  # Shift reference to prevent snap-back
            g.eqx_motor.set_nearest_degrees(g.eqx_position_deg % 360)
        else:
            return {'error': 'Invalid motor'}, 400
        
        return {'success': True, 'motor': motor, 'delta': delta}, 200
    
    def _get_rtc_time(self):
        """Get RTC time as ISO string"""
        if not g.rtc:
            return None
        try:
            if g.i2c_lock:
                with g.i2c_lock:
                    t = g.rtc.datetime()
            else:
                t = g.rtc.datetime()
            if t:
                return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[4]:02d}:{t[5]:02d}:{t[6]:02d}Z"
        except:
            pass
        return None
    
    def _parse_request(self, request):
        """Parse HTTP request"""
        lines = request.decode('utf-8').split('\r\n')
        if not lines:
            return None, None, None, None
        
        # Parse request line
        parts = lines[0].split(' ')
        if len(parts) < 2:
            return None, None, None, None
        
        method = parts[0]
        path = parts[1]
        
        # Parse headers
        headers = {}
        body_start = 0
        for i, line in enumerate(lines[1:], 1):
            if line == '':
                body_start = i + 1
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        # Parse body (JSON)
        body = {}
        if body_start < len(lines):
            body_text = '\r\n'.join(lines[body_start:])
            if body_text:
                try:
                # Parse body (JSON)
                    body = json.loads(body_text)
                except:
                    pass
        
        return method, path, headers, body
    
    def _send_response(self, client, status_code, data):
        """Send HTTP response"""
        status_text = {200: 'OK', 400: 'Bad Request', 404: 'Not Found', 405: 'Method Not Allowed', 500: 'Internal Server Error'}
        
        headers = f"HTTP/1.1 {status_code} {status_text.get(status_code, 'Unknown')}\r\n"
        headers += "Content-Type: application/json\r\n"
        headers += "Access-Control-Allow-Origin: *\r\n"
        headers += "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        headers += "Access-Control-Allow-Headers: Content-Type\r\n"
        headers += "Connection: close\r\n\r\n"
        
        client.send(headers.encode('utf-8'))
        if data:
            client.send(json.dumps(data).encode('utf-8'))
    
    def _serve_static(self, client, path):
        """Serve static files with streaming to save memory"""
        # Map root to index.html
        if path == '/':
            path = '/index.html'
        
        # Security: prevent directory traversal
        if '..' in path:
            self._send_response(client, 404, {'error': 'Not found'})
            return
        
        # Try to serve file from web/ directory
        filepath = 'web' + path
        
        # Check for gzipped version first
        is_gz = False
        try:
            if os.stat(filepath + '.gz'):
                filepath += '.gz'
                is_gz = True
        except:
            pass
            
        try:
            # Determine content type
            if path.endswith('.html'):
                content_type = 'text/html'
            elif path.endswith('.css'):
                content_type = 'text/css'
            elif path.endswith('.js'):
                content_type = 'application/javascript'
            elif path.endswith('.svg'):
                content_type = 'image/svg+xml'
            elif path.endswith('.json'):
                content_type = 'application/json'
            else:
                content_type = 'application/octet-stream'
            
            headers = f"HTTP/1.1 200 OK\r\n"
            headers += f"Content-Type: {content_type}\r\n"
            if is_gz:
                headers += "Content-Encoding: gzip\r\n"
            headers += "Access-Control-Allow-Origin: *\r\n"
            headers += "Connection: close\r\n\r\n"
            client.send(headers.encode('utf-8'))
            
            # Stream the file in chunks
            # Use smaller chunks and a small delay to prevent network stack overflow
            gc.collect()
            print(f"  -> Streaming {filepath} {'(GZ)' if is_gz else ''}...")
            CHUNK_SIZE = 512
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    try:
                        # use write() as it's more reliable for streaming in MP
                        client.write(chunk)
                        time.sleep_ms(2) # Give Pico oxygen
                    except Exception as e:
                        print(f"  !! Send error: {e}")
                        break
            gc.collect()
        except Exception as e:
            print(f"  !! Serve error: {e}")
            self._send_response(client, 404, {'error': 'Not found'})
    
    def handle_request(self, client, request):
        """Handle incoming HTTP request"""
        method, path, headers, body = self._parse_request(request)
        
        if not method or not path:
            self._send_response(client, 400, {'error': 'Bad request'})
            return
            
        print(f"[{method}] {path}")
        
        # Handle OPTIONS (CORS preflight)
        if method == 'OPTIONS':
            self._send_response(client, 200, None)
            return
        
        # Check if API route
        if path in self.routes:
            try:
                data, status_code = self.routes[path](method, body)
                self._send_response(client, status_code, data)
            except Exception as e:
                print(f"API error: {e}")
                self._send_response(client, 500, {'error': str(e)})
        else:
            # Serve static file
            self._serve_static(client, path)
    
    def start(self):
        """Start web server (blocking)"""
        import network
        
        # Get IP address
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print(f"\n{'='*50}")
            print(f"🌐 Web Server Running!")
            print(f"{'='*50}")
            print(f"URL: http://{ip}/")
            print(f"Port: {self.port}")
            print(f"{'='*50}\n")
        else:
            print(f"Web server running on port {self.port} (WiFi not connected)")
        
        addr = socket.getaddrinfo('0.0.0.0', self.port)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        
        while True:
            try:
                client, addr = s.accept()
                client_ip = addr[0]
                if client_ip not in self.seen_ips:
                    print(f"Client connected from {client_ip}")
                    self.seen_ips.add(client_ip)
                
                request = client.recv(2048)
                if request:
                    self.handle_request(client, request)
                
                client.close()
                gc.collect()  # Clean up memory
            except Exception as e:
                print(f"Server error: {e}")
                try:
                    client.close()
                except:
                    pass

    def api_wifi_scan(self, method, body):
        """GET /api/wifi/scan - Scan for available networks"""
        if method != 'GET':
            return {'error': 'Method not allowed'}, 405
        
        try:
            import wifi_setup
            networks = wifi_setup.scan_networks()
            return {'networks': networks}, 200
        except Exception as e:
            print(f"Scan error: {e}")
            return {'error': str(e)}, 500

    def api_wifi_config(self, method, body):
        """POST /api/wifi/config - Save WiFi credentials and restart"""
        if method != 'POST':
            return {'error': 'Method not allowed'}, 405
        
        try:
            data = json.loads(body)
            ssid = data.get('ssid')
            password = data.get('password')
            
            if not ssid:
                return {'error': 'SSID required'}, 400
            
            import wifi_setup
            wifi_setup.save_config(ssid, password)
            
            # Restart after a short delay to allow response to send
            import machine
            def restart(t):
                print("Restarting for WiFi config...")
                machine.reset()
                
            timer = machine.Timer(-1)
            timer.init(period=2000, mode=machine.Timer.ONE_SHOT, callback=restart)
            
            return {'message': 'Config saved. System will restart in 2 seconds.'}, 200
        except Exception as e:
            print(f"Config error: {e}")
            return {'error': str(e)}, 500

# Global server instance
_server = None

def start_server(port=80):
    """Start web server"""
    global _server
    _server = WebServer(port)
    _server.start()

if __name__ == '__main__':
    start_server()
