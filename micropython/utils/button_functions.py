"""
Button polling functions for Orbigator UI
Add these functions to orbigator.py after the poll_button() function
"""

def poll_back_button():
    """Check for back button press (non-blocking, debounced)."""
    global back_btn_last, last_back_time, current_state
    
    now = time.ticks_ms()
    current = BACK_BTN.value()
    
    # Detect falling edge (button pressed)
    if current == 0 and back_btn_last == 1:
        if time.ticks_diff(now, last_back_time) > DEBOUNCE_MS:
            last_back_time = now
            # Handle back button action based on current state
            if current_state > 0:  # Not in main menu
                current_state = 0  # Return to main menu
                print("← Back to Main Menu")
                back_btn_last = current
                return True
    
    back_btn_last = current
    return False

def poll_confirm_button():
    """Check for confirm button press (non-blocking, debounced)."""
    global confirm_btn_last, last_confirm_time, current_state
    
    now = time.ticks_ms()
    current = CONFIRM_BTN.value()
    
    # Detect falling edge (button pressed)
    if current == 0 and confirm_btn_last == 1:
        if time.ticks_diff(now, last_confirm_time) > DEBOUNCE_MS:
            last_confirm_time = now
            # Handle confirm button action based on current state
            print("✓ Confirm pressed")
            confirm_btn_last = current
            return True
    
    confirm_btn_last = current
    return False
