import time
from machine import Pin, I2C, UART
import pins
from rtc import RTC
from oled_display import OledDisplay
from rotary_encoder import RotaryEncoder

import dynamixel_extended_utils as dxl_utils
from dynamixel_motor import DynamixelMotor

print("\n==================================")
print("       PCB V2 SUPER TEST")
print("==================================")

# 1. I2C Bus setup
print("\n[1] Initializing I2C...")
i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400000)
devices = i2c.scan()
print(f"    I2C scan found devices at: {[hex(d) for d in devices]}")

# 2. RTC Setup & SRAM Test
print("\n[2] Initializing RTC (DS3232)...")
rtc = RTC(i2c)

print("    Testing SRAM Read/Write...")
test_data = b"PCB_OK"
rtc.write_sram(0x14, test_data)
sram_ok = (rtc.read_sram(0x14, len(test_data)) == test_data)

# 3. OLED Setup
print("\n[3] Initializing OLED Display...")
try:
    display = OledDisplay(i2c)
    print(f"    ✓ OLED initialized")
except Exception as e:
    print(f"    ✗ OLED init failed: {e}")
    display = None

# 4. Encoder Setup
print("\n[4] Initializing Rotary Encoder...")
encoder = RotaryEncoder(pins.ENC_A_PIN, pins.ENC_B_PIN, pins.ENC_BTN_PIN)

# 5. Button Setup
print("\n[5] Initializing Buttons...")
btn_back = Pin(pins.BACK_BTN_PIN, Pin.IN, Pin.PULL_UP)
btn_confirm = Pin(pins.CONFIRM_BTN_PIN, Pin.IN, Pin.PULL_UP)

# 6. Motor Setup
print("\n[6] Initializing Motors...")
uart = UART(0, baudrate=57600, tx=Pin(pins.DYNAMIXEL_TX_PIN), rx=Pin(pins.DYNAMIXEL_RX_PIN))
dir_pin = Pin(pins.DYNAMIXEL_DIR_PIN, Pin.OUT)
dxl_utils.uart = uart
dxl_utils.dir_pin = dir_pin

dxl_utils.set_extended_mode(1)
dxl_utils.set_extended_mode(2)

try:
    motors = {
        1: DynamixelMotor(1, "EQX"),
        2: DynamixelMotor(2, "AoV"),
    }
    for m in motors.values():
        m.set_speed_limit(10) # Safe low speed
    motors_ok = True
    print("    ✓ Motors initialized")
except Exception as e:
    print(f"    ✗ Motor init failed: {e}")
    motors_ok = False


print("\n==================================")
print("Entering continuous loop.")
print("Watch the OLED and turn the encoder!")
print("==================================\n")

active_motor_id = 1
last_enc_val = encoder.value
last_confirm_val = btn_confirm.value()

# If using absolute positions, grab starting point
if motors_ok:
    target_degs = {
        1: motors[1].update_position() or 0,
        2: motors[2].update_position() or 0
    }

try:
    while True:
        # Read Time
        dt = rtc.datetime()
        if dt:
            # YY-MM-DD (8 chars) | HH:MM:SS (8 chars)
            date_str = f"{dt[0]%100:02d}-{dt[1]:02d}-{dt[2]:02d}"
            time_str = f"{dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"
        else:
            date_str = "RTC Error"
            time_str = ""
            
        # Read Inputs
        enc_val = encoder.value
        btn_str = "[X]" if encoder.button_pressed else "[ ]"
        
        back_str = "[B]" if btn_back.value() == 0 else "[ ]"
        confirm_val = btn_confirm.value()
        conf_str = "[C]" if confirm_val == 0 else "[ ]"
        
        # Toggle Active Motor on Confirm Fall
        if confirm_val == 0 and last_confirm_val == 1:
            active_motor_id = 2 if active_motor_id == 1 else 1
        last_confirm_val = confirm_val
        
        # Process Encoder Delta for Motor Driving
        enc_diff = enc_val - last_enc_val
        if enc_diff != 0 and motors_ok:
            # 1 tick = 10 degrees 
            target_degs[active_motor_id] += enc_diff * 10
            motors[active_motor_id]._write_goal(target_degs[active_motor_id])
        last_enc_val = enc_val
        
        sram_str = "SRAM:OK" if sram_ok else "SRAM:ERR"
        
        # OLED Rendering (64px high, 12px vertical spacing)
        if display:
            display.clear()
            
            # Line 0: Date & SRAM
            display.text(f"{date_str}  {sram_str}", 0, 0)
            
            # Line 12: Motor Status
            if motors_ok:
                m_name = motors[active_motor_id].name
                m_pos = motors[active_motor_id].update_position() or 0
                display.text(f"Mot: {m_name} {m_pos:.0f}dg", 0, 16)
            else:
                display.text("Motors: ERROR", 0, 16)
                
            # Line 24: Time
            display.text(f"Time: {time_str}", 0, 32)
            
            # Line 48: Enc, B, C
            display.text(f"E:{enc_val}", 0, 52)
            
            # Right justify buttons: 128 - (3*4 chars * 8px) = 128 - 96 = 32
            btns = f"{btn_str}{back_str}{conf_str}" # eg. "[X][B][C]"
            display.text(btns, 128 - (len(btns)*8), 52)
            
            display.show()
            
        time.sleep_ms(30) # ~30fps UX loop

except KeyboardInterrupt:
    print("\nSuper test stopped by user.")
finally:
    encoder.deinit()
