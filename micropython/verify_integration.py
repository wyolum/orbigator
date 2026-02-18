import sys

# Mock hardware dependencies if running on PC, but on Pico we can just import
try:
    import orbigator
    import orb_globals as g
    from absolute_motor import AbsoluteDynamixel
    
    print("\n--- Integration Verification ---")
    
    for name, motor_obj, expected_slot in [("EQX", g.eqx_motor, 0x80), ("AoV", g.aov_motor, 0x8A)]:
        print(f"\nChecking {name}...")
        if isinstance(motor_obj, AbsoluteDynamixel):
            print(f"PASS: g.{name.lower()}_motor is AbsoluteDynamixel")
        else:
            print(f"FAIL: g.{name.lower()}_motor is {type(motor_obj)}")
            
        print(f"{name} Name: {getattr(motor_obj, 'name', 'MISSING')}")
        print(f"{name} SRAM Address: 0x{motor_obj._sram_addr:X}")
        
        if motor_obj._sram_addr == expected_slot:
            print(f"PASS: SRAM Address is 0x{expected_slot:X}")
        else:
            print(f"FAIL: SRAM Address is 0x{motor_obj._sram_addr:X} (Expected 0x{expected_slot:X})")

        if hasattr(motor_obj, 'home'):
            print(f"PASS: {name} has 'home' method")
        else:
            print(f"FAIL: {name} missing 'home' method")

        if hasattr(motor_obj, 'offset_degrees'):
            print(f"PASS: {name} has 'offset_degrees' attribute")
        else:
            print(f"FAIL: {name} missing 'offset_degrees' attribute")

except ImportError:
    print("SKIP: Cannot run full verification without MicroPython environment (ImportError)")
except Exception as e:
    print(f"FAIL: Exception during verification: {e}")
