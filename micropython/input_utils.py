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
