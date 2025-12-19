# EQX Motor Debug Script - Standalone Version
# Direct UART communication with Dynamixel protocol
# No external library dependencies

from machine import UART, Pin
import time

# UART setup for Dynamixel communication
uart = UART(0, baudrate=57600, bits=8, parity=None, stop=1)
uart.init(tx=Pin(0), rx=Pin(1))
dir_pin = Pin(2, Pin.OUT, value=0)

# Motor configuration
EQX_MOTOR_ID = 1
EQX_GEAR_RATIO = 120.0 / 11.0  # Ring gear / Drive gear

# Dynamixel addresses
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
ADDR_PROFILE_VELOCITY = 112

# CRC Table for Dynamixel Protocol 2.0
CRC_TABLE = [
    0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
    0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027, 0x0022,
    0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D, 0x8077, 0x0072,
    0x0050, 0x8055, 0x805F, 0x005A, 0x804B, 0x004E, 0x0044, 0x8041,
    0x80C3, 0x00C6, 0x00CC, 0x80C9, 0x00D8, 0x80DD, 0x80D7, 0x00D2,
    0x00F0, 0x80F5, 0x80FF, 0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1,
    0x00A0, 0x80A5, 0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1,
    0x8093, 0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
    0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197, 0x0192,
    0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE, 0x01A4, 0x81A1,
    0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB, 0x01FE, 0x01F4, 0x81F1,
    0x81D3, 0x01D6, 0x01DC, 0x81D9, 0x01C8, 0x81CD, 0x81C7, 0x01C2,
    0x0140, 0x8145, 0x814F, 0x014A, 0x815B, 0x015E, 0x0154, 0x8151,
    0x8173, 0x0176, 0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162,
    0x8123, 0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
    0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104, 0x8101,
    0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D, 0x8317, 0x0312,
    0x0330, 0x8335, 0x833F, 0x033A, 0x832B, 0x032E, 0x0324, 0x8321,
    0x0360, 0x8365, 0x836F, 0x036A, 0x837B, 0x037E, 0x0374, 0x8371,
    0x8353, 0x0356, 0x035C, 0x8359, 0x0348, 0x834D, 0x8347, 0x0342,
    0x03C0, 0x83C5, 0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1,
    0x83F3, 0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
    0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7, 0x03B2,
    0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E, 0x0384, 0x8381,
    0x0280, 0x8285, 0x828F, 0x028A, 0x829B, 0x029E, 0x0294, 0x8291,
    0x82B3, 0x02B6, 0x02BC, 0x82B9, 0x02A8, 0x82AD, 0x82A7, 0x02A2,
    0x82E3, 0x02E6, 0x02EC, 0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2,
    0x02D0, 0x82D5, 0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1,
    0x8243, 0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
    0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264, 0x8261,
    0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E, 0x0234, 0x8231,
    0x8213, 0x0216, 0x021C, 0x8219, 0x0208, 0x820D, 0x8207, 0x0202
]

def calc_crc(data):
    """Calculate CRC for Dynamixel Protocol 2.0"""
    crc = 0
    for byte in data:
        i = ((crc >> 8) ^ byte) & 0xFF
        crc = ((crc << 8) ^ CRC_TABLE[i]) & 0xFFFF
    return crc

def send_and_receive(packet, timeout_ms=150):
    """Send packet and receive response"""
    # Clear any pending data
    while uart.any():
        uart.read()
    
    # Send packet (TX mode)
    dir_pin.value(1)
    time.sleep_ms(10)
    uart.write(packet)
    time.sleep_ms(10)
    dir_pin.value(0)
    
    # Wait for response
    time.sleep_ms(timeout_ms)
    
    if uart.any():
        response = uart.read()
        # Find status packet header
        for i in range(len(response) - 10):
            if response[i:i+4] == b'\xFF\xFF\xFD\x00':
                if i + 7 < len(response) and response[i+7] == 0x55:
                    pkt_len = response[i+5] + (response[i+6] << 8)
                    if i + 7 + pkt_len <= len(response):
                        return response[i:i+7+pkt_len]
    return None

def write_dword(servo_id, address, value):
    """Write a 4-byte value to servo"""
    packet = bytearray([0xFF, 0xFF, 0xFD, 0x00, servo_id, 0x09, 0x00, 0x03])
    packet.extend([address & 0xFF, (address >> 8) & 0xFF])
    packet.extend([value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF])
    crc = calc_crc(packet)
    packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    response = send_and_receive(bytes(packet))
    return response is not None and len(response) >= 9 and response[8] == 0

