"""
OledDisplay - Simple OLED display wrapper for TDD
==================================================
Auto-detects SH1106 or SSD1306 displays.
"""

from machine import Pin, I2C

OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_ADDR = 0x3C


class OledDisplay:
    """Simple wrapper for SH1106/SSD1306 OLED display."""
    
    def __init__(self, i2c, addr=OLED_ADDR):
        self.i2c = i2c
        self.addr = addr
        self._driver = None
        self._display = None
        self._init_display()
    
    def _init_display(self):
        """Auto-detect and initialize SH1106 or SSD1306 driver."""
        # Try SH1106 first (more common for generic 1.3" OLEDs)
        try:
            from sh1106 import SH1106_I2C
            self._display = SH1106_I2C(OLED_WIDTH, OLED_HEIGHT, self.i2c, addr=self.addr)
            self._driver = "SH1106"
            return
        except ImportError:
            pass
        
        # Fallback to SSD1306
        try:
            from ssd1306 import SSD1306_I2C
            self._display = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, self.i2c, addr=self.addr)
            self._driver = "SSD1306"
            return
        except ImportError:
            pass
        
        raise RuntimeError("No OLED driver found (sh1106 or ssd1306)")
    
    @property
    def driver(self):
        """Return the name of the active driver."""
        return self._driver
    
    def clear(self):
        """Clear the display buffer."""
        self._display.fill(0)
    
    def fill(self, color):
        """Fill display with color (0=black, 1=white)."""
        self._display.fill(color)
    
    def text(self, string, x, y, color=1):
        """Draw text at position."""
        self._display.text(string, x, y, color)
    
    def show(self):
        """Push buffer to display."""
        self._display.show()
    
    def pixel(self, x, y, color=1):
        """Set a pixel."""
        self._display.pixel(x, y, color)
    
    def hline(self, x, y, w, color=1):
        """Draw horizontal line."""
        self._display.hline(x, y, w, color)
    
    def vline(self, x, y, h, color=1):
        """Draw vertical line."""
        self._display.vline(x, y, h, color)
    
    def rect(self, x, y, w, h, color=1):
        """Draw rectangle outline."""
        self._display.rect(x, y, w, h, color)
    
    def fill_rect(self, x, y, w, h, color=1):
        """Draw filled rectangle."""
        self._display.fill_rect(x, y, w, h, color)
