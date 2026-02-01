#!/bin/bash
# sync.sh - Incremental Sync for Orbigator
# Syncs only files in whitelist that have changed since last sync.

WHITELIST="sync_whitelist.txt"
LAST_SYNC=".last_sync"
SRC_BASE="micropython"

if [ ! -f "$WHITELIST" ]; then
    echo "❌ Error: $WHITELIST not found."
    exit 1
fi

# Detect first run
FIRST_RUN=0
if [ ! -f "$LAST_SYNC" ]; then
    echo "ℹ️  No previous sync detected. Syncing ALL listed files."
    FIRST_RUN=1
    # Create the file with a very old timestamp so everything looks newer
    touch -t 197001010000 "$LAST_SYNC"
fi

echo "🔍 Scanning for changes..."
COUNT=0
MODE="FILES"

while IFS= read -r line || [ -n "$line" ]; do
    # Trim
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    if [[ -z "$line" ]] || [[ "$line" == \#* ]]; then continue; fi
    if [[ "$line" == "[DIRS]" ]]; then MODE="DIRS"; continue; fi
    
    if [[ "$MODE" == "FILES" ]]; then
        SRC="$SRC_BASE/$line"
        if [ -f "$SRC" ]; then
            # Check if file is newer than last sync marker
            if [ "$SRC" -nt "$LAST_SYNC" ] || [ $FIRST_RUN -eq 1 ]; then
                echo "📤 Uploading $line..."
                mpremote fs cp "$SRC" ":$line"
                if [ $? -eq 0 ]; then ((COUNT++)); else echo "❌ Failed: $line"; fi
            fi
        fi
        
    elif [[ "$MODE" == "DIRS" ]]; then
        # Check files inside dir
        DIR_PATH="$SRC_BASE/$line"
        if [ -d "$DIR_PATH" ]; then
            # Find files in dir that are newer
            find "$DIR_PATH" -type f -newer "$LAST_SYNC" | while read -r filepath; do
                relpath="${filepath#$SRC_BASE/}"
                echo "   📄 $relpath"
                mpremote fs cp "$filepath" ":$relpath"
            done
        fi
    fi

done < "$WHITELIST"

if [ $COUNT -eq 0 ]; then
    echo "✅ No main file changes detected (or all failed)."
else
    echo "✅ Sync attempted for $COUNT items."
fi

# Update timestamp
touch "$LAST_SYNC"
echo "Run 'rm .last_sync' to force full retry."
