"""
RotaryEncoder - Simple rotary encoder handler for TDD
======================================================
Minimal implementation to pass TDD tests.
Uses IRQ-based state machine for reliable detent counting.
"""

from machine import Pin


class RotaryEncoder:
    """Rotary encoder with push button support."""
    
    def __init__(self, pin_a, pin_b, pin_btn=None):
        """
        Initialize rotary encoder.
        
        Args:
            pin_a: GPIO number for encoder A signal
            pin_b: GPIO number for encoder B signal  
            pin_btn: GPIO number for button (optional)
        """
        self._pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self._pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self._pin_btn = Pin(pin_btn, Pin.IN, Pin.PULL_UP) if pin_btn is not None else None
        
        self._value = 0
        self._last_a = self._pin_a.value()
        
        # Set up IRQ on pin A for rotation detection
        self._pin_a.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._rotation_handler)
    
    def _rotation_handler(self, pin):
        """Handle rotation interrupt."""
        a = self._pin_a.value()
        b = self._pin_b.value()
        
        # Only count on A transitions
        if a != self._last_a:
            # Determine direction based on B state at A transition
            if a == 0:  # Falling edge of A
                if b == 1:
                    self._value += 1
                else:
                    self._value -= 1
            self._last_a = a
    
    @property
    def value(self):
        """Current encoder value (cumulative position)."""
        return self._value
    
    @value.setter
    def value(self, val):
        """Set encoder value."""
        self._value = val
    
    def reset(self):
        """Reset encoder value to zero."""
        self._value = 0
    
    @property
    def button_pressed(self):
        """Check if button is currently pressed (active low)."""
        if self._pin_btn is None:
            return False
        return self._pin_btn.value() == 0
    
    def deinit(self):
        """Disable IRQ and clean up."""
        self._pin_a.irq(handler=None)
