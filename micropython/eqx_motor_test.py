"""
EQX Motor Continuous Forward Test
Tests slow forward rotation for many revolutions to verify gear engagement
Motor ID: 1 (EQX - Equatorial axis)
"""

from machine import Pin, UART, I2C
import time
import framebuf

# Motor configuration
MOTOR_ID = 1  # EQX motor
UART_TX_PIN = 0
UART_RX_PIN = 1
DIR_PIN = 2
MOTOR_BAUDRATE = 57600
VELOCITY = 1

# Initialize UART and direction control
uart = UART(0, baudrate=MOTOR_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
dir_pin = Pin(DIR_PIN, Pin.OUT)

# Initialize I2C and OLED
try:
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
    
    # SH1106 OLED driver
    class SH1106_I2C:
        def __init__(self, w, h, i2c, addr=0x3C):
            self.width, self.height, self.i2c, self.addr = w, h, i2c, addr
            self.buffer = bytearray(w * h // 8)
            self.fb = framebuf.FrameBuffer(self.buffer, w, h, framebuf.MONO_VLSB)
            def cmd(*cs):
                for c in cs: self.i2c.writeto(self.addr, b'\x00' + bytes([c]))
            cmd(0xAE, 0x20, 0x00, 0x40, 0xA1, 0xC8, 0x81, 0x7F, 0xA6, 0xA8, 0x3F,
                0xAD, 0x8B, 0xD3, 0x00, 0xD5, 0x80, 0xD9, 0x22, 0xDA, 0x12, 0xDB, 0x35, 0xAF)
            self.fill(0)
            self.show()
        def fill(self, c): self.fb.fill(c)
        def text(self, s, x, y, c=1): self.fb.text(s, x, y, c)
        def show(self):
            for p in range(self.height // 8):
                self.i2c.writeto(self.addr, b'\x00' + bytes([0xB0 + p, 0x02, 0x10]))
                s = self.width * p; e = s + self.width
                self.i2c.writeto(self.addr, b'\x40' + self.buffer[s:e])
    
    display = SH1106_I2C(128, 64, i2c, addr=0x3C)
    HAS_DISPLAY = True
    print("✓ OLED display initialized")
except:
    display = None
    HAS_DISPLAY = False
    print("⚠ OLED not found - console only")

# Import motor library and set up globals
from dynamixel_motor import DynamixelMotor
import dynamixel_extended_utils as dxl_utils

# Set up global UART for dynamixel functions
dxl_utils.uart = uart
dxl_utils.dir_pin = dir_pin

print("=" * 60)
print("EQX Motor Continuous Forward Test")
print("=" * 60)
print(f"Motor ID: {MOTOR_ID}")
print(f"Testing slow forward rotation for gear engagement")
print()

# Initialize motor (EQX with 120/11 gear ratio)
print("Initializing motor...")
motor = DynamixelMotor(MOTOR_ID, "EQX", gear_ratio=120/11)

# Set slow speed for testing gear engagement
print("Setting max speed to 10...")
motor.set_speed_limit(velocity=VELOCITY)  # Match Orbigator's max running speed

# Read current position
current_pos = motor.get_angle_degrees()
if current_pos is None:
    print("Failed to read current position")
    raise RuntimeError("Motor communication failed")

print(f"Current position: {current_pos}°")
print()

# Test parameters
DEGREES_PER_REV = 360
NUM_REVS = 10  # Number of revolutions to test
SPEED = 10  # Max speed for testing (degrees/second)

print("=" * 60)
print("Test Parameters:")
print(f"  Revolutions: {NUM_REVS}")
print(f"  Speed: {SPEED}°/s")
print(f"  Total rotation: {NUM_REVS * DEGREES_PER_REV}°")
print(f"  Estimated time: {(NUM_REVS * DEGREES_PER_REV) / SPEED:.1f} seconds")
print("=" * 60)
print()
print("Press Ctrl+C to stop test")
print()

try:
    for rev in range(1, NUM_REVS + 1):
        # 10 Earth (output) rotations = 10 * 360° output = ~109 motor rotations
        target_pos = current_pos + (rev * DEGREES_PER_REV)
        
        print(f"Earth Revolution {rev}/{NUM_REVS}: Moving to {target_pos:.1f}° output...")
        
        # Update display
        if HAS_DISPLAY:
            display.fill(0)
            display.text("EQX Motor Test", 0, 0)
            display.text(f"Rev {rev}/{NUM_REVS}", 0, 16)
            display.text(f"Target: {target_pos:.0f}", 0, 32)
            display.show()
        
        # Set goal position
        if not motor.set_angle_degrees(target_pos):
            print(f"Failed to set goal position for rev {rev}")
            break
        
        # Monitor movement
        start_time = time.time()
        last_pos = current_pos
        last_update = time.time()
        
        while True:
            pos = motor.get_angle_degrees()
            if pos is None:
                print("Lost communication with motor!")
                break
            
            # Check if reached target (within 5 degrees)
            if abs(pos - target_pos) < 5:
                elapsed = time.time() - start_time
                print(f"  ✓ Completed in {elapsed:.1f}s - Position: {pos}°")
                break
            
            # Progress update every 2 seconds
            if time.time() - last_update > 2 and abs(pos - last_pos) > 10:
                progress_pct = (pos - current_pos) / (NUM_REVS * DEGREES_PER_REV) * 100
                print(f"  Progress: {pos}° ({progress_pct:.1f}%)")
                
                # Update display
                if HAS_DISPLAY:
                    display.fill(0)
                    display.text("EQX Motor Test", 0, 0)
                    display.text(f"Rev {rev}/{NUM_REVS}", 0, 16)
                    display.text(f"Pos: {pos:.0f}", 0, 32)
                    display.text(f"{progress_pct:.0f}% complete", 0, 48)
                    display.show()
                
                last_pos = pos
                last_update = time.time()
            
            time.sleep(0.1)
        
        time.sleep(0.5)  # Brief pause between revolutions
    
    print()
    print("=" * 60)
    print("Test Complete!")
    final_pos = motor.get_position()
    print(f"Final position: {final_pos}°")
    print("=" * 60)
    
    # Final display
    if HAS_DISPLAY:
        display.fill(0)
        display.text("Test Complete!", 8, 0)
        display.text(f"{NUM_REVS} revs done", 8, 24)
        display.text(f"Pos: {final_pos:.0f}", 8, 40)
        display.show()

except KeyboardInterrupt:
    print()
    print("=" * 60)
    print("Test stopped by user")
    final_pos = motor.get_position()
    if final_pos is not None:
        print(f"Final position: {final_pos}°")
        print(f"Total rotation: {final_pos - current_pos}°")
        
        # Display stopped message
        if HAS_DISPLAY:
            display.fill(0)
            display.text("Test Stopped", 16, 16)
            display.text(f"Pos: {final_pos:.0f}", 16, 32)
            display.show()
    print("=" * 60)

except Exception as e:
    print()
    print("=" * 60)
    print(f"Error: {e}")
    import sys
    sys.print_exception(e)
    print("=" * 60)
