"""
Orbigator Pin Definitions
Single source of truth for all GPIO assignments.
Matches CURRENT BREADBOARD CONFIGURATION (Legacy)
"""
from machine import Pin

# I2C (OLED + RTC)
I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

# DYNAMIXEL UART (UART0)
DYNAMIXEL_UART_ID = 0
DYNAMIXEL_TX_PIN = 0
DYNAMIXEL_RX_PIN = 1
DYNAMIXEL_DIR_PIN = 2  # Direction control for buffer

# ROTARY ENCODER
ENC_A_PIN = 6
ENC_B_PIN = 7
ENC_BTN_PIN = 8

# BUTTONS
BACK_BTN_PIN = 9
CONFIRM_BTN_PIN = 10
