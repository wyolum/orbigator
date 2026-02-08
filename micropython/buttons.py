"""
Buttons - Simple button handler for TDD
========================================
Minimal implementation for Back and Confirm buttons.
"""

from machine import Pin


class Buttons:
    """Handler for Back and Confirm buttons with debounce."""
    
    def __init__(self, back_pin, confirm_pin):
        """
        Initialize buttons.
        
        Args:
            back_pin: GPIO number for Back button
            confirm_pin: GPIO number for Confirm button
        """
        self._back = Pin(back_pin, Pin.IN, Pin.PULL_UP)
        self._confirm = Pin(confirm_pin, Pin.IN, Pin.PULL_UP)
    
    @property
    def back_pressed(self):
        """Check if Back button is currently pressed (active low)."""
        return self._back.value() == 0
    
    @property
    def confirm_pressed(self):
        """Check if Confirm button is currently pressed (active low)."""
        return self._confirm.value() == 0
