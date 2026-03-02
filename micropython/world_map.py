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

# Global cache for the world map bitmask and segments
_world_mask = None
_world_segments = None

def get_world_segments(dat_file="world.dat"):
    """Load world segments into memory as a list of lists of (lon, lat) tuples."""
    global _world_segments
    if _world_segments is not None:
        return _world_segments
    
    _world_segments = []
    try:
        with open(dat_file, "r") as f:
            seg = []
            for raw in f:
                line = raw.strip()
                if not line:
                    if len(seg) >= 2:
                        _world_segments.append(seg)
                    seg = []
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    seg.append((lon, lat))
            if seg:
                _world_segments.append(seg)
    except Exception as e:
        print(f"Error loading segments: {e}")
    return _world_segments

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

    # Generate from segments
    print("Generating world map bitmask...")
    data = bytearray(1024)
    fb = framebuf.FrameBuffer(data, 128, 64, framebuf.MONO_VLSB)
    fb.fill(0)
    
    segments = get_world_segments(dat_file)
    for seg in segments:
        for i in range(len(seg) - 1):
            p0, p1 = seg[i], seg[i+1]
            x0 = int((p0[0] + 180) * 127 / 360)
            y0 = int((90 - p0[1]) * 63 / 180)
            x1 = int((p1[0] + 180) * 127 / 360)
            y1 = int((90 - p1[1]) * 63 / 180)
            if abs(x0 - x1) < 64: # Avoid wraps
                fb.line(x0, y0, x1, y1, 1)

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
    disp.fb.blit(mask_fb, 0, 0)
    
    sx = int((lon_deg + 180) * 127 / 360)
    sy = int((90 - lat_deg) * 63 / 180)
    
    if alt_km > 0:
        alpha = math.acos(R_EARTH / (R_EARTH + alt_km))
        lat0_r = math.radians(lat_deg)
        lon0_r = math.radians(lon_deg)
        
        steps = 16
        pts = []
        for i in range(steps + 1):
            theta = 2.0 * math.pi * i / steps
            lat_r = math.asin(math.sin(lat0_r) * math.cos(alpha) + 
                             math.cos(lat0_r) * math.sin(alpha) * math.cos(theta))
            dlon = math.atan2(math.sin(theta) * math.sin(alpha) * math.cos(lat0_r),
                              math.cos(alpha) - math.sin(lat0_r) * math.sin(lat_r))
            lon_r = lon0_r + dlon
            px = int((math.degrees(lon_r) + 180) % 360 * 127 / 360)
            py = int((90 - math.degrees(lat_r)) * 63 / 180)
            pts.append((px, py))
            
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i+1]
            if abs(p0[0] - p1[0]) < 64:
                disp.line(p0[0], p0[1], p1[0], p1[1], 1)

    if (int(time.time() * 2) % 2) == 0:
        disp.fill_rect(sx - 1, sy - 1, 3, 3, 1)
    else:
        disp.pixel(sx, sy, 1)

def render_local_map(fb, center_lat, center_lon, width=64, height=64, span_deg=90):
    """Render a zoomed-in local map into the provided FrameBuffer."""
    segments = get_world_segments()
    fb.fill(0)
    
    # Scale: width pixels covers span_deg degrees
    scale_x = width / span_deg
    scale_y = height / span_deg
    
    def project(lon, lat):
        # Center lon/lat maps to width/2, height/2
        dlon = (lon - center_lon + 180) % 360 - 180
        dlat = lat - center_lat
        px = int(width // 2 + dlon * scale_x)
        py = int(height // 2 - dlat * scale_y)
        return px, py

    for seg in segments:
        last_p = None
        for lon, lat in seg:
            p = project(lon, lat)
            if last_p is not None:
                # Clip lines that are definitely far outside the buffer for speed
                # but fb.line handles most clipping.
                x0, y0 = last_p
                x1, y1 = p
                # Simple wrap detection for longitudinal gaps
                if abs(x0 - x1) < width:
                    fb.line(x0, y0, x1, y1, 1)
            last_p = p

def draw_fov_on_fb(fb, lat0, lon0, alt_km, center_lat, center_lon, width=64, height=64, span_deg=90):
    """Draw satellite and FOV footprint on a local map buffer."""
    if alt_km <= 0: return

    scale_x = width / span_deg
    scale_y = height / span_deg

    def project(lon, lat):
        dlon = (lon - lon0 + (lon0 - center_lon) + 180) % 360 - 180
        dlat = lat - center_lat
        px = int(width // 2 + dlon * scale_x)
        py = int(height // 2 - dlat * scale_y)
        return px, py

    # 1. FOV Ring
    alpha = math.acos(R_EARTH / (R_EARTH + alt_km))
    lat0_r = math.radians(lat0)
    lon0_r = math.radians(lon0)
    
    steps = 16
    last_p = None
    for i in range(steps + 1):
        theta = 2.0 * math.pi * i / steps
        lat_r = math.asin(math.sin(lat0_r) * math.cos(alpha) + 
                         math.cos(lat0_r) * math.sin(alpha) * math.cos(theta))
        dlon = math.atan2(math.sin(theta) * math.sin(alpha) * math.cos(lat0_r),
                          math.cos(alpha) - math.sin(lat0_r) * math.sin(lat_r))
        lon_r = lon0_r + dlon
        p = project(math.degrees(lon_r), math.degrees(lat_r))
        
        if last_p and abs(last_p[0] - p[0]) < width:
            fb.line(last_p[0], last_p[1], p[0], p[1], 1)
        last_p = p

    # 2. Satellite Marker
    sx, sy = project(lon0, lat0)
    if 0 <= sx < width and 0 <= sy < height:
        if (int(time.time() * 2) % 2) == 0:
            fb.fill_rect(sx - 1, sy - 1, 3, 3, 1)
        else:
            fb.pixel(sx, sy, 1)

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
    """Legacy/Simplified FOV drawing."""
    draw_equirectangular(disp, math.degrees(lat0), math.degrees(lon0), 400.0)

