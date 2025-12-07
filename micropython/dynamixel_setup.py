"""
DYNAMIXEL XL330 Setup Utility for Raspberry Pi Pico 2
Replaces DYNAMIXEL Wizard for basic configuration tasks

Features:
- Scan for servos
- Change servo ID
- Read/write baud rate
- Enable/disable torque
- Read present position
- Factory reset

Usage: Run this script on the Pico to configure DYNAMIXEL servos
"""

from machine import UART, Pin
import time

# UART Configuration
UART_NUM = 0
TX_PIN = 0
RX_PIN = 1
DIR_PIN = 2
DEFAULT_BAUD = 57600

# Initialize UART and direction control
uart = UART(UART_NUM, baudrate=DEFAULT_BAUD, bits=8, parity=None, stop=1)
uart.init(tx=Pin(TX_PIN), rx=Pin(RX_PIN))
dir_pin = Pin(DIR_PIN, Pin.OUT, value=0)

# DYNAMIXEL Protocol 2.0 Instructions
INST_PING = 0x01
INST_READ = 0x02
INST_WRITE = 0x03
INST_REG_WRITE = 0x04
INST_ACTION = 0x05
INST_FACTORY_RESET = 0x06
INST_REBOOT = 0x08
INST_CLEAR = 0x10
INST_STATUS = 0x55
INST_SYNC_READ = 0x82
INST_SYNC_WRITE = 0x83
INST_BULK_READ = 0x92
INST_BULK_WRITE = 0x93

# Common Control Table Addresses (XL330)
ADDR_MODEL_NUMBER = 0
ADDR_MODEL_INFORMATION = 2
ADDR_FIRMWARE_VERSION = 6
ADDR_ID = 7
ADDR_BAUD_RATE = 8
ADDR_RETURN_DELAY_TIME = 9
ADDR_DRIVE_MODE = 10
ADDR_OPERATING_MODE = 11
ADDR_SECONDARY_ID = 12
ADDR_PROTOCOL_TYPE = 13
ADDR_HOMING_OFFSET = 20
ADDR_MOVING_THRESHOLD = 24
ADDR_TEMPERATURE_LIMIT = 31
ADDR_MAX_VOLTAGE_LIMIT = 32
ADDR_MIN_VOLTAGE_LIMIT = 34
ADDR_PWM_LIMIT = 36
ADDR_CURRENT_LIMIT = 38
ADDR_VELOCITY_LIMIT = 44
ADDR_MAX_POSITION_LIMIT = 48
ADDR_MIN_POSITION_LIMIT = 52
ADDR_SHUTDOWN = 63
ADDR_TORQUE_ENABLE = 64
ADDR_LED = 65
ADDR_STATUS_RETURN_LEVEL = 68
ADDR_REGISTERED_INSTRUCTION = 69
ADDR_HARDWARE_ERROR_STATUS = 70
ADDR_VELOCITY_I_GAIN = 76
ADDR_VELOCITY_P_GAIN = 78
ADDR_POSITION_D_GAIN = 80
ADDR_POSITION_I_GAIN = 82
ADDR_POSITION_P_GAIN = 84
ADDR_FEEDFORWARD_2ND_GAIN = 88
ADDR_FEEDFORWARD_1ST_GAIN = 90
ADDR_BUS_WATCHDOG = 98
ADDR_GOAL_PWM = 100
ADDR_GOAL_CURRENT = 102
ADDR_GOAL_VELOCITY = 104
ADDR_PROFILE_ACCELERATION = 108
ADDR_PROFILE_VELOCITY = 112
ADDR_GOAL_POSITION = 116
ADDR_REALTIME_TICK = 120
ADDR_MOVING = 122
ADDR_MOVING_STATUS = 123
ADDR_PRESENT_PWM = 124
ADDR_PRESENT_CURRENT = 126
ADDR_PRESENT_VELOCITY = 128
ADDR_PRESENT_POSITION = 132
ADDR_VELOCITY_TRAJECTORY = 136
ADDR_POSITION_TRAJECTORY = 140
ADDR_PRESENT_INPUT_VOLTAGE = 144
ADDR_PRESENT_TEMPERATURE = 146

