"""
Interactive Dynamixel Motor Test
Allows motor selection, speed adjustment (via encoder), and real-time angle display.
Used for tracking down mechanical alignment issues.

Motor IDs:
- 1: EQX (Equatorial axis, 120/11 ratio)
- 2: AoV (Angle of View axis, 1:1 ratio)
"""

from machine import Pin, UART, I2C
import time
import framebuf
from dynamixel_motor import DynamixelMotor
import dynamixel_extended_utils as dxl_utils

# --- Pin Definitions (Matching pins.py) ---
UART_TX_PIN = 0
UART_RX_PIN = 1
DIR_PIN = 2
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
ENC_A_PIN = 6
ENC_B_PIN = 7
ENC_BTN_PIN = 8

# --- Configuration ---
MOTOR_BAUDRATE = 57600
OLED_W, OLED_H = 128, 64

# --- Hardware Initialization ---
uart = UART(0, baudrate=MOTOR_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
dir_pin = Pin(DIR_PIN, Pin.OUT)
dxl_utils.uart = uart
dxl_utils.dir_pin = dir_pin

# OLED Setup
try:
    i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=400000)
    
    class SH1106_I2C:
        def __init__(self, w, h, i2c, addr=0x3C):
            self.width, self.height, self.i2c, self.addr = w, h, i2c, addr
            self.buffer = bytearray(w * h // 8)
            self.fb = framebuf.FrameBuffer(self.buffer, w, h, framebuf.MONO_VLSB)
            def cmd(*cs):
                for c in cs: self.i2c.writeto(self.addr, b'\x00' + bytes([c]))
            cmd(0xAE, 0x20, 0x00, 0x40, 0xA1, 0xC8, 0x81, 0x7F, 0xA6, 0xA8, 0x3F,
                0xAD, 0x8B, 0xD3, 0x00, 0xD5, 0x80, 0xD9, 0x22, 0xDA, 0x12, 0xDB, 0x35, 0xAF)
            self.fill(0); self.show()
        def fill(self, c): self.fb.fill(c)
        def text(self, s, x, y, c=1): self.fb.text(s, x, y, c)
        def show(self):
            for p in range(self.height // 8):
                self.i2c.writeto(self.addr, b'\x00' + bytes([0xB0 + p, 0x02, 0x10]))
                s = self.width * p; e = s + self.width
                self.i2c.writeto(self.addr, b'\x40' + self.buffer[s:e])
    
    display = SH1106_I2C(OLED_W, OLED_H, i2c)
    HAS_DISPLAY = True
except:
    display = None
    HAS_DISPLAY = False
    print("⚠ OLED not found")

# Encoder Setup
enc_a = Pin(ENC_A_PIN, Pin.IN, Pin.PULL_UP)
enc_b = Pin(ENC_B_PIN, Pin.IN, Pin.PULL_UP)
enc_btn = Pin(ENC_BTN_PIN, Pin.IN, Pin.PULL_UP)

enc_state = (enc_a.value() << 1) | enc_b.value()
encoder_delta = 0

def enc_isr(p):
    global enc_state, encoder_delta
    new_state = (enc_a.value() << 1) | enc_b.value()
    if new_state != enc_state:
        # 4-state transition table
        # 00 -> 01 -> 11 -> 10 -> 00 (CW)
        # 00 -> 10 -> 11 -> 01 -> 00 (CCW)
        if (enc_state == 0b00 and new_state == 0b01) or \
           (enc_state == 0b01 and new_state == 0b11) or \
           (enc_state == 0b11 and new_state == 0b10) or \
           (enc_state == 0b10 and new_state == 0b00):
            encoder_delta -= 1  # Inverted
        else:
            encoder_delta += 1  # Inverted
        enc_state = new_state

enc_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=enc_isr)
enc_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=enc_isr)

# --- Motor Management ---
motors = {
    1: {"name": "EQX", "ratio": 120/14, "obj": None}, # Updated ratio to 14-tooth pinion
    2: {"name": "AoV", "ratio": 1.0, "obj": None}
}
current_motor_id = 1
target_velocity = 10  # 1 to 100 (0 would be "unlimited" on motor, so we avoid it)
is_moving = False
last_target_pos = 0

