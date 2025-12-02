
# pins.py - Orbigator GPIO Assignment Module
# Version aligned with Orbigator Spec v1.6
# Provides a single source of truth for all GPIO pin definitions.

from machine import Pin

# ---------------------------
# I2C Bus (OLED + DS3231 RTC)
# ---------------------------
I2C_SDA = 4
I2C_SCL = 5

# ---------------------------
# Encoder + UI Buttons
# ---------------------------
ENC_A     = 16     # Encoder A (TRA)
ENC_B     = 17     # Encoder B (TRB)
ENC_PUSH  = 18     # Encoder push button (PSH) - Active LOW
CONFIRM   = 26     # Confirm button - Active LOW
BACK      = 27     # Back/Cancel button - Active LOW

# Helper constructors (optional)
confirm_btn = Pin(CONFIRM, Pin.IN, Pin.PULL_UP)
back_btn    = Pin(BACK, Pin.IN, Pin.PULL_UP)
enc_push    = Pin(ENC_PUSH, Pin.IN, Pin.PULL_UP)
enc_a       = Pin(ENC_A, Pin.IN, Pin.PULL_UP)
enc_b       = Pin(ENC_B, Pin.IN, Pin.PULL_UP)

# ---------------------------
# ULN2003 Stepper Drivers
# ---------------------------

# ULN2003 #1 – AOV Stepper
AOV_IN1 = 8
AOV_IN2 = 9
AOV_IN3 = 10
AOV_IN4 = 11

# ULN2003 #2 – Spare Stepper
ULN2_IN1 = 19
ULN2_IN2 = 20
ULN2_IN3 = 21
ULN2_IN4 = 22

# Grouped lists for ease of use
AOV_COILS = [AOV_IN1, AOV_IN2, AOV_IN3, AOV_IN4]
ULN2_COILS = [ULN2_IN1, ULN2_IN2, ULN2_IN3, ULN2_IN4]

# ---------------------------
# Pololu Step/Dir Drivers
# ---------------------------

# Pololu #1 – LAN Stepper
LAN_STEP = 14
LAN_DIR  = 15
LAN_M0   = 2
LAN_M1   = 3

# Pololu #2 – Spare Bipolar Motor
M2_STEP = 0
M2_DIR  = 1
M2_M0   = 6
M2_M1   = 7

# Shared Pololu enable/sleep pin
POLOLU_EN = 13

# ---------------------------
# Helper constructors for Pololu pins
# ---------------------------
lan_step_pin = Pin(LAN_STEP, Pin.OUT)
lan_dir_pin  = Pin(LAN_DIR, Pin.OUT)
lan_m0_pin   = Pin(LAN_M0, Pin.OUT)
lan_m1_pin   = Pin(LAN_M1, Pin.OUT)

m2_step_pin = Pin(M2_STEP, Pin.OUT)
m2_dir_pin  = Pin(M2_DIR, Pin.OUT)
m2_m0_pin   = Pin(M2_M0, Pin.OUT)
m2_m1_pin   = Pin(M2_M1, Pin.OUT)

pololu_en_pin = Pin(POLOLU_EN, Pin.OUT, value=1)  # shared EN/SLEEP
