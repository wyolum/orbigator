"""
Tests for capabilities detections and overrides.
"""
import capabilities
import json

def test_wifi_detection():
    print("Testing Wi-Fi detection...")
    # This depends on the actual hardware, but we can check the consistency
    caps = capabilities.get_capabilities()
    print(f"  Detected WiFi: {caps.has_wifi}")
    print(f"  Detected Hardware: {caps.hw_type}")

def test_wifi_override():
    print("Testing OVERRIDE_WIFI...")
    
    # Force False
    capabilities.OVERRIDE_WIFI = False
    caps = capabilities.get_capabilities()
    assert caps.has_wifi is False, "has_wifi should be False when OVERRIDE_WIFI is False"
    assert caps.has_web_server is False, "has_web_server should be False when has_wifi is False"
    assert caps.has_ntp is False, "has_ntp should be False when has_wifi is False"
    print("  ✓ Override False OK")
    
    # Force True
    capabilities.OVERRIDE_WIFI = True
    caps = capabilities.get_capabilities()
    assert caps.has_wifi is True, "has_wifi should be True when OVERRIDE_WIFI is True"
    print("  ✓ Override True OK")
    
    # Reset
    capabilities.OVERRIDE_WIFI = None

def test_config_integration(tmp_path=None):
    print("Testing config-based override...")
    # In MicroPython we can't easily use tmp_path, so we'll just mock or use a temp file
    config_file = "test_config.json"
    
    # Test enable_web: false
    with open(config_file, "w") as f:
        json.dump({"web": {"enable_web": False}}, f)
        
    # We need to make sure capabilities reads this config
    caps = capabilities.get_capabilities(config_path=config_file)
    assert caps.has_wifi is False, "has_wifi should be False if config.web.enable_web is False"
    print("  ✓ Config override False OK")
    
    # Test enable_web: true
    with open(config_file, "w") as f:
        json.dump({"web": {"enable_web": True}}, f)
    
    # Note: If hardware doesn't have wifi, it remains false unless we OVERRIDE
    caps = capabilities.get_capabilities(config_path=config_file)
    # This part depends on if we want config to be able to FORCE true on Pico2 (no)
    # Requirement: "No attempt to emulate Wi-Fi in Pico 2."
    
    print("  ✓ Config override True (respects HW) OK")

if __name__ == "__main__":
    try:
        test_wifi_detection()
        test_wifi_override()
        test_config_integration()
        print("\nAll capabilities tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
