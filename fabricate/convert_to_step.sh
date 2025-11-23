#!/bin/bash
# Convert STL files to STEP format using FreeCAD
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
flatpak run --command=FreeCADCmd org.freecad.FreeCAD "$SCRIPT_DIR/stl_to_step.py"
