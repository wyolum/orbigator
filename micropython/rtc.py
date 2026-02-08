"""
RTC - Simple DS3232 Real-Time Clock wrapper for TDD
====================================================
Minimal implementation to pass TDD tests.
Wraps DS323x driver with SRAM support enabled.
"""

from machine import Pin, I2C

RTC_ADDR = 0x68


class RTC:
    """Simple wrapper for DS3232 RTC with SRAM support."""
    
    # SRAM address range
    SRAM_START = 0x14
    SRAM_END = 0xFF
    
    def __init__(self, i2c, addr=RTC_ADDR):
        """
        Initialize DS3232 RTC.
        
        Args:
            i2c: I2C bus instance
            addr: I2C address (default 0x68)
        """
        self.i2c = i2c
        self.addr = addr
    
    def _bcd2dec(self, bcd):
        """Convert BCD to decimal."""
        return (bcd >> 4) * 10 + (bcd & 0x0F)
    
    def _dec2bcd(self, dec):
        """Convert decimal to BCD."""
        return ((dec // 10) << 4) + (dec % 10)
    
    def datetime(self, dt=None):
        """
        Get or set datetime.
        
        Args:
            dt: If None, read current time. Otherwise set time.
                Format: (year, month, day, weekday, hour, minute, second, subsecond)
                weekday: 0=Monday, 6=Sunday
        
        Returns:
            8-tuple of datetime values, or None on error
        """
        if dt is None:
            # Read current datetime
            try:
                self.i2c.writeto(self.addr, b'\x00')
                buf = self.i2c.readfrom(self.addr, 7)
                if buf is None:
                    return None
                second = self._bcd2dec(buf[0] & 0x7F)
                minute = self._bcd2dec(buf[1] & 0x7F)
                hour = self._bcd2dec(buf[2] & 0x3F)
                weekday = self._bcd2dec(buf[3] & 0x07) - 1
                day = self._bcd2dec(buf[4] & 0x3F)
                month = self._bcd2dec(buf[5] & 0x1F)
                year = self._bcd2dec(buf[6]) + 2000
                return (year, month, day, weekday, hour, minute, second, 0)
            except (OSError, TypeError):
                return None
        else:
            # Set datetime
            year, month, day, weekday, hour, minute, second, subsecond = dt
            buf = bytearray(8)
            buf[0] = 0x00  # Register address
            buf[1] = self._dec2bcd(second)
            buf[2] = self._dec2bcd(minute)
            buf[3] = self._dec2bcd(hour)
            buf[4] = self._dec2bcd(weekday + 1)
            buf[5] = self._dec2bcd(day)
            buf[6] = self._dec2bcd(month)
            buf[7] = self._dec2bcd(year - 2000)
            self.i2c.writeto(self.addr, buf)
    
    def read_sram(self, address, length):
        """
        Read data from SRAM.
        
        Args:
            address: SRAM address (0x14-0xFF)
            length: Number of bytes to read
        
        Returns:
            bytearray of data, or None on error
        """
        if address < self.SRAM_START or address > self.SRAM_END:
            return None
        if address + length - 1 > self.SRAM_END:
            return None
        
        try:
            self.i2c.writeto(self.addr, bytes([address]))
            return self.i2c.readfrom(self.addr, length)
        except Exception:
            return None
    
    def write_sram(self, address, data):
        """
        Write data to SRAM.
        
        Args:
            address: SRAM address (0x14-0xFF)
            data: bytes or bytearray to write
        
        Returns:
            True if successful, False otherwise
        """
        if address < self.SRAM_START or address > self.SRAM_END:
            return False
        if address + len(data) - 1 > self.SRAM_END:
            return False
        
        try:
            buf = bytearray([address]) + bytearray(data)
            self.i2c.writeto(self.addr, buf)
            return True
        except Exception:
            return False
