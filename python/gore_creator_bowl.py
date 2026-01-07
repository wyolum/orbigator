#!/usr/bin/env python3
"""
gore_creator_bowl.py

Generate gores for a 12-inch diameter bowl (open at south pole).
Layout: 2 gores per page on 11x17 inch paper (Letter/Tabloid).
Total 8 gores (4 sheets).

Usage:
    python gore_creator_bowl.py <map_image> [diameter_in] [min_lat]

"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
from matplotlib.transforms import Affine2D
from PIL import Image, ImageOps
import sys, os
import math

def get_gore_coordinates(diameter_in, num_gores, min_lat_deg, samples=500):
    R = diameter_in / 2.0
    dlam = 2 * np.pi / num_gores
    
    # Latitude range: South (min_lat) to North (+90)
    min_phi = np.radians(min_lat_deg)
    phis = np.linspace(min_phi, np.pi/2, samples)
    
    # Calculate Gore Coordinates
    # Sanson-Flamsteed (Sinusoidal) projection geometry
    # Width at phi = (2*pi*R * cos(phi)) / num_gores
    # x is +/- half width
    x_width = R * dlam * np.cos(phis)
    xL = -0.5 * x_width
    xR =  0.5 * x_width
    y  =  R * phis 
    
    return phis, xL, xR, y

def build_path_from_coords(xL, xR, y):
    # Build Path vertices
    # Trace up left side, then down right side
    verts = np.vstack([
        np.column_stack((xL, y)),         # Left side up to North Pole
        np.column_stack((xR[::-1], y[::-1])), # Right side down to South cut
        np.column_stack((xL[0], y[0]))    # Close loop at bottom left
    ])
    
    codes = ([Path.MOVETO] +
             [Path.LINETO] * (len(xL)-1) +
             [Path.LINETO] * (len(xR)) +
             [Path.CLOSEPOLY])
             
    return Path(verts, codes)

def warp_slice_to_gore(slice_img, diameter_in, num_gores, min_lat_deg):
    W_slice, H_slice = slice_img.size
    
    # Check if min_lat_deg is > 90 (impossible) or < -90. clamp.
    min_lat_deg = max(-90.0, min(90.0, min_lat_deg))
    
    # Determine the pixel range corresponding to [min_lat, 90]
    # Source image is assumed -90 (bottom) to +90 (top)
    # Row 0 is +90. Row H is -90.
    
    # Map min_lat to row index
    # lat = 90 - (row / H) * 180
    # row = (90 - lat) / 180 * H
    max_row = int((90 - min_lat_deg) / 180.0 * H_slice)
    if max_row > H_slice: max_row = H_slice
    if max_row < 1: max_row = 1
    
    # Crop the slice to just the needed latitude range
    # From top (0) to max_row
    active_img = slice_img.crop((0, 0, W_slice, max_row))
    W_act, H_act = active_img.size
    
    warped = Image.new("RGBA", (W_act, H_act), (0,0,0,0))
    
    # Create array of latitudes for the cropped rows
    # They go from +90 down to min_lat_deg
    phis = np.linspace(np.pi/2, np.radians(min_lat_deg), H_act)
    
    for j in range(H_act):
        phi = phis[j]
        # Calculate width scaling factor at this latitude
        # At equator (phi=0), scale = 1. At pole (phi=pi/2), scale = 0
        scale = abs(np.cos(phi))
        
        if scale < 0.001:
            new_w = 1
        else:
            new_w = max(1, int(round(W_act * scale)))
            
        # Get the row
        row_img = active_img.crop((0, j, W_act, j+1))
        
        # Resize row to compress it horizontally
        row_resized = row_img.resize((new_w, 1), Image.BICUBIC)
        
        # Paste centered
        offset_x = (W_act - new_w) // 2
        warped.paste(row_resized, (offset_x, j))
        
    return warped

def generate_synthetic_map():
    print("Generating synthetic map from vector data (geopandas)...")
    try:
        import geopandas as gpd
        from io import BytesIO
    except ImportError:
        print("Error: geopandas not found. Please install: pip install geopandas shapely")
        return None

    # Load low-res world data
    world = None
    
    # Method 1: Try deprecated datasets (if available in some versions)
    try:
        if hasattr(gpd, 'datasets'):
             world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    except:
        pass
        
    # Method 2: Try direct URL (GitHub mirror of Natural Earth)
    if world is None:
        print("Downloading vector map data...")
        url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
        try:
             world = gpd.read_file(url)
        except Exception as e:
             print(f"Error fetching map data: {e}")
             return None

    # Determine bounds
    # Equirectangular: -180 to 180 lon, -90 to 90 lat
    
    # Plotting
    # We need a high-res canvas to ensure good print quality
    # 3600 x 1800 px (10 px per degree) is decent? 
    # Let's target ~4000px width.
    dpi = 300
    w_inch = 13.33 # 4000 / 300
    h_inch = 6.66
    
    fig, ax = plt.subplots(figsize=(w_inch, h_inch), dpi=dpi)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Background (Oceans) -> Blue? Or Transparent?
    # User said "simple version". Maybe simple outlines on white?
    # Blue Marble was requested before. Let's do Blue background for continuity.
    # Or maybe White background with Black lines is safer for "simple". 
    # Let's do White with Black outlines (Outline Map).
    
    # Plot countries
    world.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.8)
    
    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=False)
    plt.close(fig)
    buf.seek(0)
    
    img = Image.open(buf).convert("RGBA")
    return img

def create_sheets(image_path=None, diameter_in=12.0, total_gores=12, gores_per_sheet=3, min_lat_deg=-60, mirror=False):
    # Load Image
    if image_path:
        print(f"Loading {image_path}...")
        try:
            img = Image.open(image_path).convert("RGBA")
        except Exception as e:
            print(f"Error opening image: {e}")
            return
    else:
        img = generate_synthetic_map()
        if img is None:
            return
        # Synthetic map handling:
        img = img.resize((4000, 2000), Image.BICUBIC)
        image_path = "vector_map" # for filename generation

    if mirror:
        print("Mirroring image...")
        img = ImageOps.mirror(img)

    W, H = img.size
    
    num_sheets = math.ceil(total_gores / gores_per_sheet)
    slice_w_px = W / total_gores
    
    # Pre-calculate geometry
    phis, xL_base, xR_base, y = get_gore_coordinates(diameter_in, total_gores, min_lat_deg)
    
    # Build standard path for image clipping
    clip_path = build_path_from_coords(xL_base, xR_base, y)
    
    # Build path with West Tab (Left side extended)
    # Tab width: 0.25 inches at equator, scaling with cos(phi)
    tab_width_max = 0.25
    tab_offset = tab_width_max * np.cos(phis)
    
    # Generate 6 individual tabs with relief notches (gaps)
    xL_cut = xL_base.copy() # Default to fold line
    
    # Adjust tab count based on gore length? 
    # For now keep 6 tabs per gore.
    num_tabs = 6
    gap_ratio = 0.1 # 10% of segment is gap
    
    phi_start = phis[0]
    phi_end = phis[-1] # ~90 deg
    phi_range = phi_end - phi_start
    seg_len = phi_range / num_tabs
    
    for i in range(num_tabs):
        start_seg = phi_start + i * seg_len
        # Define tab active range: [start + gap/2, end - gap/2]
        t_start = start_seg + (seg_len * gap_ratio * 0.5)
        t_end   = start_seg + seg_len - (seg_len * gap_ratio * 0.5)
        
        mask = (phis >= t_start) & (phis <= t_end)
        xL_cut[mask] = xL_base[mask] - tab_offset[mask]
    
    xL_tab = xL_cut
    
    # Update x_min to reflect the tabs (can go further left)
    xL_tab_min = xL_tab.min()
    
    cut_path_with_tab = build_path_from_coords(xL_tab, xR_base, y)
    
    x_min = xL_tab_min
    x_max = xR_base.max()
    y_min = y.min()
    y_max = y.max()
    
    gore_width_phys = x_max - x_min
    gore_height_phys = y_max - y_min
    
    print(f"Geometry: {diameter_in}\" Sphere, {total_gores} gores.")
    print(f"Gore Dims (w/Tab): {gore_width_phys:.2f}\" x {gore_height_phys:.2f}\"")
    print(f"Latitude Coverage: 90N to {min_lat_deg}S")
    print(f"Layout: {num_sheets} sheets, {gores_per_sheet} gores/sheet")
    
    # Paper Settings
    PAGE_W, PAGE_H = 11.0, 17.0 # Portrait 11x17
    
    # Check if it fits
    total_content_width = (gore_width_phys * gores_per_sheet) + 0.5 # with spacing
    if total_content_width > PAGE_W:
        print(f"WARNING: Content width {total_content_width:.2f}\" exceeds page width {PAGE_W}\"")
    if gore_height_phys > PAGE_H:
         print(f"WARNING: Content height {gore_height_phys:.2f}\" exceeds page height {PAGE_H}\"")

    out_prefix = os.path.splitext(os.path.basename(image_path))[0]
    
    # Generate Sheets
    for sheet_idx in range(num_sheets):
        fig = plt.figure(figsize=(PAGE_W, PAGE_H))
        ax = fig.add_subplot(111)
        ax.set_xlim(0, PAGE_W)
        ax.set_ylim(0, PAGE_H)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Add cut markers / margins
        margin_x = (PAGE_W - (gore_width_phys * gores_per_sheet)) / 2.0
        # Center vertically
        
        # Process gores for this sheet
        start_gore = sheet_idx * gores_per_sheet
        
        # Don't exceed total_gores
        gores_on_this_sheet = min(gores_per_sheet, total_gores - start_gore)
        
        for g_idx in range(gores_on_this_sheet):
            global_gore_idx = start_gore + g_idx
            print(f"Processing Gore {global_gore_idx+1}/{total_gores}...")
            
            # 1. extract slice
            left_px = int(global_gore_idx * slice_w_px)
            right_px = int((global_gore_idx + 1) * slice_w_px)
            if global_gore_idx == total_gores - 1:
                right_px = W
                
            slice_img = img.crop((left_px, 0, right_px, H))
            
            # 2. Warp
            warped_gore_img = warp_slice_to_gore(slice_img, diameter_in, total_gores, min_lat_deg)
            
            # 3. Place on Page
            # Shift X: Margin + Index*Width + HalfWidth (since centered)
            shift_x = margin_x + (g_idx * gore_width_phys) + (gore_width_phys/2.0)
            
            # Shift Y: PageCenter - (Top+Bottom)/2
            shift_y = (PAGE_H / 2.0) - ((y_max + y_min) / 2.0)
            
            trans = Affine2D().translate(shift_x, shift_y) + ax.transData
            
            # Draw Image (Clipped to standard gore)
            ax.imshow(warped_gore_img,
                      extent=[xL_base.min(), xR_base.max(), y_min, y_max], 
                      # Note: Extent must use the bounds of the Standard Gore for mapping!
                      # Not the tab bounds.
                      origin='upper',
                      transform=trans,
                      clip_path=patches.PathPatch(clip_path, transform=trans),
                      clip_on=True)
                      
            # Draw Outline (Cut Path with Tab)
            ax.add_patch(patches.PathPatch(cut_path_with_tab,
                                           facecolor='none',
                                           edgecolor='black',
                                           linewidth=0.5,
                                           transform=trans))
            
            # Optional: Draw dashed fold line (Original West edge)
            # Just plotting the xL_base vs y line
            path_fold = Path(np.column_stack((xL_base, y)), [Path.MOVETO] + [Path.LINETO]*(len(xL_base)-1))
            ax.add_patch(patches.PathPatch(path_fold,
                                           facecolor='none',
                                           edgecolor='gray',
                                           linestyle='--',
                                           linewidth=0.3,
                                           transform=trans))
            
            # Add Index Label
            ax.text(shift_x, shift_y + (y_min - 0.5), f"Gore {global_gore_idx+1}", 
                    ha='center', va='top', fontsize=8, transform=ax.transData)

        # Save Sheet
        outfile = f"{out_prefix}_bowl_sheet_{sheet_idx+1}.pdf"
        plt.savefig(outfile, dpi=300, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        print(f"Saved {outfile}")

if __name__ == "__main__":
    img_path = None
    diam = 12.0
    min_lat = -60.0
    total_gores = 12
    gores_per_sheet = 3
    
    # Filter out flags
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    
    if len(args) > 0:
        if args[0].lower() != "auto":
            img_path = args[0]
        
        if len(args) > 1:
            try:
                diam = float(args[1])
            except ValueError:
                pass 
                
        if len(args) > 2:
            try:
                min_lat = float(args[2])
            except ValueError:
                pass
                
        if len(args) > 3:
            try:
                total_gores = int(args[3])
            except ValueError:
                pass
                
        if len(args) > 4:
            try:
                gores_per_sheet = int(args[4])
            except ValueError:
                pass

    mirror_mode = "--mirror" in sys.argv
    
    if img_path is None:
        print("No image provided (or 'auto' selected). Using synthetic vector map.")
    
    create_sheets(img_path, diameter_in=diam, total_gores=total_gores, gores_per_sheet=gores_per_sheet, min_lat_deg=min_lat, mirror=mirror_mode)
