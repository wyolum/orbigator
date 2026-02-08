"""
Interactive Motor Motion Test
==============================
Use encoder to set target, confirm to move, track progress.
Shows position on OLED and in serial output.

Controls:
- Encoder: Adjust target position (+/- 10°)
- Confirm: Move motor to target
- Back: Switch between EQX/AoV motor
- Encoder button: Stop motor

Ctrl+C to exit.
"""

from machine import Pin, I2C
import time

# Initialize hardware
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

from oled_display import OledDisplay
from rotary_encoder import RotaryEncoder
from buttons import Buttons
from dynamixel_motor import DynamixelMotor

display = OledDisplay(i2c)
encoder = RotaryEncoder(6, 7, 8)
buttons = Buttons(9, 10)

print("Initializing motors...")
try:
    eqx_motor = DynamixelMotor(1, "EQX")
    aov_motor = DynamixelMotor(2, "AoV")
    motors = [eqx_motor, aov_motor]
    print("Motors ready!")
except Exception as e:
    print(f"Motor init failed: {e}")
    motors = []

# State
current_motor_idx = 0
target_degrees = 0.0
last_enc = encoder.value
moving = False
move_start_time = 0

def get_motor():
    return motors[current_motor_idx] if motors else None

def update_display():
    motor = get_motor()
    display.clear()
    
    if not motor:
        display.text("NO MOTORS", 20, 28)
        display.show()
        return
    
    # Header
    display.text(f"MOTOR: {motor.name}", 0, 0)
    display.text("-" * 16, 0, 10)
    
    # Current position
    motor.update_position()
    display.text(f"Pos: {motor.output_degrees:.1f}", 0, 22)
    
    # Target
    display.text(f"Tgt: {target_degrees:.1f}", 0, 34)
    
    # Delta
    delta = target_degrees - motor.output_degrees
    display.text(f"Delta: {delta:+.1f}", 0, 46)
    
    # Status
    if moving:
        display.text("[MOVING]", 64, 56)
    else:
        display.text("[OK] Move", 40, 56)
    
    display.show()

def check_arrival():
    global moving
    motor = get_motor()
    if not motor or not moving:
        return
    
    motor.update_position()
    delta = abs(motor.output_degrees - target_degrees)
    
    # Check if arrived (within 2 degrees)
    if delta < 2.0:
        elapsed = time.ticks_diff(time.ticks_ms(), move_start_time)
        print(f"✓ Arrived at {motor.output_degrees:.1f}° (target: {target_degrees:.1f}°, time: {elapsed}ms)")
        moving = False
    elif time.ticks_diff(time.ticks_ms(), move_start_time) > 10000:
        print(f"✗ Timeout! Current: {motor.output_degrees:.1f}°, Target: {target_degrees:.1f}°")
        moving = False

print("\nMotor Motion Test")
print("=" * 30)
print("Encoder: Adjust target (+/-10°)")
print("Confirm: Move motor")
print("Back: Switch motor")
print("Enc button: Stop")
print("Ctrl+C to exit")
print()

try:
    while True:
        motor = get_motor()
        
        # Encoder rotation - adjust target
        enc = encoder.value
        if enc != last_enc:
            delta = (enc - last_enc) * 10  # 10 degrees per detent
            target_degrees = (target_degrees + delta) % 360
            print(f"Target: {target_degrees:.1f}°")
            last_enc = enc
        
        # Encoder button - stop
        if encoder.button_pressed:
            if motor and moving:
                motor.update_position()
                motor.set_position(motor.output_degrees)  # Stop at current
                print(f"STOPPED at {motor.output_degrees:.1f}°")
                moving = False
            time.sleep_ms(200)  # Debounce
        
        # Back button - switch motor
        if buttons.back_pressed:
            current_motor_idx = (current_motor_idx + 1) % len(motors) if motors else 0
            motor = get_motor()
            if motor:
                target_degrees = motor.output_degrees
                print(f"Switched to {motor.name} (pos: {motor.output_degrees:.1f}°)")
            time.sleep_ms(200)
        
        # Confirm button - move to target
        if buttons.confirm_pressed:
            if motor and not moving:
                motor.set_speed(50)  # Medium speed
                motor.enable_torque()
                motor.set_position(target_degrees)
                move_start_time = time.ticks_ms()
                moving = True
                print(f"Moving {motor.name} to {target_degrees:.1f}°...")
            time.sleep_ms(200)
        
        # Check if motor arrived
        if moving:
            check_arrival()
        
        # Update display
        update_display()
        
        time.sleep_ms(50)

except KeyboardInterrupt:
    print("\nTest ended.")
    display.clear()
    display.text("Test ended", 20, 28)
    display.show()
