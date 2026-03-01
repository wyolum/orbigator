"""
test_world_map_fov.py — Plot continents visible from the ISS FOV
================================================================
Run with:  mpremote run micropython/tests/test_world_map_fov.py

Given an ECF position p_ecf (km), computes the sub-satellite point
and field-of-view radius, then draws the visible coastlines on the
OLED using an azimuthal equidistant projection inside a circle.
"""

import math
from machine import Pin, I2C
from sh1106 import SH1106_I2C

# ── Display init ──────────────────────────────────────────────────────────
i2c  = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
disp = SH1106_I2C(128, 64, i2c)
disp.fill(0)
disp.show()
print("Display OK")

# ── Configuration ─────────────────────────────────────────────────────────
W = 128
H = 64

# Display circle geometry — centred on screen, fits in 64px height
CX = W // 2       # 64
CY = H // 2       # 32
RADIUS = 31        # pixel radius of the FOV circle (full 64px height)

R_EARTH = 6371.0   # km

DAT_FILE = "world.dat"

# ── ISS ECF position (km) — change this! ─────────────────────────────────
# Example: ISS over the US east coast (~38°N, ~77°W, ~408 km altitude)
p_ecf = (1202.0, -5205.0, 4174.0)


# ── Math helpers ──────────────────────────────────────────────────────────
def subsatellite_point(px, py, pz):
    """ECF position (km) → (lat_rad, lon_rad, altitude_km)."""
    r = math.sqrt(px * px + py * py + pz * pz)
    lat = math.asin(pz / r)
    lon = math.atan2(py, px)
    alt = r - R_EARTH
    return lat, lon, alt


def fov_half_angle(alt_km):
    """Half-angle of the Earth disk as seen from altitude (radians).
    This is the angular radius of the FOV circle on the surface."""
    return math.acos(R_EARTH / (R_EARTH + alt_km))


def angular_distance(lat0, lon0, lat1, lon1):
    """Great-circle angular distance (radians) between two points."""
    cos_c = (math.sin(lat0) * math.sin(lat1) +
             math.cos(lat0) * math.cos(lat1) * math.cos(lon1 - lon0))
    # Clamp for floating-point safety
    if cos_c > 1.0:
        cos_c = 1.0
    elif cos_c < -1.0:
        cos_c = -1.0
    return math.acos(cos_c)


def bearing(lat0, lon0, lat1, lon1):
    """Initial bearing (radians, CW from north) from point 0 to point 1."""
    dlon = lon1 - lon0
    y = math.sin(dlon) * math.cos(lat1)
    x = (math.cos(lat0) * math.sin(lat1) -
         math.sin(lat0) * math.cos(lat1) * math.cos(dlon))
    return math.atan2(y, x)


def project(lat_r, lon_r, lat0, lon0, fov_r):
    """Azimuthal equidistant projection → (px_x, px_y) or None if outside FOV.
    Maps angular distance [0, fov_r] to pixel radius [0, RADIUS]."""
    dist = angular_distance(lat0, lon0, lat_r, lon_r)
    if dist > fov_r:
        return None
    az = bearing(lat0, lon0, lat_r, lon_r)
    r_px = dist / fov_r * RADIUS
    x = int(CX + r_px * math.sin(az) + 0.5)
    y = int(CY - r_px * math.cos(az) + 0.5)
    return x, y


# ── Drawing ───────────────────────────────────────────────────────────────
def draw_fov_circle():
    """Draw the FOV boundary circle."""
    prev_x = CX + RADIUS
    prev_y = CY
    steps = 32
    for i in range(1, steps + 1):
        a = 2.0 * math.pi * i / steps
        nx = int(CX + RADIUS * math.cos(a) + 0.5)
        ny = int(CY + RADIUS * math.sin(a) + 0.5)
        _draw_line(prev_x, prev_y, nx, ny)
        prev_x, prev_y = nx, ny


def _draw_line(x0, y0, x1, y1):
    """Bresenham line within screen bounds."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < W and 0 <= y0 < H:
            disp.pixel(x0, y0, 1)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def load_and_draw(lat0, lon0, fov_r):
    """Parse world.dat and draw visible coastline segments."""
    seg = []       # current segment of projected (x, y) pairs
    drawn = 0
    segs = 0

    with open(DAT_FILE, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                # End of segment → draw
                if len(seg) >= 2:
                    for i in range(len(seg) - 1):
                        p0 = seg[i]
                        p1 = seg[i + 1]
                        if p0 is not None and p1 is not None:
                            _draw_line(p0[0], p0[1], p1[0], p1[1])
                            drawn += 1
                    segs += 1
                elif len(seg) == 1 and seg[0] is not None:
                    x, y = seg[0]
                    if 0 <= x < W and 0 <= y < H:
                        disp.pixel(x, y, 1)
                    drawn += 1
                    segs += 1
                seg = []
                continue

            parts = line.split()
            if len(parts) >= 2:
                try:
                    lon = math.radians(float(parts[0]))
                    lat = math.radians(float(parts[1]))
                    seg.append(project(lat, lon, lat0, lon0, fov_r))
                except ValueError:
                    pass

        # Handle last segment
        if len(seg) >= 2:
            for i in range(len(seg) - 1):
                p0 = seg[i]
                p1 = seg[i + 1]
                if p0 is not None and p1 is not None:
                    _draw_line(p0[0], p0[1], p1[0], p1[1])
                    drawn += 1
            segs += 1

    print(f"Drew {segs} segments, {drawn} lines")


# ── Main ──────────────────────────────────────────────────────────────────
px, py, pz = p_ecf
lat0, lon0, alt = subsatellite_point(px, py, pz)
fov_r = fov_half_angle(alt)

print(f"ECF: ({px:.0f}, {py:.0f}, {pz:.0f}) km")
print(f"Sub-sat: {math.degrees(lat0):.1f}°N  {math.degrees(lon0):.1f}°E")
print(f"Altitude: {alt:.0f} km")
print(f"FOV half-angle: {math.degrees(fov_r):.1f}°")

draw_fov_circle()
load_and_draw(lat0, lon0, fov_r)

# Mark sub-satellite point (centre dot)
disp.fill_rect(CX - 1, CY - 1, 3, 3, 1)

disp.show()
print("Done! FOV map is on the OLED.")