def get_motor():
    m = motors[current_motor_id]
    if m["obj"] is None:
        try:
            print(f"Connecting to motor {current_motor_id} ({m['name']})...")
            m["obj"] = DynamixelMotor(current_motor_id, m["name"], gear_ratio=m["ratio"])
            # Ensure velocity is set to something safe initially
            m["obj"].set_speed_limit(target_velocity)
        except Exception as e:
            print(f"Error connecting to motor {current_motor_id}: {e}")
            return None
    return m["obj"]

def update_ui(msg=""):
    if not HAS_DISPLAY: return
    display.fill(0)
    m_info = motors[current_motor_id]
    display.text(f"MOTOR: {current_motor_id} ({m_info['name']})", 0, 0)
    
    motor = m_info["obj"]
    if motor:
        pos = motor.present_output_degrees
        # Wrap to [-180, 180]
        wrapped_pos = (pos + 180) % 360 - 180
        display.text(f"POS: {wrapped_pos:8.2f} deg", 0, 16)
        display.text(f"VEL: {target_velocity:d}", 0, 32)
        if is_moving:
            display.text("MOVING...", 0, 48)
        else:
            display.text("IDLE (Btn to Jog)", 0, 48)
    else:
        display.text("DISCONNECTED", 0, 16)
    
    if msg:
        display.text(msg, 0, 56)
    display.show()

# --- Main Logic ---
print("="*60)
print("Interactive Dynamixel Test")
print("Encoder: Adjust Speed | Button: Toggle Motor / Jog")
print("Ctrl+C to Exit")
print("="*60)

last_btn = 1
btn_press_start = 0

try:
    motor = get_motor()
    update_ui()
    
    last_ui_update = 0
    
    while True:
        # Handle Encoder
        if encoder_delta != 0:
            target_velocity = max(0, min(100, target_velocity + encoder_delta))
            encoder_delta = 0
            if is_moving and motor:
                if target_velocity == 0:
                    motor.stop()
                    is_moving = False
                    print("Velocity 0: Stopping motor.")
                else:
                    motor.set_speed_limit(target_velocity)
                    # Re-send goal to make the speed change take effect immediately
                    motor.set_angle_degrees(last_target_pos)
            update_ui()

        # Handle Button
        btn = enc_btn.value()
        if btn == 0 and last_btn == 1: # Pressed
            btn_press_start = time.ticks_ms()
        elif btn == 1 and last_btn == 0: # Released
            press_duration = time.ticks_diff(time.ticks_ms(), btn_press_start)
            if press_duration < 500: # Short press: Jog or Toggle Move
                if not is_moving:
                    # Start continuous rotation
                    if motor:
                        if target_velocity == 0:
                            print("Cannot start with velocity 0")
                        else:
                            print(f"Starting movement at velocity {target_velocity}...")
                            # In Extended Position Mode, move to a very distant point
                            # Current pos + 1000 revolutions
                            last_target_pos = motor.output_degrees + 360000
                            motor.set_speed_limit(target_velocity)
                            motor.set_angle_degrees(last_target_pos)
                            is_moving = True
                else:
                    # Stop
                    if motor:
                        print("Stopping...")
                        motor.stop()
                    is_moving = False
            else: # Long press: Toggle Motor
                is_moving = False
                if motor: motor.stop()
                current_motor_id = 1 if current_motor_id == 2 else 2
                motor = get_motor()
            update_ui()
        last_btn = btn

        # Periodic Angle Update
        if time.ticks_diff(time.ticks_ms(), last_ui_update) > 200:
            if motor:
                motor.update_present_position(force=True)
                update_ui()
            last_ui_update = time.ticks_ms()
            
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\nExiting...")
    if motor: motor.stop()
    if HAS_DISPLAY:
        display.fill(0)
        display.text("Stopped", 0, 24)
        display.show()
