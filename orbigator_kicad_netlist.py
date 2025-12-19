"""
ORBIGATOR KiCad Netlist - Pin Assignments
Raspberry Pi Pico 2 with DYNAMIXEL Motors

This file can be used as reference for KiCad schematic creation.
Format compatible with KiCad Python scripting.
"""

# Component definitions
components = {
    'U1': {
        'name': 'Raspberry Pi Pico 2',
        'type': 'MCU',
        'pins': {
            1: {'name': 'GP0', 'function': 'UART0_TX'},
            2: {'name': 'GP1', 'function': 'UART0_RX'},
            3: {'name': 'GND', 'function': 'Ground'},
            4: {'name': 'GP2', 'function': 'GPIO_OUT'},
            5: {'name': 'GP3', 'function': 'GPIO'},
            6: {'name': 'GP4', 'function': 'I2C0_SDA'},
            7: {'name': 'GP5', 'function': 'I2C0_SCL'},
            8: {'name': 'GND', 'function': 'Ground'},
            9: {'name': 'GP6', 'function': 'GPIO_IN'},
            10: {'name': 'GP7', 'function': 'GPIO_IN'},
            11: {'name': 'GP8', 'function': 'GPIO_IN'},
            36: {'name': '3V3(OUT)', 'function': 'Power'},
            38: {'name': 'GND', 'function': 'Ground'},
        }
    },
    'U2': {
        'name': 'SN74HC126N',
        'type': 'Buffer',
        'pins': {
            1: {'name': '1OE', 'function': 'Output Enable'},
            2: {'name': '1A', 'function': 'Input'},
            3: {'name': '1Y', 'function': 'Output'},
            7: {'name': 'GND', 'function': 'Ground'},
            14: {'name': 'VCC', 'function': 'Power'},
        }
    },
    'M1': {
        'name': 'DYNAMIXEL XL330-M288-T (LAN)',
        'type': 'Servo',
        'id': 1,
        'pins': {
            1: {'name': 'GND', 'function': 'Ground'},
            2: {'name': 'VDD', 'function': 'Power 5V'},
            3: {'name': 'DATA', 'function': 'Half-Duplex UART'},
        }
    },
    'M2': {
        'name': 'DYNAMIXEL XL330-M288-T (AoV)',
        'type': 'Servo',
        'id': 2,
        'pins': {
            1: {'name': 'GND', 'function': 'Ground'},
            2: {'name': 'VDD', 'function': 'Power 5V'},
            3: {'name': 'DATA', 'function': 'Half-Duplex UART'},
        }
    },
    'DISP1': {
        'name': 'OLED Display (SH1106/SSD1306)',
        'type': 'Display',
        'i2c_addr': '0x3C',
        'pins': {
            1: {'name': 'VCC', 'function': 'Power 3.3V'},
            2: {'name': 'GND', 'function': 'Ground'},
            3: {'name': 'SDA', 'function': 'I2C Data'},
            4: {'name': 'SCL', 'function': 'I2C Clock'},
        }
    },
    'RTC1': {
        'name': 'DS3231 RTC (ChronoDot)',
        'type': 'RTC',
        'i2c_addr': '0x68',
        'pins': {
            1: {'name': 'VCC', 'function': 'Power 3.3V'},
            2: {'name': 'GND', 'function': 'Ground'},
            3: {'name': 'SDA', 'function': 'I2C Data'},
            4: {'name': 'SCL', 'function': 'I2C Clock'},
        }
    },
    'ENC1': {
        'name': 'Rotary Encoder',
        'type': 'Input',
        'pins': {
            1: {'name': 'A', 'function': 'Phase A'},
            2: {'name': 'B', 'function': 'Phase B'},
            3: {'name': 'SW', 'function': 'Switch'},
            4: {'name': 'GND', 'function': 'Ground'},
        }
    },
    'R1': {
        'name': '10kΩ Resistor',
        'type': 'Resistor',
        'value': '10k',
        'pins': {
            1: {'name': 'A', 'function': 'Terminal A'},
            2: {'name': 'B', 'function': 'Terminal B'},
        }
    },
    'PS1': {
        'name': '5V Power Supply',
        'type': 'Power',
        'rating': '4-5A',
        'pins': {
            1: {'name': '+5V', 'function': 'Positive'},
            2: {'name': 'GND', 'function': 'Ground'},
        }
    }
}

