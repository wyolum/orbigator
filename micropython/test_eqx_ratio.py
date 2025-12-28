import time
from machine import Pin, I2C
from dynamixel_motor import DynamixelMotor
from dynamixel_extended_utils import set_extended_mode
import pins

# Constants
EQX_MOTOR_ID = 1
# Current guess: 120 / 14
GEAR_RATIO = 120.0 / 14.0
BUTTON_PIN = pins.ENC_BTN_PIN  # Use Encoder Switch

def main():
    print(f"EQX Ratio Test (Ratio: {GEAR_RATIO:.4f})")
    print(" initializing...")
    
    # Init Hardware
    i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400_000)
    btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
    
    # Motor Setup
    set_extended_mode(EQX_MOTOR_ID)
    motor = DynamixelMotor(EQX_MOTOR_ID, "EQX", gear_ratio=GEAR_RATIO)
    motor.set_speed_limit(20) # Reasonable speed for testing
    
    # Home first
    print("Homing...")
    motor.home()
    time.sleep(2)
    
    target_angle = 0.0
    
    print("Ready. Press Encoder Switch to advance 90 degrees.")
    
    last_btn = 1
    while True:
        current_btn = btn.value()
        
        # Debounced press detection (falling edge)
        if last_btn == 1 and current_btn == 0:
            time.sleep_ms(50) # Debounce
            if btn.value() == 0:
                target_angle += 90.0
                print(f"Commanding: {target_angle:.1f} deg")
                motor.set_angle_degrees(target_angle)
                
                # Wait for move to likely complete
                time.sleep(1)
                
                # Check actual
                motor.update_present_position(force=True)
                actual = motor.present_output_degrees
                print(f"  Actual: {actual:.2f} (Diff: {actual - target_angle:.2f})")
                
                # Wait for release
                while btn.value() == 0:
                    time.sleep_ms(10)
        
        last_btn = current_btn
        time.sleep_ms(10)

if __name__ == "__main__":
    main()
