"""
DYNAMIXEL Extended Position Mode Utilities

Best practices for Extended Position Control Mode (Mode 4):
1. Set Mode 4 once and leave it permanently
2. Read Present Position on boot to avoid jumps
3. Use Clear Multi-Turn if you need to reset (optional)
4. Don't worry about overflow (62+ years at 1°/10sec)
"""

from machine import UART, Pin
import time

# UART setup
uart = UART(0, baudrate=57600, bits=8, parity=None, stop=1)
uart.init(tx=Pin(0), rx=Pin(1))
dir_pin = Pin(2, Pin.OUT, value=0)

# CRC Table
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
    crc = 0
    for byte in data:
        i = ((crc >> 8) ^ byte) & 0xFF
        crc = ((crc << 8) ^ CRC_TABLE[i]) & 0xFFFF
    return crc

def send_and_receive(packet, timeout_ms=150):
    """Send packet and get response"""
    while uart.any():
        uart.read()
    
    dir_pin.value(1)
    time.sleep_ms(10)
    uart.write(packet)
    time.sleep_ms(10)
    dir_pin.value(0)
    
    time.sleep_ms(timeout_ms)
    
    if uart.any():
        response = uart.read()
        for i in range(len(response) - 10):
            if response[i:i+4] == b'\xFF\xFF\xFD\x00':
                if i + 7 < len(response) and response[i+7] == 0x55:
                    pkt_len = response[i+5] + (response[i+6] << 8)
                    if i + 7 + pkt_len <= len(response):
                        return response[i:i+7+pkt_len]
    return None

def write_byte(servo_id, address, value):
    """Write a single byte"""
    packet = bytearray([0xFF, 0xFF, 0xFD, 0x00, servo_id, 0x06, 0x00, 0x03])
    packet.extend([address & 0xFF, (address >> 8) & 0xFF, value])
    crc = calc_crc(packet)
    packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    response = send_and_receive(bytes(packet))
    return response is not None and len(response) >= 9 and response[8] == 0

def write_dword(servo_id, address, value):
    """Write a 4-byte value"""
    packet = bytearray([0xFF, 0xFF, 0xFD, 0x00, servo_id, 0x09, 0x00, 0x03])
    packet.extend([address & 0xFF, (address >> 8) & 0xFF])
    packet.extend([value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF])
    crc = calc_crc(packet)
    packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    response = send_and_receive(bytes(packet))
    return response is not None and len(response) >= 9 and response[8] == 0

def read_dword(servo_id, address):
    """Read a 4-byte value (for position)"""
    packet = bytearray([0xFF, 0xFF, 0xFD, 0x00, servo_id, 0x07, 0x00, 0x02])
    packet.extend([address & 0xFF, (address >> 8) & 0xFF, 0x04, 0x00])  # Read 4 bytes
    crc = calc_crc(packet)
    packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    response = send_and_receive(bytes(packet))
    
    if response is not None and len(response) >= 13 and response[8] == 0:
        # Extract 4-byte value from response
        value = response[9] | (response[10] << 8) | (response[11] << 16) | (response[12] << 24)
        # Handle signed 32-bit integer
        if value >= 0x80000000:
            value -= 0x100000000
        return value
    return None

def clear_multi_turn(servo_id):
    """
    Clear Multi-Turn command - resets Present Position to 0-4095 range
    without moving the motor. Useful for resetting the counter.
    
    This is instruction 0x0A in the DYNAMIXEL protocol.
    """
    packet = bytearray([0xFF, 0xFF, 0xFD, 0x00, servo_id, 0x03, 0x00, 0x0A])
    crc = calc_crc(packet)
    packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    response = send_and_receive(bytes(packet))
    return response is not None and len(response) >= 9 and response[8] == 0

def read_present_position(servo_id):
    """
    Read the current position from the motor.
    CRITICAL: Call this on boot before sending any Goal Position commands!
    
    Returns: Current position as signed 32-bit integer, or None on error
    """
    return read_dword(servo_id, 132)  # ADDR_PRESENT_POSITION = 132

def set_extended_mode(servo_id):
    """
    Configure servo for Extended Position Mode (Mode 4).
    Do this ONCE and leave it permanently.
    """
    print(f"Configuring Motor {servo_id} for Extended Position Mode...")
    
    # Disable torque
    if not write_byte(servo_id, 64, 0):  # ADDR_TORQUE_ENABLE = 64
        print(f"  ✗ Failed to disable torque")
        return False
    
    # Set Operating Mode to 4 (Extended Position)
    if not write_byte(servo_id, 11, 4):  # ADDR_OPERATING_MODE = 11
        print(f"  ✗ Failed to set operating mode")
        return False
    
    # Re-enable torque
    if not write_byte(servo_id, 64, 1):
        print(f"  ✗ Failed to enable torque")
        return False
    
    print(f"  ✓ Motor {servo_id} configured for Extended Position Mode")
    return True

def get_new_pos(current_pos, command_pos):
    """
    Calculate new motor position using shortest path in Extended Position Mode.
    
    This function preserves the number of full revolutions the motor has made
    and applies the change via the SHORTEST path (-180° to +180°).
    
    Args:
        current_pos: Current motor position (can be > 360° in Extended Mode)
        command_pos: Commanded position (typically 0-360°)
    
    Returns:
        New position with preserved turn count, using shortest path
        
    Examples:
        current_pos = 358.0, command_pos = 2.0
        Returns: 362.0  # Moves forward +4° (shortest path)
        
        current_pos = 10.0, command_pos = 350.0
        Returns: 370.0  # Moves backward -20° (shortest path)
    """
    turns, pos = divmod(current_pos, 360)
    change = command_pos - pos
    # Normalize change to shortest path: -180 to +180
    change = (change + 180) % 360 - 180
    return turns * 360 + pos + change

def power_on_routine(servo_id):
    """
    CRITICAL: Run this on every boot!
    
    Reads the current position and returns it as the baseline.
    Use this value as your starting point to avoid motor jumps.
    
    Returns: Current position, or None on error
    """
    print(f"Reading Motor {servo_id} present position...")
    position = read_present_position(servo_id)
    
    if position is not None:
        rotations = position / 4096.0
        degrees = (position % 4096) / 4096.0 * 360.0
        print(f"  Motor {servo_id}: position={position} ({rotations:.2f} rotations, {degrees:.1f}° within current rotation)")
        return position
    else:
        print(f"  ✗ Failed to read position from Motor {servo_id}")
        return None

# Example usage for Orbigator boot sequence:
def orbigator_init():
    """
    Complete initialization routine for Orbigator motors.
    Call this once on boot.
    """
    print("="*60)
    print("ORBIGATOR MOTOR INITIALIZATION")
    print("="*60)
    print()
    
    # Read current positions (CRITICAL - do this before any movement!)
    lan_pos = power_on_routine(1)
    aov_pos = power_on_routine(2)
    
    if lan_pos is None or aov_pos is None:
        print("\n✗ Failed to read motor positions!")
        return None, None
    
    print()
    print("✓ Motors initialized successfully")
    print(f"  EQX baseline: {lan_pos}")
    print(f"  AoV baseline: {aov_pos}")
    print()
    print("Use these values as your starting positions.")
    
    return lan_pos, aov_pos
