# Mock DS323x RTC driver for MicroPython
# Simulates DS3231 and DS3232 without hardware
# Used for testing or running without RTC module

import time

class MockDS323x:
    """
    Mock Driver for DS3231 and DS3232 Real-Time Clock modules.
    Simulates checking time (via system time) and SRAM storage (in-memory).
    """
    
    # SRAM address range for DS3232
    SRAM_START = 0x14  # First SRAM address
    SRAM_END = 0xFF    # Last SRAM address
    SRAM_SIZE = 236    # Total SRAM bytes (0xFF - 0x14 + 1)
    
    def __init__(self, i2c=None, addr=0x68, has_sram=False):
        """
        Initialize Mock DS323x RTC.
        """
        self.i2c = i2c # Ignored
        self.addr = addr
        self.has_sram = has_sram
        self._sram = bytearray(self.SRAM_SIZE)
        print(f"[MockRTC] Initialized at 0x{addr:02X} (SRAM={has_sram})")

    def datetime(self, dt=None):
        """
        Get or set datetime.
        Get: Returns system time (localtime) as tuple.
        Set: Updates internal offset (simulated).
        """
        if dt is None:
            # Return current system time
            t = time.localtime()
            # t is (year, month, md, hour, min, sec, wday, yday)
            # DS323x format: (year, month, day, weekday, hour, minute, second, subsecond)
            # weekday mapping: system 0=Mon -> DS 0=Mon (consistent in our wrapper)
            return (t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0)
        else:
            # Set datetime (Mock: just print it, or maybe set system time?)
            # Setting system time in MicroPython usually requires RTC/machine.RTC
            print(f"[MockRTC] Setting time to: {dt}")
            # For a mock, we might not want to actully change system time logic
            return None

    def temperature(self):
        """Return dummy temperature"""
        return 25.0
    
    def get_time_str(self):
        """Return formatted time string: YYYY-MM-DD HH:MM:SS"""
        dt = self.datetime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            dt[0], dt[1], dt[2], dt[4], dt[5], dt[6])
    
    # --- SRAM ---
    
    def write_sram(self, address, data):
        if not self.has_sram:
            print("[MockRTC] Error: SRAM not available")
            return False
        
        if address < self.SRAM_START or address > self.SRAM_END:
            print(f"[MockRTC] Error: SRAM address OOB")
            return False
        
        offset = address - self.SRAM_START
        if offset + len(data) > self.SRAM_SIZE:
             print(f"[MockRTC] Error: Data too long")
             return False
             
        # Write to memory
        self._sram[offset:offset+len(data)] = data
        return True
    
    def read_sram(self, address, length):
        if not self.has_sram:
            print("[MockRTC] Error: SRAM not available")
            return None
            
        if address < self.SRAM_START or address > self.SRAM_END:
            print(f"[MockRTC] Error: SRAM address OOB")
            return None
            
        offset = address - self.SRAM_START
        if offset + length > self.SRAM_SIZE:
             print(f"[MockRTC] Error: Read too long")
             return None
             
        return self._sram[offset:offset+length]
    
    def clear_sram(self):
        if not self.has_sram: return False
        self._sram = bytearray(self.SRAM_SIZE)
        return True


# Aliases
class MockDS3231(MockDS323x):
    def __init__(self, *args, **kw):
        kw['has_sram'] = False
        super().__init__(*args, **kw)

class MockDS3232(MockDS323x):
    def __init__(self, *args, **kw):
        kw['has_sram'] = True
        super().__init__(*args, **kw)
