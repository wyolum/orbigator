"""
test_radar_display.py — Radar display test with real next-pass data
===================================================================
Run with:  mpremote run micropython/tests/test_radar_display.py

Phase 1: Fast-forward through the next 24 hours using the cached ISS TLE
         to find the next overhead pass at the stored observer location.
         Collects real az/el waypoints (1 per minute during pass).

Phase 2: Builds predicted track (1px white dots) up-front, then
         animates live tracking dots (2×2) frame-by-frame on the OLED.

Phase 3: Logic assertions (does not require a display).
"""

import math
import time
from machine import I2C, Pin
from sh1106 import SH1106_I2C
import orb_utils as utils
import orb_globals as g

# ── Display init ───────────────────────────────────────────────────────────
i2c  = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
disp = SH1106_I2C(128, 64, i2c)
disp.fill(0); disp.show()
print("Display OK")

# ── Load observer location ─────────────────────────────────────────────────
from observer_frame import ObserverFrame

obs_lat = getattr(g, 'observer_lat', None)
obs_lon = getattr(g, 'observer_lon', None)
if obs_lat is None or obs_lon is None:
    print("Observer location not in globals — fetching from Wyolum...")
    loc = utils.fetch_observer_location()
    if loc:
        obs_lat, obs_lon = loc
    else:
        print("ERROR: Cannot get observer location — using fallback (Reston VA)")
        obs_lat, obs_lon = 38.93, -77.35

obs = ObserverFrame(obs_lat, obs_lon)
print(f"Observer: {obs_lat:.2f}N {obs_lon:.2f}E")

# ── Load ISS TLE from cache ───────────────────────────────────────────────
cache = utils.load_tle_cache()
sat_name = None
tle_data = None
for name in ("ISS", "ISS (ZARYA)"):
    if name in cache:
        sat_name = name
        tle_data = cache[name]
        break

if not tle_data:
    raise Exception("No ISS TLE in cache — run the main app first to populate it.")

line1 = tle_data["line1"]
line2 = tle_data["line2"]
print(f"Using TLE: {sat_name}")

# ── Parse TLE and init SGP4 ───────────────────────────────────────────────
import sgp4 as sgp4_mod
import satellite_position as satpos

epoch_year, epoch_day = utils.parse_tle_epoch(line1)
bstar = float(line1[53:59]) * 10.0 ** float(line1[59:61])
inc   = float(line2[8:16])
raan  = float(line2[17:25])
ecc   = float('0.' + line2[26:33])
argp  = float(line2[34:42])
m0    = float(line2[43:51])
n     = float(line2[52:63])

sgp4 = sgp4_mod.SGP4()
sgp4.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m0, n)

# ── Fast-forward: scan for next overhead pass ─────────────────────────────
print("Scanning for next pass (up to 24h)...")
now_unix   = utils.get_timestamp()
step_s     = 60       # scan every 60 seconds
max_s      = 86400    # look up to 24 hours ahead
pass_points = []      # list of (az_deg, el_deg) per minute during the pass
in_pass    = False
pass_start = None

disp.fill(0)
disp.text("Scanning...", 0, 28)
disp.show()

t = now_unix
end_t = now_unix + max_s
scan_step = 0

while t < end_t:
    t_struct = time.gmtime(t)
    t_tuple  = (t_struct[0], t_struct[1], t_struct[2],
                t_struct[3], t_struct[4], t_struct[5], 0, 0, 0)
    try:
        result = satpos.compute_satellite_geodetic(sgp4, epoch_year, epoch_day, t_tuple)
        ecef   = result.get("ecef", {})
        sx, sy, sz = ecef.get("x", 0), ecef.get("y", 0), ecef.get("z", 0)
        dot    = obs.dot_up(sx, sy, sz)

        if not in_pass and dot > 0:
            in_pass    = True
            pass_start = t
            print(f"  Pass starts at T+{(t - now_unix)//60}min")

        if in_pass:
            az, el = obs.az_el_deg(sx, sy, sz)
            pass_points.append((az, el))
            if dot <= 0:
                in_pass = False
                print(f"  Pass ends at T+{(t - now_unix)//60}min  ({len(pass_points)} pts)")
                break   # Found a full pass — stop scanning
    except Exception as e:
        pass  # skip bad propagation points

    t += step_s
    scan_step += 1
    if scan_step % 60 == 0:
        print(f"  ...T+{(t - now_unix)//3600:.0f}h")

