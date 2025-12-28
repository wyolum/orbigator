#!/bin/bash
# Deploy Orbigator Manual TLE Update
# Usage: ./deploy_manual_tle.sh

echo "⚠️  Closing any stalled mpremote processes..."
pkill -9 -f mpremote || true
sleep 1

DEVICE="/dev/ttyACM0"
echo "🔍 Checking for device at $DEVICE..."
if [ ! -e "$DEVICE" ]; then
    echo "❌ Device not found at $DEVICE. Please plug it in or check connection."
    exit 1
fi

echo "🚀 Starting Upload..."
set -e # Exit on error
set -x # Print commands

# 1. Globals & Core
mpremote connect $DEVICE fs cp micropython/orb_globals.py :
mpremote connect $DEVICE fs cp micropython/orb_utils.py :
mpremote connect $DEVICE fs cp micropython/propagators.py :
mpremote connect $DEVICE fs cp micropython/sgp4.py :
mpremote connect $DEVICE fs cp micropython/dynamixel_extended_utils.py :
mpremote connect $DEVICE fs cp micropython/dynamixel_motor.py :
mpremote connect $DEVICE fs cp micropython/pins.py :
mpremote connect $DEVICE fs cp micropython/input_utils.py :
mpremote connect $DEVICE fs cp micropython/satellite_catalog.py :
mpremote connect $DEVICE fs cp micropython/wifi_setup.py :
mpremote connect $DEVICE fs cp micropython/tle_fetch.py :
mpremote connect $DEVICE fs cp micropython/tle_parser.py :
mpremote connect $DEVICE fs cp micropython/orbigator.py :
mpremote connect $DEVICE fs cp micropython/modes.py :
mpremote connect $DEVICE fs cp micropython/web_server.py :

# 2. Web Assets
mpremote connect $DEVICE fs cp micropython/web/index.html :web/index.html
mpremote connect $DEVICE fs cp micropython/web/sgp4.html :web/sgp4.html
mpremote connect $DEVICE fs cp micropython/web/css/style.css :web/css/style.css
mpremote connect $DEVICE fs cp micropython/web/js/api.js :web/js/api.js
mpremote connect $DEVICE fs cp micropython/web/js/utils.js :web/js/utils.js
mpremote connect $DEVICE fs cp micropython/web/js/dashboard.js :web/js/dashboard.js
mpremote connect $DEVICE fs cp micropython/web/js/sgp4.js :web/js/sgp4.js

set +x
echo "✅ Upload Complete."
echo "🔄 Resetting Board..."
mpremote connect $DEVICE reset

echo "Done! You can now monitor with: mpremote repl"
