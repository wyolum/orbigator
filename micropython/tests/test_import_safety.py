"""
Import Safety Test
Checks that no networking modules are imported when Wi-Fi is disabled.
"""
import sys
import capabilities

def check_no_network_imports():
    print("Checking import safety for Pico 2 (Offline)...")
    
    # Force offline mode
    capabilities.OVERRIDE_WIFI = False
    
    # Restricted modules
    bad_modules = ['network', 'socket', 'urequests', 'ntptime', 'web_server', 'wifi_setup', 'networking', 'ntp_sync']
    
    # Clean check
    loaded = [m for m in bad_modules if m in sys.modules]
    if loaded:
        print(f"  WARNING: Modules already loaded: {loaded}")
    
    # Now import modes - this should be SAFE
    print("  Importing 'modes'...")
    import modes
    
    # Check again
    newly_loaded = [m for m in bad_modules if m in sys.modules]
    # Filter only those that weren't loaded at start
    actually_leaked = [m for m in newly_loaded if m not in loaded]
    
    if actually_leaked:
        print(f"  ✗ FAILED: Restricted modules were leaked: {actually_leaked}")
        return False
    else:
        print("  ✓ SUCCESS: No restricted modules loaded after importing 'modes'.")
        return True

if __name__ == "__main__":
    if check_no_network_imports():
        print("\nAll safety tests passed!")
    else:
        sys.exit(1)
