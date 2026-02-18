"""
Persistence Interface
=====================
Abstract base class and concrete implementations for data persistence.
"""

class Persist:
    """Abstract base class for persistent storage."""
    
    def __init__(self, unique_id):
        self.unique_id = unique_id

    def read(self, offset, length):
        """Read bytes from storage."""
        raise NotImplementedError

    def write(self, offset, payload):
        """Write bytes to storage. Length matches payload."""
        raise NotImplementedError


class SRAM(Persist):
    """Concrete implementation using DS323x RTC SRAM."""
    
    def __init__(self, rtc, base_address, size):
        unique_id = f"DS3232SRAM_{base_address}_{size}"
        super().__init__(unique_id)
        self.rtc = rtc
        self._base = base_address
        self._size = size
        
    def read(self, offset, length):
        if offset + length > self._size:
            raise ValueError(f"Read overflow: {offset}+{length} > {self._size}")
        return self.rtc.read_sram(self._base + offset, length)
        
    def write(self, offset, payload):
        length = len(payload)
        if offset + length > self._size:
            raise ValueError(f"Write overflow: {offset}+{length} > {self._size}")
        
        if self.rtc.write_sram(self._base + offset, payload):
            return length
        return 0
