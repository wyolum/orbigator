#!/bin/bash
# Render all components in their assembly positions to stls_in_situ/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p stls_in_situ

PARTS=(
    "aov_arm"
    "aov_motor_mount"
    "sled"
    "ring_gear"
    "drive_gear"
    "base_with_1010_hole"
    "RingLock"
    "idler"
    "spring_arms"
    "pico"
)

echo "Rendering components to stls_in_situ/"
echo "======================================"

for part in "${PARTS[@]}"; do
    echo "Rendering: $part"
    openscad -o "stls_in_situ/${part}.stl" -D "RENDER_PART=\"${part}\"" render_in_situ.scad
done

echo "======================================"
echo "Done!"
ls -la stls_in_situ/