# Broadcast ID
BROADCAST_ID = 0xFE

# CRC Table for Protocol 2.0
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

def calculate_crc(data):
    """Calculate CRC-16 for DYNAMIXEL Protocol 2.0"""
    crc = 0
    for byte in data:
        i = ((crc >> 8) ^ byte) & 0xFF
        crc = ((crc << 8) ^ CRC_TABLE[i]) & 0xFFFF
    return crc

def set_tx_mode():
    """Enable transmit mode"""
    dir_pin.value(1)
    time.sleep_us(10)

def set_rx_mode():
    """Enable receive mode"""
    dir_pin.value(0)
    time.sleep_us(10)

def make_packet(servo_id, instruction, params=[]):
    """Build a DYNAMIXEL Protocol 2.0 packet"""
    # Header
    packet = bytearray([0xFF, 0xFF, 0xFD, 0x00])
    # ID
    packet.append(servo_id)
    # Length (params + 3 for instruction + error + crc)
    length = len(params) + 3
    packet.extend([length & 0xFF, (length >> 8) & 0xFF])
    # Instruction
    packet.append(instruction)
    # Parameters
    packet.extend(params)
    # CRC
    crc = calculate_crc(packet)
    packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    
    return bytes(packet)

def send_packet(packet):
    """Send packet to DYNAMIXEL"""
    set_tx_mode()
    uart.write(packet)
    # Wait for transmission to complete
    time.sleep_ms(2)
    set_rx_mode()

def receive_response(timeout_ms=100):
    """Receive response from DYNAMIXEL"""
    set_rx_mode()
    start = time.ticks_ms()
    response = bytearray()
    
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        if uart.any():
            response.extend(uart.read())
            # Check if we have minimum packet
            if len(response) >= 11:
                # Check if we have complete packet
                if len(response) >= 7:
                    expected_len = response[5] + (response[6] << 8) + 7
                    if len(response) >= expected_len:
                        break
        time.sleep_ms(1)
    
    return bytes(response)

def communicate(packet, timeout_ms=100):
    """Send packet and receive response"""
    # Clear any pending data
    while uart.any():
        uart.read()
    
    send_packet(packet)
    return receive_response(timeout_ms)

def parse_response(response):
    """Parse DYNAMIXEL response packet"""
    if len(response) < 11:
        return None
    
    # Check header
    if response[0:4] != b'\xFF\xFF\xFD\x00':
        return None
    
    servo_id = response[4]
    length = response[5] + (response[6] << 8)
    instruction = response[7]
    error = response[8]
    params = response[9:9+length-4]
    crc_received = response[-2] + (response[-1] << 8)
    
    # Verify CRC
    crc_calc = calculate_crc(response[:-2])
    if crc_calc != crc_received:
        print("CRC Error!")
        return None
    
    return {
        'id': servo_id,
        'instruction': instruction,
        'error': error,
        'params': params
    }

# ============ High-Level Functions ============

def ping(servo_id):
    """Ping a servo to check if it's connected"""
    packet = make_packet(servo_id, INST_PING, [])
    response = communicate(packet)
    result = parse_response(response)
    
    if result:
        print(f"Servo ID {servo_id}: FOUND")
        print(f"  Model: {result['params'][0] + (result['params'][1] << 8)}")
        print(f"  Firmware: {result['params'][2]}")
        return True
    else:
        print(f"Servo ID {servo_id}: NOT FOUND")
        return False

def scan_servos(start_id=0, end_id=252):
    """Scan for all connected servos"""
    print(f"Scanning for servos (ID {start_id} to {end_id})...")
    found = []
    
    for servo_id in range(start_id, end_id + 1):
        packet = make_packet(servo_id, INST_PING, [])
        response = communicate(packet, timeout_ms=50)
        result = parse_response(response)
        
        if result:
            found.append(servo_id)
            print(f"  Found servo at ID {servo_id}")
    
    print(f"\nTotal servos found: {len(found)}")
    return found

