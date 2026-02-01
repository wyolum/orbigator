#!/bin/bash
export STL_IN="/home/justin/code/orbigator/fabricate/stls/base_with_1010_display.stl"
export STEP_OUT="/home/justin/code/orbigator/fabricate/step_files/base_with_1010_display.step"

echo "Using Flatpak FreeCAD to convert..."
flatpak run --command=FreeCADCmd org.freecad.FreeCAD /home/justin/code/orbigator/fabricate/convert_single_stl.py