# Net definitions (connections)
nets = {
    'GND': {
        'description': 'Common Ground',
        'connections': [
            ('U1', 3),   # Pico GND
            ('U1', 8),   # Pico GND
            ('U1', 38),  # Pico GND
            ('U2', 7),   # Buffer GND
            ('M1', 1),   # Motor 1 GND
            ('M2', 1),   # Motor 2 GND
            ('DISP1', 2),  # OLED GND
            ('RTC1', 2),   # RTC GND
            ('ENC1', 4),   # Encoder GND
            ('PS1', 2),    # 5V Supply GND
        ]
    },
    '+3V3': {
        'description': '3.3V Power Rail',
        'connections': [
            ('U1', 36),    # Pico 3V3 OUT
            ('U2', 14),    # Buffer VCC
            ('DISP1', 1),  # OLED VCC
            ('RTC1', 1),   # RTC VCC
        ]
    },
    '+5V': {
        'description': '5V Power Rail (External)',
        'connections': [
            ('PS1', 1),    # 5V Supply
            ('M1', 2),     # Motor 1 VDD
            ('M2', 2),     # Motor 2 VDD
            ('R1', 1),     # Pull-up resistor (top)
        ]
    },
    'UART_TX': {
        'description': 'UART TX from Pico to Buffer',
        'connections': [
            ('U1', 1),     # Pico GP0
            ('U2', 2),     # Buffer 1A (Input)
        ]
    },
    'DIR_CTRL': {
        'description': 'Direction Control for Buffer',
        'connections': [
            ('U1', 4),     # Pico GP2
            ('U2', 1),     # Buffer 1OE (Output Enable)
        ]
    },
    'DATA_BUS': {
        'description': 'DYNAMIXEL Half-Duplex Data Bus',
        'connections': [
            ('U1', 2),     # Pico GP1 (UART RX)
            ('U2', 3),     # Buffer 1Y (Output)
            ('M1', 3),     # Motor 1 DATA
            ('M2', 3),     # Motor 2 DATA
            ('R1', 2),     # Pull-up resistor (bottom)
        ]
    },
    'I2C_SDA': {
        'description': 'I2C Data Line (shared)',
        'connections': [
            ('U1', 6),     # Pico GP4
            ('DISP1', 3),  # OLED SDA
            ('RTC1', 3),   # RTC SDA
        ]
    },
    'I2C_SCL': {
        'description': 'I2C Clock Line (shared)',
        'connections': [
            ('U1', 7),     # Pico GP5
            ('DISP1', 4),  # OLED SCL
            ('RTC1', 4),   # RTC SCL
        ]
    },
    'ENC_A': {
        'description': 'Encoder Phase A',
        'connections': [
            ('U1', 9),     # Pico GP6
            ('ENC1', 1),   # Encoder A
        ]
    },
    'ENC_B': {
        'description': 'Encoder Phase B',
        'connections': [
            ('U1', 10),    # Pico GP7
            ('ENC1', 2),   # Encoder B
        ]
    },
    'ENC_SW': {
        'description': 'Encoder Switch',
        'connections': [
            ('U1', 11),    # Pico GP8
            ('ENC1', 3),   # Encoder SW
        ]
    },
}

