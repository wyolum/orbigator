# pins.py - Orbigator GPIO Assignment Module
# Raspberry Pi Pico 2 with DYNAMIXEL XL330-M288-T Motors
# Aligned with orbigator.py and ORBIGATOR_PIN_ASSIGNMENTS.txt

from machine import Pin

# ---------------------------
# DYNAMIXEL Communication (UART0 + 74HC126 Buffer)
# ---------------------------
UART_TX = 0      # GP0 - UART0 TX → 74HC126 Pin 2 (1A)
UART_RX = 1      # GP1 - UART0 RX → DYNAMIXEL DATA line
UART_DIR = 2     # GP2 - Direction Control → 74HC126 Pin 1 (1OE)

# ---------------------------
# I2C Bus (OLED + DS3231 RTC)
# ---------------------------
I2C_SDA = 4      # GP4 - I2C0 SDA (shared: OLED + RTC)
I2C_SCL = 5      # GP5 - I2C0 SCL (shared: OLED + RTC)

# ---------------------------
# Rotary Encoder
# ---------------------------
ENC_A = 6        # GP6 - Encoder Phase A (with internal pull-up)
ENC_B = 7        # GP7 - Encoder Phase B (with internal pull-up)
ENC_SW = 8       # GP8 - Encoder Switch (with internal pull-up)

# ---------------------------
# Helper Pin Constructors
# ---------------------------
# UART pins (managed by UART peripheral, typically not constructed manually)
uart_dir_pin = Pin(UART_DIR, Pin.OUT)

# I2C pins (managed by I2C peripheral)
# i2c_sda_pin = Pin(I2C_SDA, Pin.OUT, Pin.OPEN_DRAIN)
# i2c_scl_pin = Pin(I2C_SCL, Pin.OUT, Pin.OPEN_DRAIN)

# Encoder pins
enc_a_pin = Pin(ENC_A, Pin.IN, Pin.PULL_UP)
enc_b_pin = Pin(ENC_B, Pin.IN, Pin.PULL_UP)
enc_sw_pin = Pin(ENC_SW, Pin.IN, Pin.PULL_UP)

# ---------------------------
# Motor Configuration
# ---------------------------
# DYNAMIXEL Motor IDs
MOTOR_ID_AOV = 1  # Argument of Vehicle (direct drive)
MOTOR_ID_EQX = 2  # Equator crossing (11T → 120T gearing)

# Gear Ratios
EQX_GEAR_RATIO = 120.0 / 11.0  # Ring gear / Drive gear
AOV_GEAR_RATIO = 1.0            # Direct drive

# ---------------------------
# UART Configuration
# ---------------------------
UART_BAUD = 57600
UART_BITS = 8
UART_PARITY = None
UART_STOP = 1

# ---------------------------
# I2C Configuration
# ---------------------------
I2C_FREQ = 100_000  # 100 kHz for reliability with ChronoDot/DS3231

# I2C Addresses
OLED_ADDR = 0x3C    # OLED Display (SH1106/SSD1306)
RTC_ADDR = 0x68     # DS3231 RTC (ChronoDot)

# ---------------------------
# Encoder Configuration
# ---------------------------
DETENT_DIV = 2      # Encoder counts per detent (for responsiveness)
DEBOUNCE_MS = 200   # Button debounce time in milliseconds
