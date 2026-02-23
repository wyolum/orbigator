"""
test_radar_display.py — On-device radar display test
=====================================================
Run with:  mpremote run micropython/tests/test_radar_display.py

Injects a synthetic 13-point ISS pass into the trail buffer and
animates the dot across the display every 2 seconds so you can
visually inspect the radar rendering without waiting for a real pass.

Synthetic pass (Reston VA):
  Rise  Az=310° El=0°  (NW)  →  Peak Az=5° El=48°  →  Set Az=63° El=0° (ENE)
"""

import math
import time
from machine import I2C, Pin
from sh1106 import SH1106_I2C
from radar_display import RadarDisplay, _CX, _CY, _RADIUS

# ── Init display ───────────────────────────────────────────────────────────
i2c  = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
disp = SH1106_I2C(128, 64, i2c)
disp.fill(0); disp.show()
print("Display OK")

# ── Synthetic pass ─────────────────────────────────────────────────────────
PASS = [
    (310,  0),   # 0 min  rise NW
    (330,  8),   # 1
    (355, 18),   # 2
    (  5, 30),   # 3
    ( 10, 40),   # 4
    (  5, 48),   # 5  peak
    (355, 44),   # 6
    (340, 36),   # 7
    ( 30, 24),   # 8
    ( 50, 14),   # 9
    ( 60,  6),   # 10
    ( 62,  2),   # 11
    ( 63,  0),   # 12 set ENE
]

# ── Load entire trail at once (bypass 1-min throttle) ─────────────────────
rd = RadarDisplay()
for az, el in PASS:
    rd._trail[rd._trail_idx] = (az, el)
    rd._trail_idx = (rd._trail_idx + 1) % len(rd._trail)
    rd._trail_count = min(rd._trail_count + 1, len(rd._trail))
rd._last_trail_ms = time.ticks_ms()  # prevent throttle blocking future adds

print(f"Trail loaded: {rd._trail_count} waypoints")
print("Animating (2s per minute)... Ctrl-C to skip to logic checks")

# ── Animate dot along the pass ─────────────────────────────────────────────
try:
    for step, (az, el) in enumerate(PASS):
        rd.render(disp, "ISS", az, el)
        print(f"  t={step:2d}min  Az={az:3d}  El={el:2d}")
        time.sleep(2)
except KeyboardInterrupt:
    print("  (animation skipped)")

# Final frame
rd.render(disp, "ISS", *PASS[-1])

# ── Logic assertions ───────────────────────────────────────────────────────
print("\n--- Logic checks ---")
errors = 0

# 1. Trail count
if rd._trail_count == len(PASS):
    print(f"PASS  trail_count == {len(PASS)}")
else:
    print(f"FAIL  trail_count {rd._trail_count} != {len(PASS)}")
    errors += 1

# 2. Zenith (el=90) maps to display centre
cx, cy = rd._to_xy(0, 90)
if cx == _CX and cy == _CY:
    print(f"PASS  zenith -> ({_CX},{_CY})")
else:
    print(f"FAIL  zenith -> ({cx},{cy}), expected ({_CX},{_CY})")
    errors += 1

# 3. North horizon (az=0, el=0) lies on horizon ring
hx, hy = rd._to_xy(0, 0)
dist = math.sqrt((hx - _CX)**2 + (hy - _CY)**2)
if abs(dist - _RADIUS) <= 1.5:
    print(f"PASS  N-horizon at {dist:.1f}px radius (expected {_RADIUS})")
else:
    print(f"FAIL  N-horizon at {dist:.1f}px, expected {_RADIUS}")
    errors += 1

# 4. East horizon (az=90, el=0) lies on horizon ring
ex, ey = rd._to_xy(90, 0)
dist_e = math.sqrt((ex - _CX)**2 + (ey - _CY)**2)
if abs(dist_e - _RADIUS) <= 1.5:
    print(f"PASS  E-horizon at {dist_e:.1f}px radius (expected {_RADIUS})")
else:
    print(f"FAIL  E-horizon at {dist_e:.1f}px, expected {_RADIUS}")
    errors += 1

# 5. Throttle: second add within 1 min should be blocked
rd2 = RadarDisplay()
now = time.ticks_ms()
rd2.update(0, 0, now)
before = rd2._trail_count
rd2.update(45, 20, now + 500)   # 500ms later — should be blocked
if rd2._trail_count == before:
    print("PASS  trail throttle blocks rapid updates")
else:
    print("FAIL  trail throttle did not block rapid update")
    errors += 1

if errors == 0:
    print("\n\u2713 All checks passed.")
else:
    print(f"\n\u2717 {errors} check(s) failed.")
