"""
EQX Motor Constant Speed Test
Minimal program to run EQX motor at constant velocity
No display, RTC, or other dependencies required
"""

import time
from machine import Pin, UART
from dynamixel_motor import DynamixelMotor
from dynamixel_extended_utils import set_extended_mode

# UART Configuration (from pins.py)
UART_ID = 0
TX_PIN = 0
RX_PIN = 1
DIR_PIN = 2

# Motor Configuration
EQX_MOTOR_ID = 1
EQX_GEAR_RATIO = 120.0 / 14.0  # gear_ratio_num / gear_ratio_den

# Speed Settings
SPEED_LIMIT = 1  # RPM (motor shaft speed)
# For reference: 10 RPM = ~1.16 deg/sec at motor = ~10 deg/sec at output with gear ratio

print("EQX Motor Constant Speed Test")
print("=" * 40)

# Initialize Direction Control Pin
dir_pin = Pin(DIR_PIN, Pin.OUT)
dir_pin.value(1)  # TX mode
time.sleep_ms(10)

# Initialize Motor
print(f"Initializing EQX motor (ID {EQX_MOTOR_ID})...")

# Set to extended position mode for unlimited rotation
set_extended_mode(EQX_MOTOR_ID)
time.sleep_ms(100)

# Create motor instance
eqx_motor = DynamixelMotor(
    motor_id=EQX_MOTOR_ID,
    name="EQX",
    gear_ratio=EQX_GEAR_RATIO,
    offset_degrees=0.0
)

# Configure motor
print("Configuring motor parameters...")
eqx_motor.set_pid_gains(p=600, i=0, d=0)
eqx_motor.set_speed_limit(SPEED_LIMIT)
eqx_motor.enable_torque()

print(f"Motor configured: Speed Limit = {SPEED_LIMIT} RPM")

# Set motor to rotate continuously
# In extended position mode, we command a very large target position
# The motor will keep moving towards it at the configured speed
print("\nStarting continuous rotation...")
print("Motor will rotate clockwise at constant speed.")
print(f"Speed: ~{SPEED_LIMIT} RPM (motor shaft)")
print("Press Ctrl+C to stop.\n")

# Command motor to rotate 1000 turns (360,000 degrees)
# This effectively runs forever at the set speed limit
LARGE_TARGET = 360000.0  # 1000 full rotations
print(f"Commanding motor to position {LARGE_TARGET:.0f}° (will run continuously)")
eqx_motor.set_nearest_degrees(LARGE_TARGET % 360, direction_override=1)

print("Motor is now running. Monitoring position...\n")

# Monitor loop - just read and display position every second
try:
    start_time = time.time()
    
    while True:
        time.sleep(1)
        
        # Read and display current position
        angle = eqx_motor.get_angle_degrees()
        if angle is not None:
            elapsed = time.time() - start_time
            print(f"[{elapsed:6.0f}s] Position: {angle:8.2f}°")
        
except KeyboardInterrupt:
    print("\n\nStopping motor...")
    eqx_motor.stop()
    eqx_motor.disable_torque()
    print("Motor stopped. Test complete.")