if not pass_points:
    print("No overhead pass found in next 24h — falling back to synthetic pass")
    pass_points = [
        (310, 0), (330, 8), (355, 18), (5, 30), (10, 40),
        (5, 48), (355, 44), (340, 36), (30, 24), (50, 14),
        (60, 6), (62, 2), (63, 0),
    ]
    sat_name = "ISS (SIM)"

print(f"\nPass: {len(pass_points)} waypoints")

# ── Build predicted track + animate live dots ─────────────────────────────
from radar_display import RadarDisplay, to_xy, _CX, _CY, _RADIUS
rd = RadarDisplay()

# Build predicted track (all points as 1px white pixels)
predicted_xy = [to_xy(az, el) for az, el in pass_points]
rd.set_predicted_track(predicted_xy)
print(f"Predicted track: {len(predicted_xy)} points")

# Animate: add live points one at a time (2×2 dots)
print("Animating (2s/frame)... Ctrl-C to skip")
try:
    for step, (az, el) in enumerate(pass_points):
        lx, ly = to_xy(az, el)
        rd.add_live_point(lx, ly)
        rd.render(disp, sat_name, az, el)
        print(f"  t={step:2d}min  Az={az:6.1f}  El={el:5.1f}  px=({lx},{ly})  live={len(rd.live_track)}")
        time.sleep(2)
except KeyboardInterrupt:
    print("  (animation skipped)")

rd.render(disp, sat_name, *pass_points[-1])

# ── Logic assertions ──────────────────────────────────────────────────────
print("\n--- Logic checks ---")
errors = 0

# 1. Got some pass points
if len(pass_points) >= 2:
    print(f"PASS  pass has {len(pass_points)} waypoints")
else:
    print(f"FAIL  not enough pass waypoints: {len(pass_points)}")
    errors += 1

# 2. Zenith maps to display centre
cx, cy = to_xy(0, 90)
if cx == _CX and cy == _CY:
    print(f"PASS  zenith -> ({_CX},{_CY})")
else:
    print(f"FAIL  zenith -> ({cx},{cy}), expected ({_CX},{_CY})")
    errors += 1

# 3. N-horizon on ring
hx, hy = to_xy(0, 0)
dist = math.sqrt((hx - _CX)**2 + (hy - _CY)**2)
if abs(dist - _RADIUS) <= 1.5:
    print(f"PASS  N-horizon at {dist:.1f}px radius (expected {_RADIUS})")
else:
    print(f"FAIL  N-horizon at {dist:.1f}px")
    errors += 1

# 4. Predicted track set correctly
if len(rd.predicted_track) == len(pass_points):
    print(f"PASS  predicted_track has {len(rd.predicted_track)} points")
else:
    print(f"FAIL  predicted_track has {len(rd.predicted_track)}, expected {len(pass_points)}")
    errors += 1

# 5. Live track deduplication works
rd2 = RadarDisplay()
rd2.add_live_point(50, 50)
rd2.add_live_point(50, 50)  # same — should be deduplicated
rd2.add_live_point(51, 50)  # different — should be added
if len(rd2.live_track) == 2:
    print("PASS  live_track deduplication works")
else:
    print(f"FAIL  live_track has {len(rd2.live_track)} points, expected 2")
    errors += 1

if errors == 0:
    print("\n✓ All checks passed.")
else:
    print(f"\n✗ {errors} check(s) failed.")
