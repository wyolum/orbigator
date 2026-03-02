import math
import framebuf
import world_map
import orb_globals as g

# Radar geometry — right half, full 64px height
_CX     = 96   # centre of right panel
_CY     = 32   # vertical centre
_RADIUS = 29   # 64/2 - 3 px margin


def to_xy(az_deg, el_deg):
    """Convert az/el to pixel coordinates on the radar circle."""
    az_r = math.radians(az_deg)
    el_r = math.radians(el_deg)
    r    = math.cos(el_r)
    x    = int(_CX + _RADIUS * r * math.sin(az_r) + 0.5)
    y    = int(_CY - _RADIUS * r * math.cos(az_r) + 0.5)
    return x, y


class RadarDisplay:
    def __init__(self):
        self.predicted_track = []   # [(x, y), ...]  1px white dots
        self.live_track      = []   # [(x, y), ...]  2×2 filled dots
        self._last_live_xy   = None # last pixel coords for dedup
        
        # Local Map (Left Panel, 64x64)
        self.map_data = bytearray(512) # 64x64 MONO_VLSB (64*64/8 = 512)
        self.map_fb   = framebuf.FrameBuffer(self.map_data, 64, 64, framebuf.MONO_VLSB)
        self.observer_lat = None
        self.observer_lon = None

    # ------------------------------------------------------------------
    def set_observer(self, lat, lon):
        """Pre-render the local map once for the current observer location."""
        if self.observer_lat == lat and self.observer_lon == lon:
            return # already rendered
        
        self.observer_lat = lat
        self.observer_lon = lon
        world_map.render_local_map(self.map_fb, lat, lon, width=64, height=64, span_deg=90)
        print(f"RadarDisplay: Local map cached for ({lat:.2f}, {lon:.2f})")

    # ------------------------------------------------------------------
    def set_predicted_track(self, xy_pairs):
        """Set the predicted track (list of (x, y) pixel coords).
        Called once when a pass begins."""
        self.predicted_track = list(xy_pairs)

    # ------------------------------------------------------------------
    def add_live_point(self, x, y):
        """Append a live tracking point if it differs from the last one."""
        if self._last_live_xy and self._last_live_xy == (x, y):
            return  # same pixel — skip
        self._last_live_xy = (x, y)
        self.live_track.append((x, y))

    # ------------------------------------------------------------------
    def reset(self):
        """Clear both tracks (call when pass ends or new pass starts)."""
        self.predicted_track = []
        self.live_track      = []
        self._last_live_xy   = None

    # ------------------------------------------------------------------
    def render(self, disp, sat_name, az_deg, el_deg, lat_deg=None, lon_deg=None, alt_km=None):
        disp.fill(0)

        # --- Left panel: Lat/Lon map or Az/El fallback ---
        if lat_deg is not None and lon_deg is not None and alt_km is not None and g.observer_lat is not None:
            # Ensure map is rendered for current observer
            self.set_observer(g.observer_lat, g.observer_lon)
            
            # Blit static map base
            disp.fb.blit(self.map_fb, 0, 0)
            
            # Draw dynamic FOV and sat on top (of the left panel specifically)
            world_map.draw_fov_on_fb(disp, lat_deg, lon_deg, alt_km, 
                                     g.observer_lat, g.observer_lon, 
                                     width=64, height=64, span_deg=90)
        else:
            # Fallback to Az / El readout
            az_i = int(az_deg + 0.5) % 360
            el_i = int(el_deg + 0.5)
            disp.text(f"Az:{az_i:+04d}", 0, 20)
            disp.text(f"El:{el_i:+03d}", 0, 36)

        # --- Right panel: Radar content ---
        
        # Horizon circle (16-segment)
        prev_x = _CX + _RADIUS
        prev_y = _CY
        for i in range(1, 17):
            angle = 2.0 * math.pi * i / 16
            nx_ = int(_CX + _RADIUS * math.cos(angle) + 0.5)
            ny_ = int(_CY + _RADIUS * math.sin(angle) + 0.5)
            disp.line(prev_x, prev_y, nx_, ny_)
            prev_x, prev_y = nx_, ny_

        # Cardinal pixel ticks
        disp.pixel(_CX,            _CY - _RADIUS - 2)   # N
        disp.pixel(_CX,            _CY + _RADIUS + 2)   # S
        disp.pixel(_CX - _RADIUS - 2, _CY)              # W
        disp.pixel(_CX + _RADIUS + 2, _CY)              # E

        # Predicted track (1×1 white pixels)
        for px, py in self.predicted_track:
            disp.pixel(px, py)

        # Live track (2×2 dots)
        for lx, ly in self.live_track:
            disp.fill_rect(lx, ly, 2, 2)

        # Current-position dot (3×3)
        sx, sy = to_xy(az_deg, el_deg)
        disp.fill_rect(sx - 1, sy - 1, 3, 3)

        disp.show()
