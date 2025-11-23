#!/usr/bin/env python3
"""
FreeCAD script to convert STL files to STEP format.

Usage:
  freecadcmd stl_to_step.py

  Or on some systems:
  freecad -c stl_to_step.py
  FreeCAD --console stl_to_step.py
"""

import os
import sys

# FreeCAD imports
import FreeCAD
import Mesh
import Part
import MeshPart

# Configuration
STL_DIR = os.path.dirname(os.path.abspath(__file__))
STLS_SUBDIR = os.path.join(STL_DIR, "stls")
STEP_DIR = os.path.join(STL_DIR, "step_files")

# Create output directory
os.makedirs(STEP_DIR, exist_ok=True)

def stl_to_step(stl_path, step_path):
    """Convert an STL file to STEP format."""
    print(f"Converting: {os.path.basename(stl_path)}")

    try:
        # Create a new document
        doc = FreeCAD.newDocument("Conversion")

        # Import the STL mesh
        mesh = Mesh.read(stl_path)
        mesh_obj = doc.addObject("Mesh::Feature", "Mesh")
        mesh_obj.Mesh = mesh

        # Convert mesh to shape
        # Using the shape from mesh with tolerance
        shape = Part.Shape()
        shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, 0.1)

        # Create a solid from the shape
        solid = Part.makeSolid(shape)

        # Export to STEP
        solid.exportStep(step_path)

        # Close document
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

def main():
    """Process all STL files."""
    # Collect all STL files
    stl_files = []

    # Check main fabricate directory
    for f in os.listdir(STL_DIR):
        if f.lower().endswith('.stl'):
            stl_files.append(os.path.join(STL_DIR, f))

    # Check stls subdirectory
    if os.path.isdir(STLS_SUBDIR):
        for f in os.listdir(STLS_SUBDIR):
            if f.lower().endswith('.stl'):
                stl_files.append(os.path.join(STLS_SUBDIR, f))

    print(f"Found {len(stl_files)} STL files to convert")
    print(f"Output directory: {STEP_DIR}")
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
    print(f"Conversion complete: {success} succeeded, {failed} failed")

if __name__ == "__main__":
    main()
