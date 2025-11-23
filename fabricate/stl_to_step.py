#!/usr/bin/env python3
"""
FreeCAD script to convert STL files to STEP format.

Usage:
  flatpak run --command=FreeCADCmd org.freecad.FreeCAD /path/to/stl_to_step.py
"""

import os

# FreeCAD imports
import FreeCAD
import Mesh
import Part
import MeshPart

# Configuration
STL_DIR = os.path.dirname(os.path.abspath(__file__))
STLS_SUBDIR = os.path.join(STL_DIR, "stls")
STEP_DIR = os.path.join(STL_DIR, "step_files")

# STL files to skip
SKIP_LIST = [
    "pi-pico-2w-cad-reference.stl",
    "pepper_funnel.stl",
]

# Create output directory
os.makedirs(STEP_DIR, exist_ok=True)


def stl_to_step(stl_path, step_path):
    """Convert an STL file to STEP format."""
    print(f"Converting: {os.path.basename(stl_path)}")

    try:
        doc = FreeCAD.newDocument("Conversion")

        mesh = Mesh.read(stl_path)
        mesh_obj = doc.addObject("Mesh::Feature", "Mesh")
        mesh_obj.Mesh = mesh

        shape = Part.Shape()
        shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, 0.1)

        solid = Part.makeSolid(shape)
        solid.exportStep(step_path)

        FreeCAD.closeDocument("Conversion")

        print(f"  -> Created: {os.path.basename(step_path)}")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        try:
            FreeCAD.closeDocument("Conversion")
        except:
            pass
        return False


# Main
print("=" * 50)
print("STL to STEP Converter")
print("=" * 50)

stl_files = []

# Collect STL files from main directory
for f in os.listdir(STL_DIR):
    if f.lower().endswith('.stl') and f not in SKIP_LIST:
        stl_files.append(os.path.join(STL_DIR, f))

# Collect STL files from stls subdirectory
if os.path.isdir(STLS_SUBDIR):
    for f in os.listdir(STLS_SUBDIR):
        if f.lower().endswith('.stl') and f not in SKIP_LIST:
            stl_files.append(os.path.join(STLS_SUBDIR, f))

print(f"Found {len(stl_files)} STL files (skipping {SKIP_LIST})")
print(f"Output: {STEP_DIR}")
print("-" * 50)

success = 0
failed = 0

for stl_path in sorted(stl_files):
    basename = os.path.splitext(os.path.basename(stl_path))[0]
    step_path = os.path.join(STEP_DIR, f"{basename}.step")

    if stl_to_step(stl_path, step_path):
        success += 1
    else:
        failed += 1

print("-" * 50)
print(f"Done: {success} succeeded, {failed} failed")
