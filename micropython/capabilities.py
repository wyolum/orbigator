"""
Capability Layer for Orbigator
Responsible for hardware identification and feature gating.
"""

import json

# Global Override Constant
# Set to True to force Wi-Fi OFF (even on Pico 2 W).
# Set to False to use Wi-Fi if available.
DISABLE_WIFI = False

class Capabilities:
    def __init__(self, hw_type, has_wifi, has_web_server, has_ntp, has_sgp4, has_orbit_offline, has_rtc, has_cache, has_motors):
        self.hw_type = hw_type
        self.has_wifi = has_wifi
        self.has_web_server = has_web_server
        self.has_ntp = has_ntp
        self.has_sgp4 = has_sgp4
        self.has_orbit_offline = has_orbit_offline
        self.has_rtc = has_rtc
        self.has_cache = has_cache
        self.has_motors = has_motors

    def __repr__(self):
        return f"Capabilities(HW={self.hw_type}, WiFi={self.has_wifi}, Web={self.has_web_server})"

def get_capabilities(config_path="orbigator_config.json"):
    """
    Identifies hardware and returns a Capabilities object.
    Enforces deterministic behavior between Pico 2 and Pico 2 W.
    """
    global DISABLE_WIFI
    
    # 1. Detect hardware Wi-Fi presence
    hw_has_wifi = False
    try:
        import network
        # Attempt to instantiate WLAN to be sure (some builds might have 'network' but not WLAN)
        if hasattr(network, 'WLAN'):
            hw_has_wifi = True
    except ImportError:
        hw_has_wifi = False

    # 2. Apply DISABLE_WIFI override
    if DISABLE_WIFI:
        final_wifi = False
    else:
        final_wifi = hw_has_wifi

    # 3. Check config for additional overrides (only if not already improved)
    if final_wifi:
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                web_cfg = config.get("web", {})
                if not web_cfg.get("enable_web", True):
                    final_wifi = False
        except:
            pass
            
    # Final check: Invariant - If no physical wifi module, we can still override for testing
    # but the hw_type should still reflect the actual hardware presence for boot logs.
    hw_type = "HW_PICO2W" if hw_has_wifi else "HW_PICO2"
    
    # Derived capabilities
    return Capabilities(
        hw_type=hw_type,
        has_wifi=final_wifi,
        has_web_server=final_wifi, # Only on if wifi on
        has_ntp=final_wifi,        # Only on if wifi on
        has_sgp4=True,             # SGP4 can run offline if needed, though usually uses web
        has_orbit_offline=True,    # Always present
        has_rtc=True,              # Always present (DS3232)
        has_cache=True,            # Always present (SRAM/Flash)
        has_motors=True            # Always present
    )
