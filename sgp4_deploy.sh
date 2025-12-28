#!/bin/bash
# Quick SGP4 Integration Upload and Test
# Run this to deploy SGP4 integration to Pico 2W

echo "=========================================="
echo "SGP4 Integration - Upload to Pico 2W"
echo "=========================================="

# Files to upload (in addition to existing files)
NEW_FILES=(
    "micropython/satellite_catalog.py"
    "micropython/tle_cache.json"
)

MODIFIED_FILES=(
    "micropython/modes.py"
    "micropython/orb_utils.py"
)

echo ""
echo "New files to upload:"
for file in "${NEW_FILES[@]}"; do
    echo "  ✓ $file"
done

echo ""
echo "Modified files to upload:"
for file in "${MODIFIED_FILES[@]}"; do
    echo "  ✓ $file"
done

echo ""
echo "Use your existing upload_to_pico.sh script:"
echo "  ./upload_to_pico.sh"
echo ""
echo "After upload, test the integration:"
echo "  1. Navigate: Menu → Track Satellite"
echo "  2. Rotate encoder to select satellite"
echo "  3. Press encoder to start tracking"
echo "  4. Verify motors move to satellite position"
echo ""
echo "=========================================="
