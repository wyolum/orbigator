#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
import argparse

# Configuration
DEVICE = "/dev/ttyACM0"
SRC_DIR = "/home/justin/code/orbigator/micropython"
STATE_FILE = "/home/justin/code/orbigator/.pico_state.json"

WHITELIST_FILE = "/home/justin/code/orbigator/sync_whitelist.txt"

def load_whitelist():
    """Load CORE_FILES and CORE_DIRS from external whitelist file."""
    core_files = []
    core_dirs = []
    
    if not os.path.exists(WHITELIST_FILE):
        print(f"⚠️ Warning: Whitelist file {WHITELIST_FILE} not found. Using empty lists.")
        return core_files, core_dirs
        
    current_section = "FILES"
    with open(WHITELIST_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line == "[DIRS]":
                current_section = "DIRS"
                continue
            
            if current_section == "DIRS":
                core_dirs.append(line)
            else:
                core_files.append(line)
                
    return core_files, core_dirs

def get_pico_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pico_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def get_file_mtime(filepath):
    try:
        return os.path.getmtime(filepath)
    except OSError:
        return 0

def sync_file(rel_path):
    print(f"📤 Uploading {rel_path}...")
    try:
        # Use -r for directories if needed, but cp usually handles it if target is correct
        # Actually mpremote cp is usually file-based.
        subprocess.run(["mpremote", "fs", "cp", rel_path, f":{rel_path}"], cwd=SRC_DIR, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to upload {rel_path}: {e}")
        return False

def wipe_pico():
    print("🗑️  Wiping Pico root directory (cleaning up garbage)...")
    try:
        # List all files on Pico
        result = subprocess.run(["mpremote", "fs", "ls"], capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line or line.startswith('ls'): continue
            
            parts = line.split()
            if not parts: continue
            
            # File or Dir name is usually the last part
            name = parts[-1]
            
            # Skip lib/ and web/ if we want to keep them, or just wipe everything and re-sync
            # Let's wipe everything except dirs for now, or just rm -rf equivalent?
            # mpremote doesn't have rm -rf. We'll do it file by file.
            if name.endswith('/'):
                print(f"  Removing directory: {name}")
                # Note: mpremote cannot rm non-empty dirs easily.
                # In most cases for this project, the Pico is flat except for web/ and lib/.
                subprocess.run(["mpremote", "fs", "rm", "-r", name[:-1]], stderr=subprocess.DEVNULL)
            else:
                print(f"  Removing file: {name}")
                subprocess.run(["mpremote", "fs", "rm", name], stderr=subprocess.DEVNULL)
        print("Done.")
    except Exception as e:
        print(f"⚠️  Wipe partially failed (likely busy or read-only): {e}")

def main():
    parser = argparse.ArgumentParser(description="Incremental Sync to Pico 2W (Whitelist Mode)")
    parser.add_argument("--wipe", action="store_true", help="Wipe Pico root before syncing")
    args = parser.parse_args()

    if not os.path.exists(DEVICE):
        print(f"❌ Error: Pico 2 not found at {DEVICE}")
        sys.exit(1)

    if args.wipe:
        wipe_pico()
        # Reset state after wipe
        save_pico_state({})

    state = get_pico_state()
    files_to_sync = []
    
    core_files, core_dirs = load_whitelist()
    
    print(f"🔍 Scanning whitelist ({len(core_files)} files, {len(core_dirs)} dirs) for changes...")
    
    # 1. Check individual files
    for filename in core_files:
        filepath = os.path.join(SRC_DIR, filename)
        if os.path.exists(filepath):
            mtime = get_file_mtime(filepath)
            last_mtime = state.get(filename, 0)
            if mtime > last_mtime:
                files_to_sync.append(filename)
    
    # 2. Check directories
    for dname in core_dirs:
        dirpath = os.path.join(SRC_DIR, dname)
        if os.path.exists(dirpath):
            # Ensure the directory itself exists on Pico if mpremote needs it
            # (mpremote cp creates it usually)
            for root, dirs, files in os.walk(dirpath):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, SRC_DIR)
                    mtime = get_file_mtime(full_path)
                    last_mtime = state.get(rel_path, 0)
                    if mtime > last_mtime:
                        files_to_sync.append(rel_path)

    if not files_to_sync:
        print("✅ Pico is up to date (whitelisted files only).")
        return

    print(f"📦 Found {len(files_to_sync)} whitelisted changes.")
    
    success_count = 0
    for rel_path in files_to_sync:
        if sync_file(rel_path):
            state[rel_path] = get_file_mtime(os.path.join(SRC_DIR, rel_path))
            success_count += 1
    
    save_pico_state(state)
    
    if success_count > 0:
        print(f"✅ Sync complete! ({success_count} files updated)")
    else:
        print("⚠️ No files were successfully updated.")

if __name__ == "__main__":
    main()
