"""
NTP Time Synchronization for Orbigator
This module is isolated to prevent network imports on non-WiFi hardware.
"""

import time
import machine
import orb_utils as utils
import orb_globals as g

def sync_ntp(display=None):
    """
    Attempts to synchronize the system time and RTC via NTP.
    Assumes Wi-Fi is already connected.
    """
    try:
        import ntptime
        print("NTP Sync: Settling network...")
        time.sleep(2) # Give stack a moment
        
        sync_done = False
        ntptime.host = "pool.ntp.org" 
        
        for attempt in range(5):
            try:
                print(f"  NTP Sync attempt {attempt+1}...")
                if display:
                    display.fill(0)
                    display.text("Time Sync", 0, 0)
                    display.text(f"Attempt {attempt+1}...", 0, 16)
                    display.show()
                
                before_sync = time.time()
                ntptime.settime()
                after_sync = time.time()
                
                # Update System RTC and Software Clock
                t = machine.RTC().datetime()
                # t format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
                utils.set_datetime(t[0], t[1], t[2], t[4], t[5], t[6], g.rtc)
                
                correction = after_sync - before_sync
                print(f"  ✓ NTP Sync OK. RTC Correction: {correction:+.1f}s")
                return True
            except Exception as e:
                print(f"  ✗ Attempt {attempt+1} failed: {e}")
                time.sleep(2)
        
        print("  ✗ NTP Sync permanently failed.")
        return False
    except ImportError:
        print("  ✗ ntptime module not found.")
        return False
    except Exception as e:
        print(f"  ✗ NTP Unexpected error: {e}")
        return False
