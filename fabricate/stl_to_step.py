#!/usr/bin/env python3
"""
FreeCAD script to convert STL files to STEP format.

Usage:
  FreeCADCmd stl_to_step.py --all                    # Convert all except skipped
  FreeCADCmd stl_to_step.py file1.stl file2.stl      # Convert specific files
  FreeCADCmd stl_to_step.py --list                   # List available STL files

For Flatpak:
  flatpak run --command=FreeCADCmd org.freecad.FreeCAD /path/to/stl_to_step.py --all
"""

import os
import sys
import argparse

# FreeCAD imports
import FreeCAD
import Mesh
import Part
import MeshPart

# Configuration
STL_DIR = os.path.dirname(os.path.abspath(__file__))
STLS_SUBDIR = os.path.join(STL_DIR, "stls")
STEP_DIR = os.path.join(STL_DIR, "step_files")

# STL files to skip when using --all
SKIP_LIST = [
    "sat_model_2.stl",
    "pi-pico-2w-cad-reference.stl",
]

# Create output directory
os.makedirs(STEP_DIR, exist_ok=True)


def get_all_stl_files():
    """Collect all STL files from known directories."""
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

    return sorted(stl_files)


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


def resolve_stl_path(filename):
    """Resolve an STL filename to its full path."""
    # If it's already an absolute path, use it
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename

    # Check in main directory
    path = os.path.join(STL_DIR, filename)
    if os.path.exists(path):
        return path

    # Check in stls subdirectory
    path = os.path.join(STLS_SUBDIR, filename)
    if os.path.exists(path):
        return path

    return None


def main(args):
    """Process STL files based on arguments."""
    all_stl_files = get_all_stl_files()

    if args.list:
        print("Available STL files:")
        print("-" * 50)
        for stl_path in all_stl_files:
            basename = os.path.basename(stl_path)
            skip_marker = " [SKIP]" if basename in SKIP_LIST else ""
            print(f"  {basename}{skip_marker}")
        print("-" * 50)
        print(f"Total: {len(all_stl_files)} files")
        print(f"Skip list: {SKIP_LIST}")
        return

    # Determine which files to convert
    if args.all:
        # Convert all except those in skip list
        stl_files = [
            f for f in all_stl_files
            if os.path.basename(f) not in SKIP_LIST
        ]
        print(f"Converting all STL files (excluding {len(SKIP_LIST)} in skip list)")
    elif args.files:
        # Convert specific files
        stl_files = []
        for filename in args.files:
            resolved = resolve_stl_path(filename)
            if resolved:
                stl_files.append(resolved)
            else:
                print(f"WARNING: Could not find STL file: {filename}")
    else:
        print("Error: Specify --all or provide specific STL files")
        print("Use --list to see available files")
        print("Use --help for usage information")
        return

    if not stl_files:
        print("No STL files to convert")
        return

    print(f"Converting {len(stl_files)} STL files")
    print(f"Output directory: {STEP_DIR}")
    print("-" * 50)

    success = 0
    failed = 0

    for stl_path in stl_files:
        basename = os.path.splitext(os.path.basename(stl_path))[0]
        step_path = os.path.join(STEP_DIR, f"{basename}.step")

        if stl_to_step(stl_path, step_path):
            success += 1
        else:
            failed += 1

    print("-" * 50)
    print(f"Conversion complete: {success} succeeded, {failed} failed")


# Run directly (FreeCAD doesn't always set __name__ correctly)
print("=" * 50)
print("STL to STEP Converter")
print("=" * 50)

# Parse command line arguments
# FreeCAD may pass the script path as first arg, so we filter it out
argv = [arg for arg in sys.argv if not arg.endswith('.py')]

parser = argparse.ArgumentParser(description='Convert STL files to STEP format')
parser.add_argument('--all', action='store_true',
                    help='Convert all STL files except those in skip list')
parser.add_argument('--list', action='store_true',
                    help='List available STL files')
parser.add_argument('files', nargs='*', metavar='FILE',
                    help='Specific STL files to convert')

args = parser.parse_args(argv)
main(args)