def read_data(servo_id, address, length):
    """Read data from servo"""
    params = [
        address & 0xFF,
        (address >> 8) & 0xFF,
        length & 0xFF,
        (length >> 8) & 0xFF
    ]
    packet = make_packet(servo_id, INST_READ, params)
    response = communicate(packet)
    result = parse_response(response)
    
    if result and result['error'] == 0:
        return result['params']
    else:
        return None

def write_data(servo_id, address, data):
    """Write data to servo"""
    params = [address & 0xFF, (address >> 8) & 0xFF]
    if isinstance(data, int):
        # Convert int to bytes (little-endian)
        if data < 256:
            params.append(data)
        elif data < 65536:
            params.extend([data & 0xFF, (data >> 8) & 0xFF])
        else:
            params.extend([data & 0xFF, (data >> 8) & 0xFF, 
                          (data >> 16) & 0xFF, (data >> 24) & 0xFF])
    else:
        params.extend(data)
    
    packet = make_packet(servo_id, INST_WRITE, params)
    response = communicate(packet)
    result = parse_response(response)
    
    return result is not None and result['error'] == 0

def change_id(old_id, new_id):
    """Change servo ID"""
    print(f"Changing servo ID from {old_id} to {new_id}...")
    
    # First ping to verify servo exists
    if not ping(old_id):
        print("Error: Servo not found at old ID")
        return False
    
    # Write new ID
    success = write_data(old_id, ADDR_ID, new_id)
    
    if success:
        print(f"Success! Servo ID changed to {new_id}")
        # Verify
        time.sleep_ms(100)
        ping(new_id)
        return True
    else:
        print("Error: Failed to change ID")
        return False

def read_position(servo_id):
    """Read present position"""
    data = read_data(servo_id, ADDR_PRESENT_POSITION, 4)
    if data:
        pos = data[0] + (data[1] << 8) + (data[2] << 16) + (data[3] << 24)
        # Convert to signed if needed
        if pos > 2147483647:
            pos -= 4294967296
        angle = (pos / 4095.0) * 360.0
        print(f"Servo {servo_id} Position: {pos} ({angle:.1f}°)")
        return pos
    return None

def set_torque(servo_id, enable=True):
    """Enable or disable torque"""
    value = 1 if enable else 0
    success = write_data(servo_id, ADDR_TORQUE_ENABLE, value)
    if success:
        print(f"Servo {servo_id} Torque: {'ENABLED' if enable else 'DISABLED'}")
    return success

def set_position(servo_id, position):
    """Set goal position (0-4095)"""
    position = max(0, min(4095, position))
    success = write_data(servo_id, ADDR_GOAL_POSITION, position)
    if success:
        angle = (position / 4095.0) * 360.0
        print(f"Servo {servo_id} Goal Position: {position} ({angle:.1f}°)")
    return success

def factory_reset(servo_id):
    """Factory reset servo (WARNING: Resets ID to 1!)"""
    print(f"WARNING: Factory reset will reset servo {servo_id} to default settings!")
    print("ID will be reset to 1, baud rate to 57600")
    
    packet = make_packet(servo_id, INST_FACTORY_RESET, [0xFF])
    response = communicate(packet, timeout_ms=500)
    result = parse_response(response)
    
    if result:
        print("Factory reset successful!")
        return True
    else:
        print("Factory reset failed")
        return False

def reboot(servo_id):
    """Reboot servo"""
    packet = make_packet(servo_id, INST_REBOOT, [])
    response = communicate(packet, timeout_ms=500)
    result = parse_response(response)
    
    if result:
        print(f"Servo {servo_id} rebooted")
        return True
    return False

# ============ Interactive Menu ============

