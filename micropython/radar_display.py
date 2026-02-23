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
"""

import math

# Radar geometry — right half, full 64px height
_CX     = 96   # centre of right panel
_CY     = 32   # vertical centre
_RADIUS = 29   # 64/2 - 3 px margin

# Trail ring buffer  (1 pt/min × 20 pts → 20-min max pass)
_TRAIL_LEN         = 20
_TRAIL_INTERVAL_MS = 60_000   # one trail point per minute


class RadarDisplay:
    def __init__(self):
        self._trail         = [(0.0, 0.0)] * _TRAIL_LEN
        self._trail_idx     = 0
        self._trail_count   = 0
        self._last_trail_ms = 0

    # ------------------------------------------------------------------
    def _to_xy(self, az_deg, el_deg):
        az_r = math.radians(az_deg)
        el_r = math.radians(el_deg)
        r    = math.cos(el_r)
        x    = int(_CX + _RADIUS * r * math.sin(az_r) + 0.5)
        y    = int(_CY - _RADIUS * r * math.cos(az_r) + 0.5)
        return x, y

    # ------------------------------------------------------------------
    def update(self, az_deg, el_deg, now_ms=None):
        """Append to trail, throttled to 1 Hz."""
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
        self._trail_count   = 0
        self._trail_idx     = 0
        self._last_trail_ms = 0

    # ------------------------------------------------------------------
    def render(self, disp, sat_name, az_deg, el_deg):
        disp.fill(0)

        # --- Left panel: Az / El readout ---
        az_i = int(az_deg + 0.5) % 360
        el_i = int(el_deg + 0.5)
        # Use explicit sign; Az is 0-360 so always positive
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

        # --- Trail arc ---
        if self._trail_count >= 2:
            start_i = (self._trail_idx - self._trail_count) % _TRAIL_LEN
            px, py = None, None
            for j in range(self._trail_count):
                az_t, el_t = self._trail[(start_i + j) % _TRAIL_LEN]
                tx, ty = self._to_xy(az_t, el_t)
                if px is not None:
                    disp.line(px, py, tx, ty)
                px, py = tx, ty

        # --- Current-position dot (3×3) ---
        sx, sy = self._to_xy(az_deg, el_deg)
        disp.fill_rect(sx - 1, sy - 1, 3, 3)

        disp.show()
