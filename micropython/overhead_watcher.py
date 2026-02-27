"""
overhead_watcher.py - Satellite Horizon State Machine
======================================================
Monitors the dot_up() value from ObserverFrame and triggers
a display wake event when the satellite rises above the horizon.

Hysteresis prevents flicker near the boundary. The hot-loop cost
is just one float comparison per tick.

The alert stays active for the entire duration the satellite is
above the horizon (dynamic pass length — works for LEO, MEO, GEO).
"""

import time

# --- Tunable constants ---
HORIZON_ON_DOT  = 0.0     # trigger when dot crosses zero (exact horizon)
HORIZON_OFF_DOT = -0.05   # hysteresis: don't disarm until dot clearly below
DWELL_MS        = 3000    # must be above horizon this long before alert fires

# States
_BELOW   = 0
_DWELL   = 1   # candidates: above ON but not yet confirmed
_ABOVE   = 2   # alert active


class OverheadWatcher:
    """
    State machine tracking whether the satellite is above the horizon.

    Usage (every tracking tick):
        watcher.update(dot, now_ms)
        if watcher.is_alert_active():
            ...show radar...
        if watcher.pass_just_started:
            ...compute predicted track...
    """

    def __init__(self):
        self._state           = _BELOW
        self._dwell_start     = 0
        self.pass_just_started = False   # True for exactly one tick after DWELL→ABOVE

    # ------------------------------------------------------------------
    def update(self, dot_up, now_ms):
        """Call once per tracking tick with the dot_up() result."""

        # Reset one-shot flag at the top of every tick
        self.pass_just_started = False

        if self._state == _BELOW:
            if dot_up > HORIZON_ON_DOT:
                self._state = _DWELL
                self._dwell_start = now_ms

        elif self._state == _DWELL:
            if dot_up <= HORIZON_ON_DOT:
                # Dropped back below before dwell completed - reset
                self._state = _BELOW
            elif time.ticks_diff(now_ms, self._dwell_start) >= DWELL_MS:
                # Confirmed above horizon - fire alert
                self._state = _ABOVE
                self.pass_just_started = True
                print(f"OVERHEAD ALERT: satellite above horizon! dot={dot_up:.3f}")

        elif self._state == _ABOVE:
            # Disarm once satellite clearly below (hysteresis)
            if dot_up < HORIZON_OFF_DOT:
                self._state = _BELOW
                print("OVERHEAD: satellite set below horizon.")

    # ------------------------------------------------------------------
    def is_alert_active(self):
        """True while the alert display should be shown."""
        return self._state == _ABOVE