def print_menu():
    print("\n" + "="*50)
    print("DYNAMIXEL XL330 Setup Utility")
    print("="*50)
    print("1. Scan for servos")
    print("2. Ping servo")
    print("3. Change servo ID")
    print("4. Read position")
    print("5. Enable torque")
    print("6. Disable torque")
    print("7. Set position")
    print("8. Factory reset")
    print("9. Reboot servo")
    print("0. Exit")
    print("="*50)

def main():
    """Main interactive loop"""
    print("\nDYNAMIXEL Setup Utility Started")
    print(f"UART: {UART_NUM}, Baud: {DEFAULT_BAUD}")
    print(f"TX: GP{TX_PIN}, RX: GP{RX_PIN}, DIR: GP{DIR_PIN}")
    
    while True:
        print_menu()
        choice = input("Select option: ").strip()
        
        if choice == '1':
            scan_servos()
        
        elif choice == '2':
            servo_id = int(input("Enter servo ID: "))
            ping(servo_id)
        
        elif choice == '3':
            old_id = int(input("Enter current ID: "))
            new_id = int(input("Enter new ID (1-252): "))
            change_id(old_id, new_id)
        
        elif choice == '4':
            servo_id = int(input("Enter servo ID: "))
            read_position(servo_id)
        
        elif choice == '5':
            servo_id = int(input("Enter servo ID: "))
            set_torque(servo_id, True)
        
        elif choice == '6':
            servo_id = int(input("Enter servo ID: "))
            set_torque(servo_id, False)
        
        elif choice == '7':
            servo_id = int(input("Enter servo ID: "))
            position = int(input("Enter position (0-4095): "))
            set_torque(servo_id, True)
            set_position(servo_id, position)
        
        elif choice == '8':
            servo_id = int(input("Enter servo ID: "))
            confirm = input("Are you sure? (yes/no): ")
            if confirm.lower() == 'yes':
                factory_reset(servo_id)
        
        elif choice == '9':
            servo_id = int(input("Enter servo ID: "))
            reboot(servo_id)
        
        elif choice == '0':
            print("Exiting...")
            break
        
        else:
            print("Invalid option")

# Quick setup functions for Orbigator
def setup_orbigator_servos():
    """Quick setup for Orbigator: Configure 2 servos as ID 1 and 2"""
    print("\n=== ORBIGATOR SERVO SETUP ===")
    print("This will configure your servos for Orbigator")
    print("Make sure ONLY ONE servo is connected at a time!\n")
    
    input("Connect FIRST servo (LAN Motor) and press Enter...")
    
    # Scan for servo
    found = scan_servos()
    if len(found) != 1:
        print("Error: Expected exactly 1 servo. Please check connections.")
        return
    
    current_id = found[0]
    print(f"\nFound servo at ID {current_id}")
    
    if current_id != 1:
        print("Setting servo to ID 1 (LAN Motor)...")
        change_id(current_id, 1)
    else:
        print("Servo already at ID 1")
    
    print("\nDisconnect first servo")
    input("Connect SECOND servo (AOV Motor) and press Enter...")
    
    # Scan for second servo
    found = scan_servos()
    if len(found) != 1:
        print("Error: Expected exactly 1 servo. Please check connections.")
        return
    
    current_id = found[0]
    print(f"\nFound servo at ID {current_id}")
    
    if current_id != 2:
        print("Setting servo to ID 2 (AOV Motor)...")
        change_id(current_id, 2)
    else:
        print("Servo already at ID 2")
    
    print("\n=== SETUP COMPLETE ===")
    print("You can now connect both servos in daisy-chain")
    print("Servo 1: LAN Motor")
    print("Servo 2: AOV Motor")

if __name__ == "__main__":
    # Uncomment one of these:
    
    # Option 1: Interactive menu
    main()
    
    # Option 2: Quick Orbigator setup
    # setup_orbigator_servos()
    
    # Option 3: Quick test
    # scan_servos()
    # ping(1)
    # ping(2)
