import math
import framebuf
import os
import time

# Constants
R_EARTH = 6371.0
W = 128
H = 64
CX = W // 2
CY = H // 2
RADIUS = 31 # For circular FOV mode

# Global cache for the world map bitmask
_world_mask = None

def get_world_mask(dat_file="world.dat", mask_file="world_mask.bin"):
    """Load or generate a 128x64 MONO_VLSB bitmask of the world."""
    global _world_mask
    if _world_mask is not None:
        return _world_mask

    # Try loading from binary cache first
    try:
        if mask_file in os.listdir():
            with open(mask_file, "rb") as f:
                data = bytearray(f.read())
                if len(data) == 1024:
                    _world_mask = framebuf.FrameBuffer(data, 128, 64, framebuf.MONO_VLSB)
                    return _world_mask
    except:
        pass

    # Generate from world.dat
    print("Generating world map bitmask...")
    data = bytearray(1024)
    fb = framebuf.FrameBuffer(data, 128, 64, framebuf.MONO_VLSB)
    fb.fill(0)
    
    try:
        with open(dat_file, "r") as f:
            seg = []
            for raw in f:
                line = raw.strip()
                if not line:
                    if len(seg) >= 2:
                        for i in range(len(seg) - 1):
                            p0, p1 = seg[i], seg[i+1]
                            fb.line(p0[0], p0[1], p1[0], p1[1], 1)
                    seg = []
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    # Project to 128x64 equirectangular
                    x = int((lon + 180) * 127 / 360)
                    y = int((90 - lat) * 63 / 180)
                    seg.append((x, y))
    except Exception as e:
        print(f"Map generation error: {e}")

    # Save to binary cache
    try:
        with open(mask_file, "wb") as f:
            f.write(data)
    except:
        pass

    _world_mask = fb
    return _world_mask

def draw_equirectangular(disp, lat_deg, lon_deg, alt_km):
    """Draw equirectangular world map with satirical FOV overlay."""
    mask_fb = get_world_mask()
    # Blit the world map (assumes disp.buffer is a bytearray or compatible)
    disp.fb.blit(mask_fb, 0, 0)
    
    # 1. Project Satellite Position
    sx = int((lon_deg + 180) * 127 / 360)
    sy = int((90 - lat_deg) * 63 / 180)
    
    # 2. Draw FOV Footprint
    if alt_km > 0:
        alpha = math.acos(R_EARTH / (R_EARTH + alt_km))
        lat0_r = math.radians(lat_deg)
        lon0_r = math.radians(lon_deg)
        
        steps = 16
        pts = []
        for i in range(steps + 1):
            theta = 2.0 * math.pi * i / steps
            # Spherical trig for points at distance alpha
            lat_r = math.asin(math.sin(lat0_r) * math.cos(alpha) + 
                             math.cos(lat0_r) * math.sin(alpha) * math.cos(theta))
            dlon = math.atan2(math.sin(theta) * math.sin(alpha) * math.cos(lat0_r),
                              math.cos(alpha) - math.sin(lat0_r) * math.sin(lat_r))
            lon_r = lon0_r + dlon
            
            # Project to screen
            px = int((math.degrees(lon_r) + 180) % 360 * 127 / 360)
            py = int((90 - math.degrees(lat_r)) * 63 / 180)
            pts.append((px, py))
            
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i+1]
            # Avoid drawing lines across the screen wrap
            if abs(p0[0] - p1[0]) < 64:
                disp.line(p0[0], p0[1], p1[0], p1[1], 1)

    # 3. Blinking Sat Marker
    if (int(time.time() * 2) % 2) == 0:
        disp.fill_rect(sx - 1, sy - 1, 3, 3, 1)
    else:
        disp.pixel(sx, sy, 1)

def subsatellite_point(px, py, pz):
    r = math.sqrt(px * px + py * py + pz * pz)
    if r < 1.0: return 0.0, 0.0, 0.0
    lat = math.asin(pz / r)
    lon = math.atan2(py, px)
    alt = r - R_EARTH
    return lat, lon, alt

def fov_half_angle(alt_km):
    if alt_km <= 0: return 0.0
    return math.acos(R_EARTH / (R_EARTH + alt_km))

def draw_fov(disp, lat0, lon0, fov_r, dat_file="world.dat"):
    """Keep legacy circular FOV for compatibility if needed."""
    # ... legacy implementation or redirect to equirectangular ...
    draw_equirectangular(disp, math.degrees(lat0), math.degrees(lon0), 400.0) # Dummy alt if unknown

