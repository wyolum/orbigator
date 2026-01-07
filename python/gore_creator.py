#!/usr/bin/env python3
"""
gore_multipage_landscape.py

Generate a single landscape-oriented PDF showing 4 warped globe gores side-by-side
(4-gore template) for a 13" globe. North-up, equator centered, with balanced margins.

Dependencies:
    pip install numpy matplotlib Pillow
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
from matplotlib.transforms import Affine2D
from PIL import Image
import sys, os


def build_base_gore(diameter_in, num_gores, samples=300):
    # Build the gore outline for a spherical globe
    R = diameter_in / 2.0
    dlam = 2 * np.pi / num_gores
    phis = np.linspace(-np.pi/2, np.pi/2, samples)
    xL = -R * (dlam/2) * np.cos(phis)
    xR =  R * (dlam/2) * np.cos(phis)
    y  =  R * phis
    verts = np.vstack([
        np.column_stack((xL, y)),
        np.column_stack((xR[::-1], y[::-1])),
        [(0,0)]
    ])
    codes = ([Path.MOVETO] +
             [Path.LINETO] * (samples-1) +
             [Path.LINETO] +
             [Path.LINETO] * (samples-1) +
             [Path.CLOSEPOLY])
    return Path(verts, codes), xL.min(), y.min(), R * dlam


def warp_slice_to_gore(slice_img, diameter_in, num_gores):
    """
    Warp a rectangular slice image so its width at each row matches the spherical gore.
    """
    W, H = slice_img.size
    phis = np.linspace(np.pi/2, -np.pi/2, H)
    warped = Image.new("RGBA", (W, H), (0,0,0,0))
    for j, phi in enumerate(phis):
        row = slice_img.crop((0, j, W, j+1))
        scale = abs(np.cos(phi))
        new_w = max(1, int(round(W * scale)))
        row2 = row.resize((new_w, 1), Image.BICUBIC)
        warped.paste(row2, ((W-new_w)//2, j))
    return warped.convert(slice_img.mode)


def make_landscape(image_path,
                   diameter_in=13.0,
                   num_gores=4,
                   samples=4000,
                   margin_in=0.5):
    # Load the equirectangular map
    img = Image.open(image_path).convert("RGBA")
    W, H = img.size

    # Outline and dimensions
    gore_path, x_min, y_min, gore_w = build_base_gore(
        diameter_in, num_gores, samples)
    slice_w = W / num_gores

    # Page size: landscape 11" x 8.5"
    page_w, page_h = 11.0, 8.5
    fig = plt.figure(figsize=(page_w, page_h))
    ax  = fig.add_subplot(111)

    # Balanced margins: left = x_min - margin, right = x_min + gore_w*num_gores + margin
    left_edge  = x_min - margin_in
    right_edge = x_min + gore_w * num_gores + margin_in
    ax.set_xlim(left_edge, right_edge)
    # vertical limits: from min latitude to max latitude + margins
    ax.set_ylim(y_min - margin_in, -y_min + margin_in)

    ax.set_aspect('equal')
    ax.axis('off')

    # Draw each gore
    for i in range(num_gores):
        # Crop and warp slice
        left_px  = int(i * slice_w)
        right_px = int((i + 1) * slice_w)
        slice_img = img.crop((left_px, 0, right_px, H))
        warped = warp_slice_to_gore(slice_img, diameter_in, num_gores)

        # Position transform
        tx = i * gore_w
        trans = Affine2D().translate(tx, 0) + ax.transData

        # Render warped map slice
        ax.imshow(warped,
                  extent=[x_min, x_min + gore_w, y_min, -y_min],
                  origin='upper',
                  transform=trans,
                  clip_path=patches.PathPatch(gore_path, transform=trans),
                  clip_on=True)
        # Outline
        ax.add_patch(patches.PathPatch(gore_path,
                                      facecolor='none',
                                      edgecolor='k',
                                       lw=.1,alpha=.1,
                                      transform=trans))

    # Save PDF
    base = os.path.splitext(os.path.basename(image_path))[0]
    out_pdf = f"{base}_4gore_landscape_fixed.pdf"
    plt.savefig(out_pdf, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    print(f"Saved landscape 4-gore PDF: {out_pdf}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python gore_multipage_landscape.py <map.png>")
    else:
        make_landscape(sys.argv[1], num_gores=12)
