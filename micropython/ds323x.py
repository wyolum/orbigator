# DS323x RTC driver for MicroPython
# Supports both DS3231 and DS3232 RTCs
# DS3232 adds 236 bytes of battery-backed SRAM (addresses 0x14-0xFF)

import time

class DS323x:
    """
    Driver for DS3231 and DS3232 Real-Time Clock modules.
    
    DS3231: Basic RTC with temperature sensor
    DS3232: Adds 236 bytes of battery-backed SRAM at 0x14-0xFF
    
    Both use I2C address 0x68
    """
    
    # SRAM address range for DS3232
    SRAM_START = 0x14  # First SRAM address
    SRAM_END = 0xFF    # Last SRAM address
    SRAM_SIZE = 236    # Total SRAM bytes (0xFF - 0x14 + 1)
    
    def __init__(self, i2c, addr=0x68, has_sram=False):
        """
        Initialize DS323x RTC.
        
        Args:
            i2c: I2C bus instance
            addr: I2C address (default 0x68)
            has_sram: True for DS3232 (with SRAM), False for DS3231
        """
        self.i2c = i2c
        self.addr = addr
        self.has_sram = has_sram
        # Check if device is present
        # Note: Scan check disabled - do i2c.scan() before creating DS3231 instance
        # if addr not in i2c.scan():
        #     raise OSError("DS3231 not found at address 0x{:02x}".format(addr))

    def _bcd2dec(self, bcd):
        """Convert BCD to decimal"""
        return (bcd >> 4) * 10 + (bcd & 0x0F)

    def _dec2bcd(self, dec):
        """Convert decimal to BCD"""
        return ((dec // 10) << 4) + (dec % 10)

    def datetime(self, dt=None):
        """Get or set datetime as tuple: (year, month, day, weekday, hour, minute, second, subsecond)
        weekday: 0=Monday, 6=Sunday
        If dt is None, returns current datetime. If dt is provided, sets the datetime.
        Returns None if I2C communication fails.
        """
        if dt is None:
            # Read current datetime using write-then-read method (more reliable)
            try:
                self.i2c.writeto(self.addr, b'\x00')  # Set register pointer to 0x00
                buf = self.i2c.readfrom(self.addr, 7)  # Read 7 bytes
                if buf is None:
                    return None
                second = self._bcd2dec(buf[0] & 0x7F)
                minute = self._bcd2dec(buf[1] & 0x7F)
                hour = self._bcd2dec(buf[2] & 0x3F)  # 24-hour mode
                weekday = self._bcd2dec(buf[3] & 0x07) - 1  # DS323x uses 1-7, we use 0-6
                day = self._bcd2dec(buf[4] & 0x3F)
                month = self._bcd2dec(buf[5] & 0x1F)
                year = self._bcd2dec(buf[6]) + 2000
                return (year, month, day, weekday, hour, minute, second, 0)
            except (OSError, TypeError):
                # I2C communication failed
                return None
        else:
            # Set datetime
            year, month, day, weekday, hour, minute, second, subsecond = dt
            buf = bytearray(8)
            buf[0] = 0x00  # Register address
            buf[1] = self._dec2bcd(second)
            buf[2] = self._dec2bcd(minute)
            buf[3] = self._dec2bcd(hour)  # 24-hour mode
            buf[4] = self._dec2bcd(weekday + 1)  # DS323x uses 1-7
            buf[5] = self._dec2bcd(day)
            buf[6] = self._dec2bcd(month)
            buf[7] = self._dec2bcd(year - 2000)
            self.i2c.writeto(self.addr, buf)

    def temperature(self):
        """Read temperature in Celsius from built-in sensor"""
        self.i2c.writeto(self.addr, b'\x11')  # Set register pointer to 0x11
        buf = self.i2c.readfrom(self.addr, 2)  # Read 2 bytes
        temp = buf[0] + (buf[1] >> 6) * 0.25
        if buf[0] & 0x80:  # negative temperature
            temp = temp - 256
        return temp

    def get_time_str(self):
        """Return formatted time string: YYYY-MM-DD HH:MM:SS"""
        dt = self.datetime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            dt[0], dt[1], dt[2], dt[4], dt[5], dt[6])
    
    # DS3232 SRAM functions (battery-backed memory)
    
    def write_sram(self, address, data):
        """
        Write data to SRAM (DS3232 only).
        
        Args:
            address: SRAM address (0x14-0xFF)
            data: bytes or bytearray to write
        
        Returns:
            True if successful, False otherwise
        """
        if not self.has_sram:
            print("Error: SRAM not available (DS3231 doesn't have SRAM)")
            return False
        
        if address < self.SRAM_START or address > self.SRAM_END:
            print(f"Error: SRAM address must be 0x{self.SRAM_START:02X}-0x{self.SRAM_END:02X}")
            return False
        
        if address + len(data) - 1 > self.SRAM_END:
            print(f"Error: Data exceeds SRAM bounds (max {self.SRAM_SIZE} bytes)")
            return False
        
        try:
            # Write address + data
            buf = bytearray([address]) + bytearray(data)
            self.i2c.writeto(self.addr, buf)
            return True
        except Exception as e:
            print(f"SRAM write failed: {e}")
            return False
    
    def read_sram(self, address, length):
        """
        Read data from SRAM (DS3232 only).
        
        Args:
            address: SRAM address (0x14-0xFF)
            length: Number of bytes to read
        
        Returns:
            bytearray of data, or None on error
        """
        if not self.has_sram:
            print("Error: SRAM not available (DS3231 doesn't have SRAM)")
            return None
        
        if address < self.SRAM_START or address > self.SRAM_END:
            print(f"Error: SRAM address must be 0x{self.SRAM_START:02X}-0x{self.SRAM_END:02X}")
            return None
        
        if address + length - 1 > self.SRAM_END:
            print(f"Error: Read exceeds SRAM bounds (max {self.SRAM_SIZE} bytes)")
            return None
        
        try:
            # Set address pointer
            self.i2c.writeto(self.addr, bytes([address]))
            # Read data
            return self.i2c.readfrom(self.addr, length)
        except Exception as e:
            print(f"SRAM read failed: {e}")
            return None
    
    def clear_sram(self):
        """
        Clear all SRAM (DS3232 only).
        Writes zeros to entire SRAM range.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.has_sram:
            print("Error: SRAM not available (DS3231 doesn't have SRAM)")
            return False
        
        try:
            # Write zeros to all SRAM
            zeros = bytearray(self.SRAM_SIZE)
            return self.write_sram(self.SRAM_START, zeros)
        except Exception as e:
            print(f"SRAM clear failed: {e}")
            return False


# Backward compatibility aliases
#DS3231 = DS323x  # DS3231 is just DS323x with has_sram=False
#DS3232 = DS323x  # DS3232 is just DS323x with has_sram=True
class DS3231(DS323x):
    def __init__(self, *args, **kw):
        kw['has_sram'] = False
        super().__init__(*args, **kw)
class DS3232(DS323x):
    def __init__(self, *args, **kw):
        kw['has_sram'] = True
        super().__init__(*args, **kw)
