#!/bin/bash
# Render all render_*.scad files to stls_in_situ/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p stls_in_situ

echo "Rendering all components to stls_in_situ/"
echo "=========================================="

for scad_file in render_*.scad; do
    # Extract name: render_foo.scad -> foo
    name=$(basename "$scad_file" .scad | sed 's/^render_//')
    output="stls_in_situ/${name}.stl"

    echo "Rendering: $scad_file -> $output"
    openscad -o "$output" "$scad_file"
done

echo "=========================================="
echo "Done!"
ls -la stls_in_situ/
