"""
radar_display.py - Radar Sky Plot Renderer
==========================================
Renders a radar-style overhead sky view on the 128x64 SH1106 OLED.

Layout (128x64):
  Row  0-14:  Header line  "<SAT> ALERT!"
  Row 14-24:  Az/El readout
  Row 24-63:  Radar circle (horizon = outer ring, zenith = centre)

Coordinate mapping:
  r   = cos(el_rad)         range [0, 1], 1 at horizon, 0 at zenith
  x   = CX + RADIUS * r * sin(az_rad)
  y   = CY - RADIUS * r * cos(az_rad)   (y flipped for display)
"""

import math

# Radar geometry
_CX     = 64   # screen centre X
_CY     = 45   # screen centre Y (lower half of display)
_RADIUS = 18   # horizon ring radius in pixels

# Trail ring buffer  (5-min pass @ 1 Hz = 300 pts)
_TRAIL_LEN = 300
_TRAIL_INTERVAL_MS = 1000   # add one trail point per second max


class RadarDisplay:
    """
    Maintains a fixed-length trail of (az_deg, el_deg) samples
    and renders the full radar display to an SH1106 display object.
    """

    def __init__(self):
        self._trail = [(0.0, 0.0)] * _TRAIL_LEN
        self._trail_idx = 0
        self._trail_count = 0
        self._last_trail_ms = 0   # ticks_ms of last trail append

    # ------------------------------------------------------------------
    def _to_xy(self, az_deg, el_deg):
        """Convert az/el to radar pixel coordinates."""
        az_r = math.radians(az_deg)
        el_r = math.radians(el_deg)
        r    = math.cos(el_r)          # 1 at horizon, 0 at zenith
        x    = int(_CX + _RADIUS * r * math.sin(az_r) + 0.5)
        y    = int(_CY - _RADIUS * r * math.cos(az_r) + 0.5)
        return x, y

    # ------------------------------------------------------------------
    def update(self, az_deg, el_deg, now_ms=None):
        """Append position to trail — throttled to 1 Hz to cover full pass."""
        import time
        if now_ms is None:
            now_ms = time.ticks_ms()
        if self._trail_count > 0 and time.ticks_diff(now_ms, self._last_trail_ms) < _TRAIL_INTERVAL_MS:
            return
        self._trail[self._trail_idx] = (az_deg, el_deg)
        self._trail_idx = (self._trail_idx + 1) % _TRAIL_LEN
        if self._trail_count < _TRAIL_LEN:
            self._trail_count += 1
        self._last_trail_ms = now_ms

    # ------------------------------------------------------------------
    def reset_trail(self):
        """Clear trail (call when satellite rises or changes)."""
        self._trail_count = 0
        self._trail_idx   = 0
        self._last_trail_ms = 0

    # ------------------------------------------------------------------
    def render(self, disp, sat_name, az_deg, el_deg):
        """
        Full radar render. Clears the display and draws:
          - Header + Az/El readout
          - Horizon circle
          - Cross-hair (N/S/E/W ticks)
          - Trail arc
          - Satellite dot
        """
        disp.fill(0)

        # --- Header ---
        name = (sat_name or "SAT")[:7]
        disp.text(f"{name} ALERT!", 0, 0)

        # --- Az/El readout ---
        az_i  = int(az_deg  + 0.5)
        el_i  = int(el_deg  + 0.5)
        disp.text(f"Az:{az_i:03d} El:{el_i:02d}", 0, 10)

        # --- Horizon circle ---
        # Approximate circle with 16 segments
        prev_x = _CX + _RADIUS
        prev_y = _CY
        segs = 16
        for i in range(1, segs + 1):
            angle = 2.0 * math.pi * i / segs
            nx_ = int(_CX + _RADIUS * math.cos(angle) + 0.5)
            ny_ = int(_CY + _RADIUS * math.sin(angle) + 0.5)
            disp.line(prev_x, prev_y, nx_, ny_)
            prev_x, prev_y = nx_, ny_

        # --- Cardinal tick marks (pixels only) ---
        disp.pixel(_CX,            _CY - _RADIUS - 2)  # N
        disp.pixel(_CX,            _CY + _RADIUS + 2)  # S
        disp.pixel(_CX - _RADIUS - 2, _CY)             # W
        disp.pixel(_CX + _RADIUS + 2, _CY)             # E

        # --- Trail arc ---
        if self._trail_count >= 2:
            # Walk ring buffer in chronological order
            start_i = (self._trail_idx - self._trail_count) % _TRAIL_LEN
            prev_tx, prev_ty = None, None
            for j in range(self._trail_count):
                az_t, el_t = self._trail[(start_i + j) % _TRAIL_LEN]
                tx, ty = self._to_xy(az_t, el_t)
                if prev_tx is not None:
                    disp.line(prev_tx, prev_ty, tx, ty)
                prev_tx, prev_ty = tx, ty

        # --- Satellite dot (3x3) ---
        sx, sy = self._to_xy(az_deg, el_deg)
        disp.fill_rect(sx - 1, sy - 1, 3, 3)

        disp.show()
