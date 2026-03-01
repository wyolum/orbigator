"""
test_world_map.py — Plot world.dat continents on the OLED
=========================================================
Run with:  mpremote run micropython/tests/test_world_map.py

Reads world.dat (lon/lat pairs, blank lines separate coastline segments)
and draws them on the 128x64 OLED using equirectangular projection.

The map can be centred on any longitude by changing CENTER_LON below.
"""

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
CENTER_LON = 0  # Change to e.g. -98 to centre on the US, or 135 for Australia
DAT_FILE = "world.dat"


def lon_lat_to_px(lon, lat):
    """Equirectangular: lon/lat → pixel (x, y).
    Wraps longitude around CENTER_LON so the map can be recentred."""
    # Shift longitude relative to centre, wrap to [-180, 180)
    rel = (lon - CENTER_LON + 180) % 360 - 180
    x = int((rel + 180) / 360 * W)
    y = int((90 - lat) / 180 * H)
    return x, y


def load_and_draw():
    """Parse world.dat and draw coastline segments onto the display."""
    seg = []       # current segment of (x, y) pairs
    drawn = 0      # total pixels drawn
    segs = 0       # segments drawn

    with open(DAT_FILE, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                # Blank line = end of segment → draw it
                if len(seg) >= 2:
                    for i in range(len(seg) - 1):
                        x0, y0 = seg[i]
                        x1, y1 = seg[i + 1]
                        # Skip wrap-around lines that span most of the screen
                        if abs(x1 - x0) > W // 2:
                            continue
                        _draw_line(x0, y0, x1, y1)
                        drawn += 1
                    segs += 1
                elif len(seg) == 1:
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
                    lon = float(parts[0])
                    lat = float(parts[1])
                    seg.append(lon_lat_to_px(lon, lat))
                except ValueError:
                    pass

        # Handle last segment if file doesn't end with blank line
        if len(seg) >= 2:
            for i in range(len(seg) - 1):
                x0, y0 = seg[i]
                x1, y1 = seg[i + 1]
                if abs(x1 - x0) > W // 2:
                    continue
                _draw_line(x0, y0, x1, y1)
                drawn += 1
            segs += 1
        elif len(seg) == 1:
            x, y = seg[0]
            if 0 <= x < W and 0 <= y < H:
                disp.pixel(x, y, 1)
                drawn += 1
            segs += 1

    print(f"Drew {segs} segments, {drawn} line sections")


def _draw_line(x0, y0, x1, y1):
    """Bresenham line — works within framebuf pixel-by-pixel."""
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


# ── Main ──────────────────────────────────────────────────────────────────
print(f"Loading {DAT_FILE} (center_lon={CENTER_LON})...")
load_and_draw()
disp.show()
print("Done! Map is on the OLED.")
