#!/bin/bash
# Upload Orbigator code to Pico 2
# Usage: ./upload_to_pico.sh

set -e

DEVICE="/dev/ttyACM0"
SRC_DIR="/home/justin/code/orbigator/micropython"

echo "🚀 Uploading Orbigator code to Pico 2..."

# Check if device exists
if [ ! -e "$DEVICE" ]; then
    echo "❌ Error: Pico 2 not found at $DEVICE"
    echo "   Please check USB connection"
    exit 1
fi

# Check if mpremote is installed
if ! command -v mpremote &> /dev/null; then
    echo "📦 Installing mpremote..."
    pip install --user mpremote
fi

cd "$SRC_DIR"

echo "📤 Uploading core files..."
mpremote fs cp orbigator.py :
mpremote fs cp modes.py :
mpremote fs cp orb_globals.py :
mpremote fs cp pins.py :
mpremote fs cp orb_utils.py :
mpremote fs cp dynamixel_motor.py :
mpremote fs cp dynamixel_extended_utils.py :
mpremote fs cp ds3231.py :
mpremote fs cp ss1306.py :

echo "✅ Upload complete!"
echo ""
echo "📋 Files on Pico:"
mpremote fs ls

echo ""
echo "🔌 To connect to REPL:"
echo "   mpremote repl"
echo ""
echo "🔄 To soft reboot:"
echo "   Press Ctrl+D in REPL"
