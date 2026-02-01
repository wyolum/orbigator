import machine
import time
from machine import Pin

print("--- ORBIGATOR PIN DOCTOR (FULL BOARD) ---")
print("Diagnosing ALL assigned pins for shorts/faults...")

# Classification of pins
# (Pin Number, Name, Is_Input_Normally)
PINS = [
    # UART
    (0, "GP0 (UART TX)", False),
    (1, "GP1 (UART RX)", True),  # Connected to Buffer Output (Driven by buffer or Pull-up)
    (2, "GP2 (DIR)", False),
    
    # I2C
    (4, "GP4 (SDA)", False), # Bidirectional
    (5, "GP5 (SCL)", False), # Bidirectional
    
    # Encoder (Connected to switches -> GND or VCC depending on wiring)
    # usually switches short to GND.
    (6, "GP6 (ENC A)", True),
    (7, "GP7 (ENC B)", True),
    (8, "GP8 (ENC SW)", True),
    
    # Buttons
    (9,  "GP9 (BACK)", True),
    (10, "GP10 (CONFIRM)", True),
]

def test_drive(pin_num, name):
    print(f"\n[OUTPUT TEST] GP{pin_num} ({name})")
    try:
        p = Pin(pin_num, Pin.OUT)
        
        # Drive HIGH
        p.value(1); time.sleep(0.01)
        if p.value() == 1: print("  High: OK")
        else: print("  High: FAIL (Stuck Low?)")
            
        # Drive LOW
        p.value(0); time.sleep(0.01)
        if p.value() == 0: print("  Low:  OK")
        else: print("  Low:  FAIL (Stuck High?)")
        
        # Clean up (Input)
        Pin(pin_num, Pin.IN)
    except Exception as e:
        print(f"  Error: {e}")

def test_pulls(pin_num, name):
    print(f"\n[INPUT TEST]  GP{pin_num} ({name})")
    try:
        # Test Internal Pull-Down
        p = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
        time.sleep(0.01)
        pd_val = p.value()
        
        # Test Internal Pull-Up
        p = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        time.sleep(0.01)
        pu_val = p.value()
        
        print(f"  Pull-Down Read: {pd_val}")
        print(f"  Pull-Up   Read: {pu_val}")
        
        if pd_val == 0 and pu_val == 1:
            print("  Result: HEALTHY (Pin responds to pulls)")
        elif pd_val == 0 and pu_val == 0:
            print("  Result: STUCK LOW (Short to GND or Button Pressed)")
        elif pd_val == 1 and pu_val == 1:
            print("  Result: STUCK HIGH (Short to 3V3 or External Pull-up stronger than internal Pull-down)")
        else:
            print("  Result: INDETERMINATE")
            
    except Exception as e:
        print(f"  Error: {e}")

print("\n--- STARTING DIAGNOSTIC ---")
for pin_num, name, is_input in PINS:
    if is_input:
        test_pulls(pin_num, name)
    else:
        test_drive(pin_num, name)

print("\n--- DONE ---")
