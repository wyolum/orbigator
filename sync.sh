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
            if [ "$SRC" -nt "$LAST_SYNC" ] || [ $FIRST_RUN -eq 1 ]; then
                # Handle nested dirs
                if [[ "$line" == */* ]]; then
                    PARENT_DIR="${line%/*}"
                    mpremote fs ls ":$PARENT_DIR" >/dev/null 2>&1 || mpremote fs mkdir ":$PARENT_DIR" >/dev/null 2>&1
                fi
                echo "📤 $line"
                mpremote fs cp "$SRC" ":$line" && ((COUNT++))
            fi
        fi
        
    elif [[ "$MODE" == "DIRS" ]]; then
        DIR_PATH="$SRC_BASE/$line"
        if [ -d "$DIR_PATH" ]; then
            echo "📁 Processing directory :$line..."
            mpremote fs ls ":$line" >/dev/null 2>&1 || mpremote fs mkdir ":$line" >/dev/null 2>&1
            
            # Find and sync files inside DIR
            while read -r fpath; do
                if [ "$fpath" -nt "$LAST_SYNC" ] || [ $FIRST_RUN -eq 1 ]; then
                    relpath="${fpath#$SRC_BASE/}"
                    # Ensure nested dirs within this DIR entry
                    if [[ "$relpath" == */* ]]; then
                        D="${relpath%/*}"
                        mpremote fs ls ":$D" >/dev/null 2>&1 || mpremote fs mkdir ":$D" >/dev/null 2>&1
                    fi
                    echo "   📄 $relpath"
                    mpremote fs cp "$fpath" ":$relpath" && ((COUNT++))
                fi
            done < <(find "$DIR_PATH" -type f)
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
