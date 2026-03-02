"""
SH1106 OLED Driver for MicroPython
==================================
I2C driver for SH1106 128x64 OLED displays.
"""

import framebuf


class SH1106_I2C:
    """I2C driver for SH1106 OLED display."""
    
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.buffer = bytearray(width * height // 8)
        self.fb = framebuf.FrameBuffer(self.buffer, width, height, framebuf.MONO_VLSB)
        
        # Initialize display
        self._init_display()
        self.is_sleeping = False
        self.fill(0)
        self.show()
    
    def _init_display(self):
        """Send initialization commands to SH1106."""
        cmds = [
            0xAE,        # Display OFF
            0x20, 0x00,  # Memory addressing mode
            0x40,        # Start line = 0
            0xA1,        # Segment remap
            0xC8,        # COM output scan direction
            0x81, 0x7F,  # Contrast
            0xA6,        # Normal display (not inverted)
            0xA8, 0x3F,  # Multiplex ratio (64-1)
            0xAD, 0x8B,  # DC-DC enable
            0xD3, 0x00,  # Display offset = 0
            0xD5, 0x80,  # Clock divide ratio
            0xD9, 0x22,  # Pre-charge period
            0xDA, 0x12,  # COM pins hardware config
            0xDB, 0x35,  # VCOMH deselect level
            0xAF,        # Display ON
        ]
        for c in cmds:
            self.i2c.writeto(self.addr, bytes([0x00, c]))
    
    def fill(self, color):
        """Fill display with color (0=black, 1=white)."""
        self.fb.fill(color)
    
    def text(self, string, x, y, color=1):
        """Draw text at position."""
        self.fb.text(string, x, y, color)
    
    def pixel(self, x, y, color=1):
        """Set a pixel."""
        self.fb.pixel(x, y, color)
    
    def hline(self, x, y, w, color=1):
        """Draw horizontal line."""
        self.fb.hline(x, y, w, color)
    
    def vline(self, x, y, h, color=1):
        """Draw vertical line."""
        self.fb.vline(x, y, h, color)
    
    def rect(self, x, y, w, h, color=1):
        """Draw rectangle outline."""
        self.fb.rect(x, y, w, h, color)
    
    def fill_rect(self, x, y, w, h, color=1):
        """Draw filled rectangle."""
        self.fb.fill_rect(x, y, w, h, color)
    
    def line(self, x1, y1, x2, y2, color=1):
        """Draw line."""
        self.fb.line(x1, y1, x2, y2, color)
    
    def degree(self, x, y, color=1):
        """Draw a small 2x2 circle for the degree symbol."""
        self.pixel(x, y, color)
        self.pixel(x+1, y, color)
        self.pixel(x, y+1, color)
        self.pixel(x+1, y+1, color)
    
    def show(self):
        """Push buffer to display."""
        for page in range(self.height // 8):
            # Set page address and column (SH1106 has 2-pixel offset)
            self.i2c.writeto(self.addr, bytes([0x00, 0xB0 + page, 0x02, 0x10]))
            # Write page data
            start = self.width * page
            end = start + self.width
            self.i2c.writeto(self.addr, bytes([0x40]) + self.buffer[start:end])
    
    def sleep(self):
        """Turn display OFF (panel power retained, no burn-in)."""
        self.i2c.writeto(self.addr, bytes([0x00, 0xAE]))
        self.is_sleeping = True

    def wake(self):
        """Turn display ON."""
        self.i2c.writeto(self.addr, bytes([0x00, 0xAF]))
        self.is_sleeping = False
