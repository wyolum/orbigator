
# ==========================================
# TrackLL Mode (Front Face Tracking)
# ==========================================
class TrackLLMode(SGP4Mode):
    """
    Tracking Mode that forces the solution to the "Front Face" of the device.
    Uses SGP4 to get Lat/Lon, then calculates Virtual Inclination.
    """
    def __init__(self):
        super().__init__()
        # Ensure we use the current selected satellite from SGP4Mode
        self.mode_name = "Track LL"

    def enter(self):
        # We reuse SGP4Mode's enter to setup the propagator
        super().enter()
        self.track_mode = "VIRTUAL" # Just a label
        if g.disp:
            g.disp.fill(0)
            g.disp.text("Front Face", 0, 0)
            g.disp.text("Tracking Init...", 0, 12)
            g.disp.show()
            
    def render(self, disp):
        # Override render to show we are in TrackLL
        disp.fill(0)
        disp.text("FRONT FACE", 0, 0)
        
        if self.tracking and self.propagator:
             # Show Lat/Lon
            la_str = f"Lat: {self.lat_deg:+.2f}"
            disp.text(la_str, 0, 16)
            
            lo_str = f"Lon: {self.lon_deg:+.2f}"
            disp.text(lo_str, 0, 28)
            
            disp.text(f"Alt: {self.alt_km:.0f}km", 0, 40)
            if self.tle_age != "OK":
                 disp.text(f"TLE: {self.tle_age}", 0, 52)
        else:
             disp.text("Waiting...", 0, 20)
             
        disp.show()

    def update(self, now_ms):
        """Update satellite position and motors."""
        if not self.propagator or not self.tracking:
            return
        
        # 1. Update target orientation from propagator
        ts = utils.get_timestamp()
        
        # Throttle updates to ~1Hz or when second changes to save CPU/Bus
        if ts == self.last_unix:
             return
        
        self.last_unix = ts
        
        try:
            # SGP4Propagator.get_aov_eqx returns (aov, eqx, lat, lon)
            aov, eqx, lat, lon = self.propagator.get_aov_eqx(ts)
            self.alt_km = self.propagator.get_altitude()
            
            self.lat_deg = lat
            self.lon_deg = lon
            
            # 3. Solve Virtual Inclination (Force Front Face)
            virt_aov, virt_eqx = utils.calculate_virtual_inclination(
                lat, lon, 
                g.PHYSICAL_INCLINATION_DEG, 
                current_aov=g.aov_position_deg, 
                force_ascending=True
            )
            
            if virt_aov is not None:
                # 4. Command Motors
                self.last_aov_angle = virt_aov
                self.last_eqx_angle = virt_eqx
                
                # Apply offsets/etc if needed, but set_nearest_degrees handles wrapping.
                if g.aov_motor:
                    g.aov_motor.set_nearest_degrees(virt_aov)
                    g.aov_motor.update_present_position()
                    
                if g.eqx_motor:
                    g.eqx_motor.set_nearest_degrees(virt_eqx)
                    g.eqx_motor.update_present_position()
        except AttributeError:
             print("TrackLL: Propagator missing method")
        except Exception as e:
            print(f"TrackLL Error: {e}")
