"""
Input Utilities for Orbigator
Centralized input handling policies and utilities.
"""

# Global Encoder Policy
# ---------------------
# CW (Clockwise) rotation = +1 = Increase value / Navigate down
# CCW (Counter-clockwise) = -1 = Decrease value / Navigate up
#
# This policy is applied consistently across ALL modes to prevent
# "feels backwards in this screen" bugs.

import time

class NudgeManager:
    """
    Manages velocity-based acceleration for encoder rotation.
    Allows for fine-grained 0.1° nudges while supporting large 180° moves.
    """
    def __init__(self, fine_step=0.1, medium_step=1.0, coarse_step=10.0):
        self.fine_step = fine_step
        self.medium_step = medium_step
        self.coarse_step = coarse_step
        self.last_time = time.ticks_ms()
        
    def get_delta(self, raw_delta):
        """
        Calculate accelerated delta based on rotation speed.
        """
        if raw_delta == 0:
            return 0.0
            
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_time)
        self.last_time = now
        
        # Absolute delta to handle CW/CCW
        abs_raw = abs(raw_delta)
        # Compensate for multi-click batches (if delta > 1, dt per click is smaller)
        dt_per_click = dt / abs_raw
        
        # Velocity thresholds (ms per click)
        if dt_per_click > 120: # Slow turn
            step = self.fine_step
        elif dt_per_click > 40: # Normal turn
            step = self.medium_step
        else: # Fast spin
            step = self.coarse_step
            
        return raw_delta * step

def normalize_encoder_delta(raw_delta):
    """
    Normalize encoder delta according to global policy.
    
    Args:
        raw_delta: Raw encoder delta from ISR (positive = CW, negative = CCW)
    
    Returns:
        Normalized delta: +1 for CW (increase/down), -1 for CCW (decrease/up)
    
    Note: If your encoder hardware is reversed, invert the sign here
    rather than in individual mode handlers.
    """
    # Current hardware: CW = positive delta
    # Policy: CW = increase/down = +1
    # Therefore: no inversion needed
    return raw_delta
