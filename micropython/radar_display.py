"""
radar_display.py - Radar Sky Plot Renderer
==========================================
Layout (128×64):
  Left  (0–63):   Az: +ddd  /  El: +dd   (two lines, vertically centred)
  Right (64–127): Radar circle, full height, horizon ring = outer edge

Coordinate mapping (right panel):
  r = cos(el_rad)           1.0 at horizon, 0 at zenith
  x = CX + RADIUS * r * sin(az_rad)
  y = CY - RADIUS * r * cos(az_rad)

Two drawing layers:
  predicted_track  – 1×1 white pixels computed once at pass start
  live_track       – 2×2 dots added in real-time as satellite crosses
"""

import math

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
    def render(self, disp, sat_name, az_deg, el_deg):
        disp.fill(0)

        # --- Left panel: Az / El readout ---
        az_i = int(az_deg + 0.5) % 360
        el_i = int(el_deg + 0.5)
        disp.text(f"Az:{az_i:+04d}", 0, 20)
        disp.text(f"El:{el_i:+03d}", 0, 36)

        # --- Horizon circle (16-segment) ---
        prev_x = _CX + _RADIUS
        prev_y = _CY
        for i in range(1, 17):
            angle = 2.0 * math.pi * i / 16
            nx_ = int(_CX + _RADIUS * math.cos(angle) + 0.5)
            ny_ = int(_CY + _RADIUS * math.sin(angle) + 0.5)
            disp.line(prev_x, prev_y, nx_, ny_)
            prev_x, prev_y = nx_, ny_

        # --- Cardinal pixel ticks ---
        disp.pixel(_CX,            _CY - _RADIUS - 2)   # N
        disp.pixel(_CX,            _CY + _RADIUS + 2)   # S
        disp.pixel(_CX - _RADIUS - 2, _CY)              # W
        disp.pixel(_CX + _RADIUS + 2, _CY)              # E

        # --- Predicted track (1×1 white pixels) ---
        for px, py in self.predicted_track:
            disp.pixel(px, py)

        # --- Live track (2×2 dots) ---
        for lx, ly in self.live_track:
            disp.fill_rect(lx, ly, 2, 2)

        # --- Current-position dot (3×3) ---
        sx, sy = to_xy(az_deg, el_deg)
        disp.fill_rect(sx - 1, sy - 1, 3, 3)

        disp.show()
