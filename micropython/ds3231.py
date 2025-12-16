# Simple DS3231 RTC driver for MicroPython
# Based on DS3231 datasheet and community implementations

import time

class DS3231:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
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
        """
        if dt is None:
            # Read current datetime using write-then-read method (more reliable)
            self.i2c.writeto(self.addr, b'\x00')  # Set register pointer to 0x00
            buf = self.i2c.readfrom(self.addr, 7)  # Read 7 bytes
            second = self._bcd2dec(buf[0] & 0x7F)
            minute = self._bcd2dec(buf[1] & 0x7F)
            hour = self._bcd2dec(buf[2] & 0x3F)  # 24-hour mode
            weekday = self._bcd2dec(buf[3] & 0x07) - 1  # DS3231 uses 1-7, we use 0-6
            day = self._bcd2dec(buf[4] & 0x3F)
            month = self._bcd2dec(buf[5] & 0x1F)
            year = self._bcd2dec(buf[6]) + 2000
            return (year, month, day, weekday, hour, minute, second, 0)
        else:
            # Set datetime
            year, month, day, weekday, hour, minute, second, subsecond = dt
            buf = bytearray(8)
            buf[0] = 0x00  # Register address
            buf[1] = self._dec2bcd(second)
            buf[2] = self._dec2bcd(minute)
            buf[3] = self._dec2bcd(hour)  # 24-hour mode
            buf[4] = self._dec2bcd(weekday + 1)  # DS3231 uses 1-7
            buf[5] = self._dec2bcd(day)
            buf[6] = self._dec2bcd(month)
            buf[7] = self._dec2bcd(year - 2000)
            self.i2c.writeto(self.addr, buf)

    def temperature(self):
        """Read temperature in Celsius from DS3231's built-in sensor"""
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