def read_dword(servo_id, address):
    """Read a 4-byte value from servo"""
    packet = bytearray([0xFF, 0xFF, 0xFD, 0x00, servo_id, 0x07, 0x00, 0x02])
    packet.extend([address & 0xFF, (address >> 8) & 0xFF, 0x04, 0x00])
    crc = calc_crc(packet)
    packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    response = send_and_receive(bytes(packet))
    
    if response is not None and len(response) >= 13 and response[8] == 0:
        value = response[9] | (response[10] << 8) | (response[11] << 16) | (response[12] << 24)
        # Handle signed 32-bit integer
        if value >= 0x80000000:
            value -= 0x100000000
        return value
    return None

# Main script
print("="*60)
print("EQX Motor Debug Script - Standalone")
print("="*60)
print(f"Motor ID: {EQX_MOTOR_ID}")
print(f"Gear Ratio: {EQX_GEAR_RATIO:.2f}:1")
print()

# Read initial position
print("Reading initial position...")
initial_ticks = read_dword(EQX_MOTOR_ID, ADDR_PRESENT_POSITION)

if initial_ticks is None:
    print("✗ Failed to read position - check connections!")
    print("  - UART: TX=GP0, RX=GP1, DIR=GP2")
    print("  - Motor ID should be 1")
    print("  - Baud rate: 57600")
    import sys
    sys.exit(1)

print(f"✓ Initial position: {initial_ticks} ticks")

# Convert to degrees (motor degrees, not output degrees)
TICKS_PER_DEGREE = 4096.0 / 360.0
initial_motor_deg = initial_ticks / TICKS_PER_DEGREE
initial_output_deg = initial_motor_deg / EQX_GEAR_RATIO

print(f"  Motor degrees: {initial_motor_deg:.2f}°")
print(f"  Output degrees: {initial_output_deg:.2f}°")

# Set speed limit
print("\nSetting speed limit...")
if write_dword(EQX_MOTOR_ID, ADDR_PROFILE_VELOCITY, 50):
    print("✓ Speed limit set to 50")
else:
    print("⚠ Failed to set speed limit (continuing anyway)")

print("\n" + "="*60)
print("Starting continuous forward/backward movement")
print("1 revolution forward, 1 revolution backward")
print("Press Ctrl+C to stop")
print("="*60)

cycle = 0
try:
    while True:
        cycle += 1
        print(f"\n--- Cycle {cycle} ---")
        
        # Forward 1 revolution (360 motor degrees)
        forward_motor_deg = initial_motor_deg + 360.0
        forward_ticks = int(forward_motor_deg * TICKS_PER_DEGREE)
        
        print(f"Moving FORWARD to {forward_motor_deg:.2f}° motor ({forward_ticks} ticks)...")
        if write_dword(EQX_MOTOR_ID, ADDR_GOAL_POSITION, forward_ticks):
            print("  ✓ Command sent")
        else:
            print("  ✗ Command failed!")
        
        time.sleep(3)
        
        # Read actual position
        actual_ticks = read_dword(EQX_MOTOR_ID, ADDR_PRESENT_POSITION)
        if actual_ticks is not None:
            actual_motor_deg = actual_ticks / TICKS_PER_DEGREE
            print(f"  Actual position: {actual_motor_deg:.2f}° motor ({actual_ticks} ticks)")
        
        # Backward to initial position
        backward_ticks = int(initial_motor_deg * TICKS_PER_DEGREE)
        
        print(f"Moving BACKWARD to {initial_motor_deg:.2f}° motor ({backward_ticks} ticks)...")
        if write_dword(EQX_MOTOR_ID, ADDR_GOAL_POSITION, backward_ticks):
            print("  ✓ Command sent")
        else:
            print("  ✗ Command failed!")
        
        time.sleep(3)
        
        # Read actual position
        actual_ticks = read_dword(EQX_MOTOR_ID, ADDR_PRESENT_POSITION)
        if actual_ticks is not None:
            actual_motor_deg = actual_ticks / TICKS_PER_DEGREE
            print(f"  Actual position: {actual_motor_deg:.2f}° motor ({actual_ticks} ticks)")

except KeyboardInterrupt:
    print("\n\nStopped by user")
    print(f"Total cycles completed: {cycle}")
    
    # Return to initial position
    print(f"\nReturning to initial position ({initial_motor_deg:.2f}° motor)...")
    initial_ticks_int = int(initial_motor_deg * TICKS_PER_DEGREE)
    write_dword(EQX_MOTOR_ID, ADDR_GOAL_POSITION, initial_ticks_int)
    time.sleep(2)
    
    print("\n✓ Debug script complete")