# Configuration parameters
config = {
    'uart': {
        'peripheral': 'UART0',
        'baud_rate': 57600,
        'data_bits': 8,
        'parity': 'None',
        'stop_bits': 1,
        'tx_pin': 'GP0',
        'rx_pin': 'GP1',
    },
    'i2c': {
        'peripheral': 'I2C0',
        'frequency': 100000,  # 100 kHz
        'sda_pin': 'GP4',
        'scl_pin': 'GP5',
    },
    'dynamixel': {
        'motor_1': {
            'id': 1,
            'name': 'EQX',
            'operating_mode': 4,  # Extended Position Control
            'gear_ratio': 120.0 / 11.0,  # Ring gear / Drive gear
        },
        'motor_2': {
            'id': 2,
            'name': 'AoV',
            'operating_mode': 4,  # Extended Position Control
            'gear_ratio': 1.0,  # Direct drive
        },
    },
    'encoder': {
        'a_pin': 'GP6',
        'b_pin': 'GP7',
        'sw_pin': 'GP8',
        'detent_div': 2,
        'pull_up': True,
    },
}

# Bill of Materials
bom = [
    {'ref': 'U1', 'value': 'Raspberry Pi Pico 2', 'qty': 1},
    {'ref': 'U2', 'value': 'SN74HC126N', 'qty': 1},
    {'ref': 'M1', 'value': 'DYNAMIXEL XL330-M288-T', 'qty': 1, 'notes': 'EQX Motor, ID=1'},
    {'ref': 'M2', 'value': 'DYNAMIXEL XL330-M288-T', 'qty': 1, 'notes': 'AoV Motor, ID=2'},
    {'ref': 'DISP1', 'value': 'OLED 128x64 (SH1106/SSD1306)', 'qty': 1},
    {'ref': 'RTC1', 'value': 'DS3231 RTC (ChronoDot)', 'qty': 1},
    {'ref': 'ENC1', 'value': 'Rotary Encoder with Switch', 'qty': 1},
    {'ref': 'R1', 'value': '10kΩ', 'qty': 1, 'notes': 'Pull-up for DATA line'},
    {'ref': 'PS1', 'value': '5V 4-5A Power Supply', 'qty': 1, 'notes': 'For DYNAMIXEL motors'},
]

# Design rules and notes
design_notes = """
CRITICAL DESIGN NOTES:
======================

1. POWER ISOLATION
   - DYNAMIXEL motors MUST use external 5V supply (4-5A minimum)
   - DO NOT power motors from Pico VSYS or USB
   - Common ground between Pico and motor supply is CRITICAL

2. HALF-DUPLEX UART
   - 74HC126 tri-state buffer enables half-duplex communication
   - GP2 controls buffer: HIGH = Pico TX, LOW = Motor TX
   - 10kΩ pull-up on DATA line to 5V is required

3. I2C BUS
   - OLED and RTC share I2C0 bus (different addresses)
   - 100 kHz frequency for reliability with long wires
   - Internal pull-ups may be sufficient, external 4.7kΩ optional

4. ENCODER
   - Uses internal pull-ups on Pico (no external resistors needed)
   - DETENT_DIV = 2 for responsive feel
   - Direction reversed in software ISR

5. DYNAMIXEL PINOUT
   - Pin 1 (GND) always on outer edge of connector
   - Both connectors on motor are MIRRORED
   - Verify with multimeter before connecting power

6. FIRMWARE
   - File: orbigator.py
   - Extended Position Mode (Mode 4) set once, left permanently
   - Position read on boot before any commands (prevents jumps)
   - AoV catch-up limited to ±180° (shortest path)
"""

if __name__ == '__main__':
    print("ORBIGATOR KiCad Netlist")
    print("=" * 60)
    print("\nComponents:")
    for ref, comp in components.items():
        print(f"  {ref}: {comp['name']}")
    
    print("\nNets:")
    for net_name, net_info in nets.items():
        print(f"  {net_name}: {net_info['description']}")
        print(f"    Connections: {len(net_info['connections'])}")
    
    print("\nBill of Materials:")
    for item in bom:
        notes = f" - {item['notes']}" if 'notes' in item else ""
        print(f"  {item['ref']}: {item['value']} (x{item['qty']}){notes}")
    
    print("\n" + design_notes)
