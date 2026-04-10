from machine import Pin
import time
import pins

print("\n--- 74HC126 Buffer & Bus Diagnostic ---")

# Setup pins as raw GPIO to test the buffer manually
tx_pin = Pin(pins.DYNAMIXEL_TX_PIN, Pin.OUT, value=1)
rx_pin = Pin(pins.DYNAMIXEL_RX_PIN, Pin.IN, Pin.PULL_DOWN)  # PULL_DOWN so if floating, reads 0
dir_pin = Pin(pins.DYNAMIXEL_DIR_PIN, Pin.OUT, value=0)

time.sleep_ms(10)

# TEST 1: DIR = 0 (Buffer Disabled)
# The bus should be pulled HIGH by the 10k hardware pull-up resistor (R1).
dir_pin.value(0)
time.sleep_ms(10)
val1 = rx_pin.value()
print(f"Test 1 - Buffer DISABLED (DIR=0): RX reads {val1} (Expected: 1 from 10k pull-up)")

# TEST 2: DIR = 1, TX = 0
# The buffer is enabled and should drive the bus LOW, overcoming the 10k pullup.
tx_pin.value(0)
dir_pin.value(1)
time.sleep_ms(10)
val2 = rx_pin.value()
print(f"Test 2 - Buffer ENABLED (DIR=1), TX=0: RX reads {val2} (Expected: 0)")

# TEST 3: DIR = 1, TX = 1
# The buffer is enabled and should drive the bus HIGH.
tx_pin.value(1)
dir_pin.value(1)
time.sleep_ms(10)
val3 = rx_pin.value()
print(f"Test 3 - Buffer ENABLED (DIR=1), TX=1: RX reads {val3} (Expected: 1)")

# Analysis
print("\n--- Result Analysis ---")
if val1 == 1 and val2 == 0 and val3 == 1:
    print("✅ Buffer and Bus appear perfectly functional from the Pico's perspective.")
    print("If it still fails, the issue is external (Motor power missing, bad motor cable, or wrong baud/ID).")
else:
    print("❌ Buffer or Bus is FAILING.")
    if val1 == 0:
        print("  -> ERROR: The bus is NOT being pulled HIGH when idle.")
        print("     Check if R1 (10k pull-up to 5V) is missing, or if motors are pulling it low.")
    if val2 == 1:
        print("  -> ERROR: The buffer cannot pull the bus LOW.")
        print("     Possible reasons: 74HC126 is backwards, dead, or R1 is way too strong (10 ohm instead of 10k).")
    if val3 == 0:
        print("  -> ERROR: The buffer cannot drive the bus HIGH.")
