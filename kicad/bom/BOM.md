# Orbigator Bill of Materials (BOM)

## Microcontroller

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| U1 | 1 | Raspberry Pi Pico 2 | RP2350 Microcontroller Board | Module:Raspberry_Pi_Pico_SMD | [Link](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf) | Main controller |

## Logic ICs

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| U2 | 1 | 74HC126 | Quad Tri-State Buffer | Package_DIP:DIP-14_W7.62mm | [Link](https://www.ti.com/lit/ds/symlink/sn74hc126.pdf) | UART direction control |

## Display & RTC

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| DISP1 | 1 | SSD1306/SH1106 | 128x64 OLED Display | Display:OLED_128x64_I2C | [Link](https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf) | I2C Address: 0x3C |
| RTC1 | 1 | DS3231 | Real-Time Clock Module | Module:ChronoDot_RTC | [Link](https://datasheets.maximintegrated.com/en/ds/DS3231.pdf) | I2C Address: 0x68 |

## Motors

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| M1 | 1 | XL330-M288-T | DYNAMIXEL Servo (ID 1) | Connector_JST:JST_EH_B3B-EH-A_1x03_P2.50mm_Vertical | [Link](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/) | EQX Motor, 11T→120T gearing |
| M2 | 1 | XL330-M288-T | DYNAMIXEL Servo (ID 2) | Connector_JST:JST_EH_B3B-EH-A_1x03_P2.50mm_Vertical | [Link](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/) | AoV Motor, direct drive |

## User Interface

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| ENC1 | 1 | Rotary Encoder | Encoder with push button | Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm | - | User input |

## Resistors

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| R1 | 1 | 10kΩ | Pull-up resistor | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal | - | DYNAMIXEL DATA bus pull-up to +5V |
| R2 | 1 | 4.7kΩ | Pull-up resistor | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal | - | I2C SDA pull-up to +3.3V **CRITICAL** |
| R3 | 1 | 4.7kΩ | Pull-up resistor | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal | - | I2C SCL pull-up to +3.3V **CRITICAL** |
| R4 | 1 | 47Ω | Current limiting resistor | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal | - | Supercap charging resistor |

## Capacitors

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| C1 | 1 | 0.47F 5.5V | Supercapacitor | Capacitor_THT:CP_Radial_D10.0mm_P5.00mm | [Link](https://industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ABA0000C1218.pdf) | RTC backup power (recommended) |
| C2 | 1 | 100nF | Ceramic capacitor | Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm | - | 74HC126 decoupling |
| C3 | 1 | 100nF | Ceramic capacitor | Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm | - | Pico decoupling |

## Connectors

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| J1 | 1 | Barrel Jack | 5V Power Input | Connector_BarrelJack:BarrelJack_Horizontal | - | 5V 4-5A supply |
| J2 | 1 | JST-EH 3-pin | DYNAMIXEL Bus | Connector_JST:JST_EH_B3B-EH-A_1x03_P2.50mm_Vertical | - | Motor daisy-chain |
| J3 | 1 | Header 5-pin | Rotary Encoder | Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical | - | A, B, SW, VCC, GND |

## Optional Components

| Ref | Qty | Value | Description | Footprint | Datasheet | Notes |
|-----|-----|-------|-------------|-----------|-----------|-------|
| BAT1 | 1 | CR2032 | Coin cell battery | Battery:BatteryHolder_Keystone_3000_1x12mm | - | Alternative to supercap (larger footprint) |

## Assembly Notes

### Critical Requirements

1. **I2C Pull-ups (R2, R3)**: 
   - **MUST** be installed for reliable I2C communication
   - Without these, OLED will glitch and RTC will be unreliable
   - Individual module pull-ups are NOT sufficient

2. **RTC Backup Power**:
   - **Recommended**: 0.47F supercapacitor (C1) with 47Ω resistor (R4)
   - Provides several days to weeks of backup
   - Much smaller footprint than CR2032
   - Alternative: CR2032 battery (BAT1) for 5-10 years backup

3. **DYNAMIXEL Pull-up (R1)**:
   - Required for reliable half-duplex communication
   - Must be connected to +5V (motor supply voltage)

### Power Distribution

- **3.3V Rail** (from Pico): U2, DISP1, RTC1, ENC1
- **5V Rail** (external): M1, M2, R1 pull-up
- **Common Ground**: All components

### Connector Pinouts

**J2 - DYNAMIXEL (JST-EH 3-pin)**:
1. GND
2. VDD (+5V)
3. DATA

**J3 - Encoder (5-pin header)**:
1. A (GP6)
2. B (GP7)
3. SW (GP8)
4. VCC (+3.3V)
5. GND

## Cost Estimate

| Category | Estimated Cost (USD) |
|----------|---------------------|
| Pico 2 | $5.00 |
| Motors (2x) | $50.00 |
| Display | $8.00 |
| RTC Module | $10.00 |
| Encoder | $2.00 |
| Passives & ICs | $5.00 |
| PCB (prototype) | $10.00 |
| **Total** | **~$90.00** |

## Sourcing

- **Pico 2**: Adafruit, Pimoroni, SparkFun
- **DYNAMIXEL XL330-M288-T**: ROBOTIS official store
- **OLED Display**: Adafruit, Amazon, AliExpress
- **DS3231 RTC**: Adafruit ChronoDot, Amazon
- **Passives**: Digi-Key, Mouser, LCSC

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-21 | Justin Shaw | Initial BOM with supercap backup option |
