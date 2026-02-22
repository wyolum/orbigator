"""
Orbigator UI Modes
Mode-based architecture for clean UI state management
"""

import orb_globals as g
import orb_utils as utils
import input_utils
import time
import math

# SGP4 imported locally in SGP4Mode
import propagate


class Mode:
    """Base class for UI modes."""
    def __init__(self):
        self.debug_counter = 0
    
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        pass
    
    def on_encoder_press(self):
        self.on_confirm()
    
    def on_confirm(self):
        pass
    
    def on_back(self):
        pass
    
    def update(self, dt):
        pass
    
    def render(self, disp):
        pass
    
    def enter(self):
        pass
    
    def exit(self):
        pass

    def on_pause(self):
        """Called when a new mode is pushed on top of this one."""
        pass

    def on_resume(self):
        """Called when the mode on top is popped."""
        pass


class ModeStack:
    """
    Manages a stack of Mode objects.
    The top of the stack is the active mode.
    """
    def __init__(self):
        self.stack = []
    
    def push(self, mode):
        if self.stack:
            self.stack[-1].on_pause()
        self.stack.append(mode)
        mode.enter()
        print(f"UI Push: {type(mode).__name__} (Depth: {len(self.stack)})")
        
    def pop(self):
        if not self.stack: return
        
        # Don't pop the root mode (TrackMode/OrbitMode)
        if len(self.stack) == 1:
            print("UI Pop ignored: Cannot pop root mode.")
            return

        mode = self.stack.pop()
        mode.exit()
        print(f"UI Pop: {type(mode).__name__} (New Depth: {len(self.stack)})")
        
        if self.stack:
            self.stack[-1].on_resume()
            
    def replace(self, mode):
        """Replace current mode (pop + push)."""
        if self.stack:
            old = self.stack.pop()
            old.exit()
        self.stack.append(mode)
        mode.enter()
        print(f"UI Replace: {type(mode).__name__}")
        
    def set_root(self, mode):
        """Clear stack and set new root mode."""
        # Pop everything down to the last element (which pop() protects)
        while len(self.stack) > 1:
            self.pop()
            
        # Manually remove the last element if it exists
        if self.stack:
             old = self.stack.pop()
             old.exit()

        # Stack is empty
        self.stack.append(mode)
        mode.enter()
        print(f"UI Root Set: {type(mode).__name__}")
        
    def handle_input(self, event_type, value=None):
        if not self.stack: return
        
        active = self.stack[-1]
        
        # --- OLED Wake on Input ---
        now_ms = time.ticks_ms()
        g.last_input_ticks = now_ms
        if g.disp and hasattr(g.disp, 'is_sleeping') and g.disp.is_sleeping:
            try:
                g.disp.wake()
            except:
                pass
            return  # Swallow event: first touch only wakes display, doesn't change state
        
        if event_type == "ENC_ROTATE":
            active.on_encoder_rotate(value)
        elif event_type == "ENC_PRESS":
            # Some modes handle press differently, defaults to confirm or toggle
            active.on_encoder_press()
        elif event_type == "CONFIRM":
            active.on_confirm()
        elif event_type == "BACK":
            active.on_back()
            
    def update(self, dt):
        # 1. Always update Root Mode (Physics/Motors) if it exists and isn't active
        if len(self.stack) > 1:
             # Assuming root is index 0
             # We need a standard contract for "Update Physics vs UI"
             # For now, let's just assume Root needs a tick if it's OrbitMode/SGP4Mode
             root = self.stack[0]
             if hasattr(root, "update_background"):
                 root.update_background(dt)
        
        # 2. Update Active Mode (UI)
        if self.stack:
            self.stack[-1].update(dt)
            
    def render(self, disp):
        # --- OLED Idle Sleep ---
        if g.oled_timeout_ms > 0:
            now_ms = time.ticks_ms()
            # Bootstrap: start the idle timer on first render
            if g.last_input_ticks == 0:
                g.last_input_ticks = now_ms
            idle_ms = time.ticks_diff(now_ms, g.last_input_ticks)
            if idle_ms >= g.oled_timeout_ms:
                # Time to sleep
                if disp and hasattr(disp, 'is_sleeping') and not disp.is_sleeping:
                    try:
                        disp.fill(0)
                        disp.show()
                        disp.sleep()
                    except Exception as e:
                        print(f"OLED sleep error: {e}")
                return  # Skip render while sleeping
        
        # Wake if needed (e.g. timeout was just changed to Never, or input woke us)
        if disp and hasattr(disp, 'is_sleeping') and disp.is_sleeping:
            try:
                disp.wake()
            except:
                pass
        
        if self.stack:
            self.stack[-1].render(disp)
            
    @property
    def current(self):
        return self.stack[-1] if self.stack else None


class MenuMode(Mode):
    """Main menu mode."""
    
    def __init__(self):
        super().__init__()
        self.selection = 0
        # Build menu items based on capabilities (R5)
        self.items = ["Orbit!", "Set Period", "Settings"]
        
        if g.caps.has_wifi:
            # Insert Track Satellite after Orbit!
            self.items.insert(1, "Track Satellite")
            
            if g.caps.has_web_server:
                # Add dynamic web server toggle
                web_label = "Halt Web Svc" if g.web_server_enabled else "Start Web Svc"
                self.items.append(web_label)
            
        # Default selection based on current mode to prevent accidental switching
        if g.current_mode_id == "SGP4":
            # Find index of Track Satellite
            for i, item in enumerate(self.items):
                if item == "Track Satellite":
                    self.selection = i
                    break
        elif g.current_mode_id == "ORBIT":
            # Default to 0 (Orbit!)
            self.selection = 0
            
    def enter(self):
        g.current_mode_id = "MENU"
    
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        # Default: CW (delta > 0) = Move Down (selection increases)
        move = 1 if delta > 0 else -1 if delta < 0 else 0
        self.selection = (self.selection + move) % len(self.items)
        print(f"Menu: {self.items[self.selection]}")
    
    def on_confirm(self):
        item = self.items[self.selection]
        if item == "Orbit!":
            g.ui.set_root(OrbitMode())
        elif item == "Track Satellite":
            g.ui.set_root(SGP4Mode())
        elif item == "Set Period":
            g.ui.push(PeriodEditorMode())
        elif item == "Settings":
            g.ui.push(SettingsMode())
        elif item == "Halt Web Svc":
            print("Halting Web Server...")
            g.web_server_enabled = False
            self.items[self.selection] = "Start Web Svc"
        elif item == "Start Web Svc":
            print("Starting Web Server...")
            g.web_server_enabled = True
            utils.start_web_server_thread()
            self.items[self.selection] = "Halt Web Svc"
        
    def on_back(self):
        g.ui.pop()
    
    def render(self, disp):
        disp.fill(0)
        disp.text("MAIN MENU", 0, 0)
        
        # Page size: 4 items (16 to 64px)
        page_size = 4
        start_idx = max(0, min(self.selection - page_size // 2, len(self.items) - page_size))
        
        # Scroll indicators
        if start_idx > 0: disp.text("^", 120, 16)
        if start_idx + page_size < len(self.items): disp.text("v", 120, 52)

        for i in range(start_idx, min(start_idx + page_size, len(self.items))):
            item = self.items[i]
            prefix = ">" if i == self.selection else " "
            y = 16 + (i - start_idx) * 12
            disp.text(f"{prefix} {item}", 0, y)
        
        disp.show()


class OrbitMode(Mode):
    """Orbital motion mode."""
    
    def __init__(self):
        super().__init__()
        self.nudge_target = 0
        self.initialized = False
        self.propagator = None
        self.last_command_ticks = 0
        self.last_target_aov = 0.0
        self.last_target_eqx = 0.0
        self.last_unix = 0  # Cache for propagator math
        self.tracking = True # Toggle with Confirm button
        self.last_aov_angle = 0.0
        self.last_eqx_angle = 0.0
        self.nudge_manager = input_utils.NudgeManager(fine_step=1.0, medium_step=1.0, coarse_step=1.0)
        self.last_aov_wrapped = 0.0  # Track wrapped AoV for south point detection
    
    def enter(self) :
        """Initialize orbital tracking and catch up if needed."""
        g.current_mode_id = "ORBIT"
        
        # Speed limits are set in orbigator.py from config.
        # Do not override them here unless we want specific "tracking" speeds.
        # User requested faster speeds, so we respect the config.

            
        # Check if we are resuming an active session (Menu -> Orbit) or starting fresh (Boot -> Orbit)
        # Absolute Time Propagation Strategy
        # The simulated orbit is defined to start at Epoch = 0 (1970).
        # Position is a pure function of current time.
        # This eliminates drift, catch-up logic, and state saving needs.
        
        g.run_start_time = 0  # Fixed Epoch
        g.run_start_ticks = 0 # Not used for absolute mode
        
        aov_rate, eqx_rate_sec, eqx_rate_day, period_min = utils.compute_motor_rates(g.orbital_altitude_km)
        g.aov_rate_deg_sec = aov_rate
        g.eqx_rate_deg_sec = eqx_rate_sec
        g.eqx_rate_deg_day = eqx_rate_day
        g.orbital_period_min = period_min
        
        # Initialize propagator with Start Time = 0
        # This means the satellite has been orbiting since 1970.
        self.propagator = propagate.KeplerJ2(
            g.orbital_altitude_km, g.orbital_inclination_deg, 
            g.orbital_eccentricity, g.orbital_periapsis_deg,
            0.0, 0.0, 0.0 # Start Phase 0, Start Time 0
        )
        self.initialized = True
        
        # Calculate where we SHOULD be right now
        target_aov, target_eqx = self.propagator.get_aov_eqx(utils.get_timestamp())
        
        print(f"Orbit Init (Abs Time): Target AoV={target_aov:.1f}, EQX={target_eqx:.1f}")
        
        # NOTE: Do NOT command motors here. Phase anchoring in orbigator.py
        # will handle initial positioning after calculating the offset.

    def on_encoder_rotate(self, delta):
        # Apply accelerated nudging policy
        delta = self.nudge_manager.get_delta(delta)
        
        if self.nudge_target == 0:
            # Nudge AoV (orbital position)
            g.run_start_aov_deg += delta
            if self.propagator:
                self.propagator.nudge_aov(delta)
        else:
            # Nudge EQX (equatorial orientation)
            g.run_start_eqx_deg += delta
            if self.propagator:
                self.propagator.nudge_eqx(delta)
    
    def on_encoder_press(self):
        self.nudge_target = (self.nudge_target + 1) % 2
    
    def on_confirm(self):
        self.tracking = not self.tracking
        if not self.tracking:
            if g.aov_motor: g.aov_motor.stop()
            if g.eqx_motor: g.eqx_motor.stop()
        return None
        
    def on_back(self):
        # Push Main Menu instead of returning it
        g.ui.push(MenuMode())
    
    def update_background(self, now_ms):
        """Physics/Motor update loop that runs even when menu is open."""
        if not self.initialized or not self.tracking: return
        
        # 1. Update target orientation from propagator (cache by second)
        now_unix = utils.get_timestamp()
        if now_unix != self.last_unix:
            self.last_aov_angle, self.last_eqx_angle = self.propagator.get_aov_eqx(now_unix)
            self.last_unix = now_unix
        
        # Use cached values
        aov_angle = self.last_aov_angle
        eqx_angle = self.last_eqx_angle
        
        # 2. Throttled Motor Update (strictly 1Hz)
        if self.last_command_ticks == 0 or time.ticks_diff(now_ms, self.last_command_ticks) >= 1000:
            # Diagnostic logic omitted for brevity in background optimization, 
            # or keep it if essential. Let's keep the jump detection.
            diff_aov = abs(aov_angle - self.last_target_aov)
            diff_eqx = abs(eqx_angle - self.last_target_eqx)
            
            if self.last_command_ticks != 0: 
                is_wrap_aov = diff_aov > 350
                is_wrap_eqx = diff_eqx > 350
                
                if (diff_aov > 2.0 and not is_wrap_aov) or (diff_eqx > 2.0 and not is_wrap_eqx):
                     # Print check might interfere with UI if UART shared?
                     # Ideally logging should be buffered or suppressed in bg?
                     # For now, let it print.
                     pass 
            
            self.last_target_aov = aov_angle
            self.last_target_eqx = eqx_angle
            self.last_command_ticks = now_ms
            
            # Update Globals for State Saving
            g.aov_position_deg = aov_angle % 360.0
            g.eqx_position_deg = eqx_angle % 360.0
            
            if g.eqx_motor:
                g.eqx_motor.set_nearest_degrees(g.eqx_position_deg)
                g.eqx_motor.update_present_position(force=True)
            if g.aov_motor:
                g.aov_motor.set_nearest_degrees(g.aov_position_deg)
                g.aov_motor.update_present_position(force=True)

        # Revolution counter
        current_aov_wrapped = g.aov_position_deg % 360
        if self.last_aov_wrapped < 270 and current_aov_wrapped >= 270:
            g.orbital_rev_count += 1
            utils.save_state()
        self.last_aov_wrapped = current_aov_wrapped

    def update(self, now_ms):
        # When active, run background physics + any foreground logic
        self.update_background(now_ms)
    
    def render(self, disp):
        disp.fill(0)
        target = "X" if self.nudge_target == 1 else "A"
        disp.text(f"ORBITING  [{target}]", 0, 0)
        
        # Display Zulu time if available
        now_str = "Zulu: --:--:--Z"
        if g.rtc:
             if g.i2c_lock:
                 with g.i2c_lock:
                     t = g.rtc.datetime()
             else:
                 t = g.rtc.datetime()
             
             if t:
                  now_str = "Zulu: {:02d}:{:02d}:{:02d}Z".format(t[4], t[5], t[6])
        disp.text(now_str, 0, 10)
        
        p_min = g.orbital_period_min
        p_mi = int(p_min)
        p_si = int((p_min - p_mi) * 60)
        if p_mi >= 60:
            h = p_mi // 60
            m = p_mi % 60
            disp.text(f"T: {h:02d}h {m:02d}m {p_si:02d}s", 0, 22)
        else:
            disp.text(f"T: {p_mi:02d}m {p_si:02d}s", 0, 22)
        
        a_str = f"AoV: {g.aov_position_deg % 360:.1f}"
        disp.text(a_str, 0, 44)
        disp.degree(len(a_str)*8 + 1, 44)

        e_str = f"EQX: {g.eqx_position_deg % 360:.1f}"
        disp.text(e_str, 0, 54)
        disp.degree(len(e_str)*8 + 1, 54)
        
        # Catch-up status based on physical hardware feedback
        catching_up = False
        # Use a 2.0 degree threshold to account for settling/backlash
        aov_target = g.aov_position_deg % 360
        aov_actual = g.aov_motor.output_degrees % 360 if g.aov_motor else 0
        eqx_target = g.eqx_position_deg % 360
        eqx_actual = g.eqx_motor.output_degrees % 360 if g.eqx_motor else 0
        
        if g.aov_motor:
            diff_aov = abs(aov_target - aov_actual)
            if diff_aov > 180: diff_aov = abs(diff_aov - 360)
            if diff_aov > 2.0:
                catching_up = True
        
        if not catching_up and g.eqx_motor:
            diff_eqx = abs(eqx_target - eqx_actual)
            if diff_eqx > 180: diff_eqx = abs(diff_eqx - 360)
            if diff_eqx > 2.0:
                catching_up = True
            
        if not self.tracking:
            disp.text("** PAUSED **", 16, 31)
        elif catching_up:
            # Show actual positions during catch-up (replacing Altitude line)
            act_a = aov_actual % 360
            act_e = eqx_actual % 360
            # Use concise format to avoid overlap
            disp.text(f"ACT:A{act_a:3.0f} E{act_e:3.0f}", 0, 31)
            disp.degree(8*8+2, 31)  # After A###
            disp.degree(14*8+2, 31) # After E###
        else:
            disp.text(f"Rev: {g.orbital_rev_count:05d}", 0, 31)
            
        utils.draw_network_status(disp)
        disp.show()


class PeriodEditorMode(Mode):
    """Editor for orbital period in hh:mm:ss format."""
    
    def __init__(self):
        super().__init__()
        total_sec = int(g.orbital_period_min * 60)
        self.hh = total_sec // 3600
        self.mm = (total_sec % 3600) // 60
        self.ss = total_sec % 60
        self.field = 0 # 0=H, 1=M, 2=S
    
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        # CW = increase
        d = delta
        if self.field == 0:
            self.hh = max(0, min(23, self.hh + d))
        elif self.field == 1:
            self.mm = (self.mm + d) % 60
        elif self.field == 2:
            self.ss = (self.ss + d) % 60
            
    def on_encoder_press(self):
        self.field = (self.field + 1) % 3
        
    def on_confirm(self):
        if self.field < 2:
            self.field += 1
            return None
        # Save and return
        new_period_min = (self.hh * 3600 + self.mm * 60 + self.ss) / 60.0
        if new_period_min > 0:
            g.orbital_period_min = new_period_min
            g.orbital_altitude_km, _ = utils.compute_altitude_from_period(new_period_min)
            utils.save_state()
        g.ui.pop()
    
    def on_back(self):
        if self.field > 0:
            self.field -= 1
            return None
        g.ui.pop()
    
    def render(self, disp):
        disp.fill(0)
        disp.text("SET PERIOD", 0, 0)
        
        h_str = "{:02d}".format(self.hh)
        m_str = "{:02d}".format(self.mm)
        s_str = "{:02d}".format(self.ss)
        
        x_base = 30
        y_pos = 25
        
        # HH
        if self.field == 0:
            disp.fb.fill_rect(x_base, y_pos-1, 16, 10, 1)
            disp.fb.text(h_str, x_base, y_pos, 0)
        else:
            disp.fb.text(h_str, x_base, y_pos, 1)
        
        disp.fb.text(":", x_base+16, y_pos, 1)
        
        # MM
        if self.field == 1:
            disp.fb.fill_rect(x_base+24, y_pos-1, 16, 10, 1)
            disp.fb.text(m_str, x_base+24, y_pos, 0)
        else:
            disp.fb.text(m_str, x_base+24, y_pos, 1)
            
        disp.fb.text(":", x_base+40, y_pos, 1)
        
        # SS
        if self.field == 2:
            disp.fb.fill_rect(x_base+48, y_pos-1, 16, 10, 1)
            disp.fb.text(s_str, x_base+48, y_pos, 0)
        else:
            disp.fb.text(s_str, x_base+48, y_pos, 1)
            
        labels = ["Hours", "Minutes", "Seconds"]
        disp.text(f"Edit: {labels[self.field]}", 10, 45)
        disp.text("Confirm to Save", 10, 56)
        disp.show()


class SettingsMode(Mode):
    """Settings menu for secondary parameters."""
    
    def __init__(self, selection=0):
        super().__init__()
        self.selection = selection
        # Combined "Calibrate Zero" replaces separate Homing/Calibrate
        self.items = ["Set Altitude", "Set Inclination", "Set Eccentricity", "Set Periapsis", "Set Rev Count", "Set Zulu Time", "Calibrate Zero", "Motor ID Test", "Screen Timeout", "Back"]
    
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        # Default: CW = Move Down
        move = 1 if delta > 0 else -1 if delta < 0 else 0
        self.selection = (self.selection + move) % len(self.items)
        
    def on_confirm(self):
        if self.selection == 0:
            g.ui.push(AltitudeEditorMode())
        elif self.selection == 1:
            g.ui.push(InclinationEditorMode())
        elif self.selection == 2:
            g.ui.push(EccentricityEditorMode())
        elif self.selection == 3:
            g.ui.push(PeriapsisEditorMode())
        elif self.selection == 4:
            g.ui.push(RevCountEditorMode())
        elif self.selection == 5:
            g.ui.push(DatetimeEditorMode())
        elif self.selection == 6:
            g.ui.push(HomingMode())
        elif self.selection == 7:
            print("Running Motor ID Test...")
            if g.eqx_motor: g.eqx_motor.flash_led(1)
            time.sleep_ms(500)
            if g.aov_motor: g.aov_motor.flash_led(2)
        elif self.selection == 8:
            g.ui.push(ScreenTimeoutMode())
        elif self.selection == 9:
            g.ui.pop()
    
    def on_back(self):
        g.ui.pop()
    
    def render(self, disp):
        disp.fill(0)
        disp.text("SETTINGS", 0, 0)
        
        # Page size: 4 items
        page_size = 4
        start_idx = max(0, min(self.selection - page_size // 2, len(self.items) - page_size))
        
        # Scroll indicators
        if start_idx > 0: disp.text("^", 120, 16)
        if start_idx + page_size < len(self.items): disp.text("v", 120, 52)
        
        for i in range(start_idx, min(start_idx + page_size, len(self.items))):
            item = self.items[i]
            prefix = ">" if i == self.selection else " "
            y = 16 + (i - start_idx) * 12
            disp.text(f"{prefix} {item}", 0, y)
        disp.show()

class ScreenTimeoutMode(Mode):
    """
    Menu to select OLED screen timeout duration.
    Options: 1 min, 2 min, 5 min, 10 min, Never
    """
    TIMEOUT_OPTIONS = [
        ("1 min",  60_000),
        ("2 min",  120_000),
        ("5 min",  300_000),
        ("10 min", 600_000),
        ("Never",  0),
    ]
    
    def __init__(self):
        super().__init__()
        # Set selection to current value
        self.selection = 0
        for i, (_, ms) in enumerate(self.TIMEOUT_OPTIONS):
            if ms == g.oled_timeout_ms:
                self.selection = i
                break
    
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        move = 1 if delta > 0 else -1 if delta < 0 else 0
        self.selection = (self.selection + move) % len(self.TIMEOUT_OPTIONS)
    
    def on_confirm(self):
        _, ms = self.TIMEOUT_OPTIONS[self.selection]
        g.oled_timeout_ms = ms
        # Reset idle timer so display stays on for a moment after selection
        g.last_input_ticks = time.ticks_ms()
        label, _ = self.TIMEOUT_OPTIONS[self.selection]
        print(f"Screen timeout set to: {label}")
        g.ui.pop()
    
    def on_back(self):
        g.ui.pop()
    
    def render(self, disp):
        disp.fill(0)
        disp.text("SCREEN TIMEOUT", 0, 0)
        for i, (label, ms) in enumerate(self.TIMEOUT_OPTIONS):
            prefix = ">" if i == self.selection else " "
            active = "*" if ms == g.oled_timeout_ms else " "
            disp.text(f"{prefix}{active}{label}", 0, 16 + i * 10)
        disp.show()


class HomingMode(Mode):
    """
    Unified 'Calibrate Zero' Mode.
    1. Pauses background tracking.
    2. Moves motors to where they THINK zero is.
    3. Allows user to JOG EQX to where PHYSICAL zero is.
    4. Saves the new offset (= OldOffset + Jog).
    """
    def __init__(self):
        super().__init__()
        self.nudge_manager = input_utils.NudgeManager(fine_step=0.1, medium_step=1.0, coarse_step=5.0)
        self.jog_val = 0.0
        self.base_angle = 0.0
        self.root_mode = None
        self.was_tracking = False

    def enter(self):
        # 1. PAUSE BACKGROUND TRACKING
        if g.ui.stack:
            self.root_mode = g.ui.stack[0]
            if hasattr(self.root_mode, 'tracking'):
                self.was_tracking = self.root_mode.tracking
                self.root_mode.tracking = False
                print("Homing: Paused background tracking")
        
        if g.eqx_motor:
            # Avoid unwinding: Find nearest whole turn logical zero
            curr = g.eqx_motor.position_deg
            self.base_angle = round(curr / 360.0) * 360.0
            
            print(f"Calibrate Zero: Raw={curr:.1f} BaseImplied={self.base_angle:.1f} Off={g.eqx_motor.offset_degrees:.2f}")
            g.eqx_motor.goto(self.base_angle)
            
        if g.aov_motor:
            # Move AoV to 90 (Zenith) as requested
            curr_a = g.aov_motor.position_deg
            # Find nearest k*360 + 90
            # (curr - 90) / 360 rounded gives the nearest cycle index relative to 90
            base_a = round((curr_a - 90.0) / 360.0) * 360.0 + 90.0
            g.aov_motor.goto(base_a)

    def exit(self):
        # Restore tracking state
        if self.root_mode and hasattr(self.root_mode, 'tracking'):
            self.root_mode.tracking = self.was_tracking
            print(f"Homing: Restored tracking={self.was_tracking}")

    def on_encoder_rotate(self, delta):
        """
        Jog EQX motor to align with physical zero.
        Target Logical = Base + Jog.
        """
        if g.eqx_motor:
            d = self.nudge_manager.get_delta(delta)
            self.jog_val += d
            g.eqx_motor.goto(self.base_angle + self.jog_val)
            
    def on_confirm(self):
        # Save new offset.
        # We are physically at P. We want P to correspond to Logical 'base_angle'.
        # Current logic: L = P + OldOff => P = L - OldOff
        # Here L_current = base + jog.
        # So P = base + jog - OldOff.
        #
        # New logic: L_new = P + NewOff.
        # We want L_new = base.
        # base = (base + jog - OldOff) + NewOff.
        # 0 = jog - OldOff + NewOff.
        # NewOff = OldOff - jog.
        
        if g.eqx_motor:
            old_off = g.eqx_motor.offset_degrees
            new_off = (old_off - self.jog_val) % 360.0
            
            g.eqx_motor.offset_degrees = new_off
            utils.save_motor_calibration("eqx", new_off)
            print(f"Calibration Saved: {new_off:.2f} (Was {old_off:.2f}, Jog {self.jog_val:.2f})")
            
            # Re-command base (clears the jog visual offset from logical, keeps physical)
            g.eqx_motor.goto(self.base_angle)
            
        g.ui.pop()
        
    def on_back(self):
        # Cancel - Revert
        if g.eqx_motor:
            print("Calibration Cancelled.")
            g.eqx_motor.goto(0) # Go back to original logical 0
        g.ui.pop()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("CALIBRATE ZERO", 0, 0)
        disp.text("Jog EQX to True 0", 0, 16)
        
        disp.text(f"Jog: {self.jog_val:+.1f}", 0, 32)
        
        if g.eqx_motor: 
            # Show actual physical angle?
            # Phys = Log + Off
            phys = (self.jog_val + g.eqx_motor.offset_degrees) % 360
            disp.text(f"Phys: {phys:.1f}", 0, 44)
        
        disp.text("Click to Save", 0, 56)
        disp.show()


class AltitudeEditorMode(Mode):
    """Editor for orbital altitude."""
    def __init__(self):
        super().__init__()
        self.alt = int(g.orbital_altitude_km)
        # Slower acceleration, max 20km per click (~0.2% of range)
        self.nudge_manager = input_utils.NudgeManager(fine_step=1, medium_step=5, coarse_step=20)
        
    def on_encoder_rotate(self, delta):
        d = self.nudge_manager.get_delta(delta)
        self.alt = max(200, min(2000, self.alt + int(d)))
        
    def on_confirm(self):
        g.orbital_altitude_km = float(self.alt)
        g.orbital_period_min = utils.compute_period_from_altitude(g.orbital_altitude_km)
        utils.save_state()
        g.ui.pop()
        
    def on_back(self):
        g.ui.pop()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("SET ALTITUDE", 0, 0)
        alt_str = f"{self.alt} km"
        w = len(alt_str) * 8
        disp.fb.fill_rect(40, 14, w+4, 10, 1)
        disp.fb.text(alt_str, 42, 15, 0)
        disp.text("Step: 10 km", 0, 40)
        disp.text("Confirm to Save", 0, 52)
        disp.show()

class InclinationEditorMode(Mode):
    """Editor for orbital inclination."""
    def __init__(self):
        super().__init__()
        # Store as 10x integer for easy encoder step (0.1 deg)
        self.inc_x10 = int(g.orbital_inclination_deg * 10)
        # Max 1.0 deg (10 in x10 units) per click
        self.nudge_manager = input_utils.NudgeManager(fine_step=1, medium_step=5, coarse_step=10)
        
    def on_encoder_rotate(self, delta):
        d = self.nudge_manager.get_delta(delta)
        # Range 0 to 180 (most common 0 to 99)
        self.inc_x10 = max(0, min(1800, self.inc_x10 + int(d)))
        
    def on_confirm(self):
        g.orbital_inclination_deg = float(self.inc_x10) / 10.0
        utils.save_state()
        g.ui.pop()
        
    def on_back(self):
        g.ui.pop()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("SET INCLINATION", 0, 0)
        inc_val = f"{self.inc_x10/10.0:.1f}"
        w = (len(inc_val) + 1) * 8
        disp.fb.fill_rect(30, 14, w+4, 10, 1)
        disp.fb.text(inc_val, 32, 15, 0)
        disp.degree(32 + len(inc_val)*8 + 1, 15, 0)
        
        s_str = "Step: 0.1"
        disp.text(s_str, 0, 40)
        disp.degree(len(s_str)*8 + 1, 40)
        disp.text("Confirm to Save", 0, 52)
        disp.show()

class DatetimeEditorMode(Mode):
    """Editor for system date and time."""
    def __init__(self, next_mode=None):
        super().__init__()
        self.next_mode = next_mode if next_mode else SettingsMode(selection=5)  # Zulu Time is index 5
        t = utils.get_timestamp(g.rtc)
        # Pico 2000 epoch: (Y, M, D, H, M, S, WD, YD)
        lt = time.localtime(int(t))
        self.year = lt[0] if lt[0] >= 2024 else 2024
        self.month = lt[1]
        self.day = lt[2]
        self.hour = lt[3]
        self.minute = lt[4]
        self.field = 0 # 0=Y, 1=M, 2=D, 3=H, 4=Min
        
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        d = delta # CW = increase
        if self.field == 0: self.year = max(2024, min(2099, self.year + d))
        elif self.field == 1: self.month = (self.month - 1 + d) % 12 + 1
        elif self.field == 2: self.day = (self.day - 1 + d) % 31 + 1
        elif self.field == 3: self.hour = (self.hour + d) % 24
        elif self.field == 4: self.minute = (self.minute + d) % 60
        
    def on_confirm(self):
        if self.field < 4:
            self.field += 1
            return None
        # Save time
        utils.set_datetime(int(self.year), int(self.month), int(self.day), int(self.hour), int(self.minute), 0, g.rtc)
        # Force a state save to update the config timestamp
        utils.save_state()
        
        # If part of a wizard (next_mode), push it?
        # But we are replacing mode return with stack ops.
        # Original logic: return self.next_mode
        # If next_mode was SettingsMode(selection=5), we just pop.
        # If next_mode was OrbitMode (boot sequence), we should push/replace?
        # DatetimeEditorMode is used in boot sequence if config says so.
        # "g.current_mode = DatetimeEditorMode(next_mode=OrbitMode())" in orbigator.py
        # We need to handle this.
        if isinstance(self.next_mode, Mode):
             # Transition to next mode
             g.ui.replace(self.next_mode)
        else:
             # Default back to settings (pop)
             g.ui.pop()
        
    def on_back(self):
        if self.field > 0:
            self.field -= 1
            return None
        g.ui.pop()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("SET ZULU TIME", 0, 0)
        
        # Draw "D: " and "T: " labels
        disp.text("D:", 0, 12)
        disp.text("T:", 0, 24)
        
        # Helper to draw highlighted text
        def draw_field(val_str, x, y, is_active):
            w = len(val_str) * 8
            if is_active:
                disp.fb.fill_rect(x, y-1, w, 10, 1)
                disp.fb.text(val_str, x, y, 0)
            else:
                disp.fb.text(val_str, x, y, 1)
        
        # Coordinates
        y_d = 12
        # Year (Field 0)
        draw_field("{:04d}".format(self.year), 24, y_d, self.field == 0)
        disp.text("-", 24+32, y_d)
        
        # Month (Field 1)
        draw_field("{:02d}".format(self.month), 24+32+8, y_d, self.field == 1)
        disp.text("-", 24+32+8+16, y_d)
        
        # Day (Field 2)
        draw_field("{:02d}".format(self.day), 24+32+8+16+8, y_d, self.field == 2)
        
        y_t = 24
        # Hour (Field 3)
        draw_field("{:02d}".format(self.hour), 24, y_t, self.field == 3)
        disp.text(":", 24+16, y_t)
        
        # Minute (Field 4)
        draw_field("{:02d}".format(self.minute), 24+16+8, y_t, self.field == 4)
        disp.text("Z", 24+16+8+16, y_t)
        
        fields = ["Year", "Month", "Day", "Hour", "Minute"]
        disp.text(f"Edit: {fields[self.field]}", 0, 40)
        disp.text("Confirm >> Next", 0, 52)
        disp.show()


class EccentricityEditorMode(Mode):
    """Editor for orbital eccentricity."""
    def __init__(self):
        super().__init__()
        # Store as 100x integer for 0.01 precision (0 to 90 = 0.00 to 0.90)
        self.ecc_x100 = int(g.orbital_eccentricity * 100)
        # Slower: 0.01, 0.02, 0.05 per click
        self.nudge_manager = input_utils.NudgeManager(fine_step=1, medium_step=2, coarse_step=5)
        
    def on_encoder_rotate(self, delta):
        d = self.nudge_manager.get_delta(delta)
        # Range 0 to 90 (0.00 to 0.90)
        self.ecc_x100 = max(0, min(90, self.ecc_x100 + int(d)))
        
    def on_confirm(self):
        g.orbital_eccentricity = float(self.ecc_x100) / 100.0
        utils.save_state()
        g.ui.pop()
        
    def on_back(self):
        g.ui.pop()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("SET ECCENTRICITY", 0, 0)
        ecc = float(self.ecc_x100) / 100.0
        ecc_str = f"{ecc:.2f}"
        w = len(ecc_str) * 8
        disp.fb.fill_rect(40, 14, w+4, 10, 1)
        disp.fb.text(ecc_str, 42, 15, 0)
        
        # Show orbit type
        if ecc < 0.01:
            orbit_type = "Circular"
        elif ecc < 0.3:
            orbit_type = "Elliptical"
        else:
            orbit_type = "Highly Ellip"
        disp.text(orbit_type, 30, 28)
        
        disp.text("Step: 0.01", 0, 40)
        disp.text("Confirm to Save", 0, 52)
        disp.show()

class PeriapsisEditorMode(Mode):
    """Editor for argument of periapsis."""
    def __init__(self):
        super().__init__()
        self.periapsis = int(g.orbital_periapsis_deg)
        # Max 1.0 deg per click
        self.nudge_manager = input_utils.NudgeManager(fine_step=1, medium_step=5, coarse_step=10)
        
    def on_encoder_rotate(self, delta):
        d = self.nudge_manager.get_delta(delta)
        self.periapsis = (self.periapsis + int(d)) % 360
        
    def on_confirm(self):
        g.orbital_periapsis_deg = float(self.periapsis)
        utils.save_state()
        g.ui.pop()
        
    def on_back(self):
        g.ui.pop()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("SET PERIAPSIS", 0, 0)
        per_val = f"{self.periapsis}"
        w = (len(per_val) + 1) * 8
        disp.fb.fill_rect(30, 14, w+4, 10, 1)
        disp.fb.text(per_val, 32, 15, 0)
        disp.degree(32 + len(per_val)*8 + 1, 15, 0)
        
        disp.text("(Closest point)", 0, 28)
        
        s_str = "Step: 5"
        disp.text(s_str, 0, 40)
        disp.degree(len(s_str)*8 + 1, 40)
        disp.text("Confirm to Save", 0, 52)
        disp.show()
        disp.show()

class RevCountEditorMode(Mode):
    """Editor for orbital revolution count (digit by digit)."""
    def __init__(self):
        super().__init__()
        # Support up to 999999 revs (6 digits)
        self.digits = [0] * 6
        # Initialize from current value
        val = int(g.orbital_rev_count)
        for i in range(5, -1, -1):
            self.digits[i] = val % 10
            val //= 10
        self.field = 0  # 0-5 for each digit
        
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        # CW = increase digit
        self.digits[self.field] = (self.digits[self.field] + delta) % 10
        
    def on_encoder_press(self):
        self.field = (self.field + 1) % 6
        
    def on_confirm(self):
        if self.field < 5:
            self.field += 1
            return None
        # Save and return
        new_count = 0
        for d in self.digits:
            new_count = new_count * 10 + d
        g.orbital_rev_count = new_count
        utils.save_state()
        g.ui.pop()
        
    def on_back(self):
        if self.field > 0:
            self.field -= 1
            return None
        g.ui.pop()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("SET REV COUNT", 0, 0)
        
        # Draw 6 digits
        x_base = 16
        y_pos = 25
        
        for i in range(6):
            d_str = str(self.digits[i])
            x = x_base + i * 16
            
            if self.field == i:
                disp.fb.fill_rect(x, y_pos-1, 8, 10, 1)
                disp.fb.text(d_str, x, y_pos, 0)
            else:
                disp.fb.text(d_str, x, y_pos, 1)
        
        disp.text("Orbit Counter", 16, 45)
        disp.text("Confirm to Save", 10, 56)
        disp.show()

class MotorOfflineMode(Mode):
    """Degraded mode when motor communication fails."""
    def __init__(self, motor_id, motor_name, error_msg):
        super().__init__()
        self.motor_id = motor_id
        self.motor_name = motor_name
        self.error_msg = error_msg
        print(f"\n{'='*60}")
        print(f"MOTOR OFFLINE: {motor_name} (ID {motor_id})")
        print(f"Error: {error_msg}")
        print(f"{'='*60}\n")
        
    def on_confirm(self):
        # Attempt recovery
        print(f"Attempting to recover motor {self.motor_id} ({self.motor_name})...")
        g.motor_health_ok = True
        g.motor_offline_id = None
        g.motor_offline_error = ""
        
        # Reset failure counters
        if self.motor_id == 2 and g.aov_motor:
            g.aov_motor.consecutive_failures = 0
        elif self.motor_id == 1 and g.eqx_motor:
            g.eqx_motor.consecutive_failures = 0
        
        # We were likely pushed on top of something. Pop to return.
        g.ui.pop()
        
    def on_back(self):
        return None  # Stay in offline mode
        
    def render(self, disp):
        disp.fill(0)
        disp.text("MOTOR OFFLINE", 0, 0)
        disp.text(f"Motor: {self.motor_name}", 0, 12)
        disp.text(f"ID: {self.motor_id}", 0, 24)
        
        # Error code (truncate if too long)
        err = self.error_msg[:16]
        disp.text(f"Err: {err}", 0, 36)
        
        disp.text("Confirm to Retry", 0, 56)
        disp.show()


class SGP4Mode(Mode):
    """Real-time satellite tracking using SGP4 propagation."""
    
    def __init__(self):
        super().__init__()
        self.satellite_index = 0
        self.tracking = False
        self.sgp4 = None
        self.satellite_name = None
        self.tle_age = "unknown"
        self.last_update = 0
        self.lat_deg = 0.0
        self.lon_deg = 0.0
        self.alt_km = 0.0
        self.fetching = False
        self.propagator = None
        self.last_target_aov = 0.0
        self.last_target_eqx = 0.0
        self.last_unix = 0 # Cache for propagator math
        self.last_aov_angle = 0.0
        self.last_eqx_angle = 0.0
        self.last_command_ticks = 0
        self.inclination = 0.0
        self.last_tle_check = 0
        self.nudge_manager = input_utils.NudgeManager(fine_step=1.0, medium_step=1.0, coarse_step=1.0)
        
        # WiFi is handled globally by g.caps (R4.2)
        
    def enter(self):
        """Initialize SGP4 tracking mode."""
        g.current_mode_id = "SGP4"
        
        # Re-assert speed limits for safety
        # Re-assert speed limits for safety? No, user wants fast slewing.
        # We rely on orbigator_config.json

        from satellite_catalog import get_satellite_count, get_satellite_name
        import sgp4
        
        # Load satellite catalog
        self.sat_count = get_satellite_count()
        if self.sat_count == 0:
            print("Error: No satellites in catalog")
            return
        
        # Load TLE cache
        self.tle_cache = utils.load_tle_cache()
        
        # Initialize        # Load satellite data/TLE
        self._load_satellite()
        
        self.initialized = True
        
        # Checkpoint: Save state so we resume from this time/sat on reboot
        utils.save_state()
        print(f"SGP4 Mode: {self.sat_count} satellites available")
    
    def select_satellite_by_name(self, name):
        """Set active satellite by name."""
        if self.satellite_name == name and self.initialized:
            return True
            
        from satellite_catalog import get_satellite_count, get_satellite_name
        for i in range(get_satellite_count()):
            if get_satellite_name(i) == name:
                self._load_satellite(i)
                return True
        return False
        
    def _load_satellite(self, index=0):
        """Load and initialize SGP4 for selected satellite."""
        from satellite_catalog import get_satellite_name, get_satellite_norad
        import sgp4
        
        self.satellite_index = index
        self.satellite_name = get_satellite_name(index)
        self.norad_id = get_satellite_norad(index)
        norad_id = self.norad_id
        
        # Check if TLE is in cache
        if self.satellite_name in self.tle_cache:
            tle_data = self.tle_cache[self.satellite_name]
            line1 = tle_data["line1"]
            line2 = tle_data["line2"]
            last_fetch = tle_data.get("last_fetch", 0)
            self.tle_age = utils.get_tle_age_str(last_fetch)
            
            # Check if update needed
            needs_update = utils.tle_needs_update(last_fetch)
            
            # Validate NORAD ID in TLE Line 2 (chars 2-7) matches expected
            # Line 2 format: 2 NNNNN ...
            try:
                cached_id = line2.split()[1]
                if str(cached_id) != str(self.norad_id):
                    print(f"TLE Mismatch! Cached {cached_id} != Expected {self.norad_id}")
                    needs_update = True
                    self.tle_age = "WRONG SAT"
            except:
                pass

            if needs_update:
                print(f"TLE for {self.satellite_name} is stale or wrong, needs update")
                self.tle_age += " OLD"
                self.fetching = True # Trigger auto-fetch
        else:
            # No TLE in cache - need to fetch
            print(f"No TLE for {self.satellite_name}, need to fetch")
            self.tle_age = "missing"
            self.fetching = True # Trigger auto-fetch
            return
        
        # If fetching, skip parsing until we have data
        if self.fetching and self.tle_age == "missing":
            return
        
        # Parse TLE
        print(f"DEBUG LOAD TLE for {self.satellite_name}:")
        print(f"L1: {line1}")
        print(f"L2: {line2}")
        
        epoch_year, epoch_day = utils.parse_tle_epoch(line1)
        bstar = float(line1[53:59]) * 10.0 ** float(line1[59:61])
        inc = float(line2[8:16])
        raan = float(line2[17:25])
        ecc = float('0.' + line2[26:33])
        argp = float(line2[34:42])
        m = float(line2[43:51])
        n = float(line2[52:63])
        
        # Initialize SGP4
        import propagate
        self.inclination = inc
        self.sgp4 = sgp4.SGP4()
        self.sgp4.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)
        self.propagator = propagate.MicroSGP4(self.sgp4)
        self.tracking = True # Start tracking automatically on selection
        
        print(f"Loaded {self.satellite_name}: epoch {epoch_year} day {epoch_day:.2f}")
    
    def _fetch_tle(self):
        """Fetch TLE data via WiFi (WiFi hardware/capability required)."""
        # 1. Hardware/Capability Check (R4.2)
        if not g.caps.has_wifi:
            print("SGP4: WiFi capability not enabled.")
            return False

        # 2. Config Check
        import json
        import os
        if "wifi_config.json" not in os.listdir():
            print("SGP4: wifi_config.json missing. Cannot fetch TLE.")
            return False

        # 3. Load Config
        try:
            with open("wifi_config.json", "r") as f:
                cfg = json.load(f)
                ssid = cfg.get("ssid")
                password = cfg.get("password")
                if not ssid: raise ValueError("Empty SSID")
        except Exception as e:
            print(f"SGP4: Invalid WiFi config: {e}")
            return False

        # 4. Fetching UI
        self.fetching = True
        g.disp.fill(0)
        g.disp.text("Fetching TLE...", 0, 0)
        g.disp.text("Please wait", 0, 12)
        g.disp.show()
        print(f"Fetching TLE for {self.satellite_name}...")
        
        # 5. Connect to WiFi using standard networking module
        import networking
        ip = networking.connect_wifi(ssid, password, display=g.disp)
        if not ip:
            print("SGP4: WiFi connection failed")
            self.fetching = False
            return False
        
        # 6. Fetch TLE Data
        import tle_fetch
        # Use NORAD ID if available
        target_id = getattr(self, 'norad_id', self.satellite_name)
        tle_data = tle_fetch.fetch_tle(target_id)
        if not tle_data:
            print("SGP4: TLE fetch failed")
            self.fetching = False
            return False
            
        # 7. Update cache and reload
        name, line1, line2 = tle_data
        self.tle_cache[self.satellite_name] = {
            "line1": line1,
            "line2": line2,
            "last_fetch": int(utils.get_timestamp())
        }
        utils.save_tle_cache(self.tle_cache)
        self._load_satellite(self.satellite_index)
        
        self.fetching = False
        print(f"✓ SGP4: TLE updated for {self.satellite_name}")
        return True

    def set_manual_tle(self, name, line1, line2):
        """Set TLE manually from API."""
        import sgp4
        
        try:
            # Parse TLE
            epoch_year, epoch_day = utils.parse_tle_epoch(line1)
            bstar = float(line1[53:59]) * 10.0 ** float(line1[59:61])
            inc = float(line2[8:16])
            raan = float(line2[17:25])
            ecc = float('0.' + line2[26:33])
            argp = float(line2[34:42])
            m = float(line2[43:51])
            n = float(line2[52:63])
            
            # Initialize SGP4
            self.sgp4 = sgp4.SGP4()
            self.sgp4.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)
            
            # Update state
            self.satellite_index = -1 # Manual
            self.satellite_name = name
            self.tle_age = "Manual"
            self.tracking = True # Start tracking immediately
            self.propagator = propagate.MicroSGP4(self.sgp4)
            
            print(f"Manual TLE set for {name}")
            return True, "TLE loaded successfully"
        except Exception as e:
            print(f"Manual TLE error: {e}")
            return False, str(e)

    def on_encoder_rotate(self, delta):
        import input_utils
        delta = input_utils.normalize_encoder_delta(delta)
        
        if not self.tracking:
            # Satellite selection mode
            move = 1 if delta > 0 else -1 if delta < 0 else 0
            self.satellite_index = (self.satellite_index + move) % self.sat_count
            self._load_satellite(self.satellite_index)
            print(f"DEBUG: Saving selection {self.satellite_index}")
            utils.save_state() # Save selection
        # If tracking, ignore rotation (or could add nudge like OrbitMode)
    
    def on_encoder_press(self):
        """Force TLE refresh (WiFi required)."""
        if self.satellite_name:
            if g.caps.has_wifi:
                self._fetch_tle()
            else:
                # No WiFi hardware
                import time
                print("SGP4: WiFi not available")
                g.disp.fill(0)
                g.disp.text("No WiFi!", 0, 0)
                g.disp.text("Cannot refresh", 0, 12)
                g.disp.show()
                time.sleep(1)
        return None
    
    def on_confirm(self):
        """Start/stop tracking."""
        self.tracking = not self.tracking
        if self.tracking:
            print(f"Tracking {self.satellite_name}")
            utils.save_state() # Save that we are tracking
        else:
            print(f"Selection mode")
        return None
    
    def on_back(self):
        """Return to menu."""
        g.ui.push(MenuMode())
    
    def update_background(self, now_ms):
        """Physics/Motor update loop that runs even when menu is open."""
        
        # --- Periodic TLE Check (every 60s) ---
        if self.tracking and g.caps.has_wifi and not self.fetching:
             if self.last_tle_check == 0 or time.ticks_diff(now_ms, self.last_tle_check) >= 60000:
                 self.last_tle_check = now_ms
                 # Check if update needed based on cache timestamp
                 if self.satellite_name in self.tle_cache:
                     last_fetch = self.tle_cache[self.satellite_name].get("last_fetch", 0)
                     if utils.tle_needs_update(last_fetch):
                         print(f"Periodic TLE Check: {self.satellite_name} is stale. Fetching...")
                         self.fetching = True

        # --- Auto-Fetch Logic ---
        if self.fetching:
             # Ensure we don't spam fetch (10s retry delay could be added here if needed)
             # For now, rely on single-shot or blocking call if we want simplicity
             # But update() is 1Hz. Let's do it once.
             # Actually, we should probably do this in a thread or check condition
             # To keep it simple and safe in the main loop:
             if g.caps.has_wifi and (self.last_command_ticks == 0 or time.ticks_diff(now_ms, self.last_command_ticks) >= 2000):
                 # Try to fetch
                 print("Attempting auto-fetch...")
                 success = self._fetch_tle()
                 if not success:
                     # If failed, stop trying for a bit or forever?
                     # Let's stop trying for this session to avoid loop
                     # print("Auto-fetch failed. Disabling until manual retry.")
                     self.fetching = False
                 else:
                     # Success - _fetch_tle sets fetching=False and reloads
                     pass
                 self.last_command_ticks = now_ms
             return

        if not self.propagator or not self.tracking:
            return
        
        # print(f"SGP4 Update: {getattr(self, 'satellite_name', 'UNK')} track={self.tracking}")
        
        # 1. Update target orientation from propagator (cache by second)
        now_unix = utils.get_timestamp()
        if now_unix != self.last_unix:
            self.last_aov_angle, self.last_eqx_angle, self.lat_deg, self.lon_deg = self.propagator.get_aov_eqx(now_unix)
            self.alt_km = self.propagator.get_altitude()
            
            # print(f"SGP4 Calc: AoV={self.last_aov_angle:.1f} EQX={self.last_eqx_angle:.1f} | Lat={self.lat_deg:.2f} Lon={self.lon_deg:.2f} @ {now_unix}")

            # Update Globals for State Saving
            g.aov_position_deg = self.last_aov_angle % 360.0
            g.eqx_position_deg = self.last_eqx_angle % 360.0
            self.last_unix = now_unix
        
        # Use cached values for motor commands
        aov_angle = self.last_aov_angle
        eqx_angle = self.last_eqx_angle
        
        # 2. Throttled Motor Update (strictly 1Hz)
        if self.last_command_ticks == 0 or time.ticks_diff(now_ms, self.last_command_ticks) >= 1000:
            # Diagnostic: Check for mathematical jumps in the propagator targets
            diff_aov = abs(aov_angle - self.last_target_aov)
            diff_eqx = abs(eqx_angle - self.last_target_eqx)
            
            if self.last_command_ticks != 0: # Skip first run diagnostic
                # Ignore jumps that look like a 360->0 or 0->360 wrap
                is_wrap_aov = diff_aov > 350
                is_wrap_eqx = diff_eqx > 350
                
                if (diff_aov > 2.0 and not is_wrap_aov) or (diff_eqx > 2.0 and not is_wrap_eqx):
                    dt_ms = time.ticks_diff(now_ms, self.last_command_ticks)
                    # print(f"\n[SGP4 JUMP] {self.satellite_name} @ {now_unix} (dt={dt_ms}ms)")
                    pass
            
            self.last_target_aov = aov_angle
            self.last_target_eqx = eqx_angle
            self.last_command_ticks = now_ms
            
            
            if g.aov_motor:
                g.aov_motor.set_nearest_degrees(g.aov_position_deg)
                g.aov_motor.update_present_position(force=True) # Poll hardware after move
            
            if g.eqx_motor:
                # Command the PHASE-SHIFTED target
                g.eqx_motor.set_nearest_degrees(g.eqx_position_deg)
                g.eqx_motor.update_present_position(force=True) # Poll hardware after move
        
        # Note: SRAM persistence is now handled by motor.on_turn_change callback

        # --- Tier 0: Trig-free horizon test (hot loop) ---
        if g.observer_frame and g.overhead_watcher and self.propagator:
            try:
                ecef = self.propagator.get_ecef()
                if ecef:
                    dot = g.observer_frame.dot_up(*ecef)
                    was_active = g.overhead_watcher.is_alert_active()
                    g.overhead_watcher.update(dot, now_ms)
                    # Wake display when alert first triggers
                    if g.overhead_watcher.is_alert_active() and not was_active:
                        g.last_input_ticks = now_ms  # reset idle timer = wake display
                        if g.disp and hasattr(g.disp, 'is_sleeping') and g.disp.is_sleeping:
                            try: g.disp.wake()
                            except: pass
                        if g.radar_display:
                            g.radar_display.reset_trail()
            except Exception as _oa_err:
                pass  # Fail silent - never interrupt tracking
    
    def update(self, now_ms):
        self.update_background(now_ms)
    
    def render(self, disp):
        """Render SGP4 mode display."""

        # --- Tier 1: Radar alert display (only when satellite is overhead) ---
        if g.overhead_watcher and g.overhead_watcher.is_alert_active():
            if g.observer_frame and g.radar_display and self.propagator:
                try:
                    ecef = self.propagator.get_ecef()
                    if ecef:
                        az, el = g.observer_frame.az_el_deg(*ecef)
                        g.radar_display.update(az, el)
                        g.radar_display.render(disp, self.satellite_name or "SAT", az, el)
                        return  # radar render replaces normal HUD
                except:
                    pass  # fall through to normal HUD on any error

        # Normal SGP4 HUD
        disp.fill(0)
        
        if not self.satellite_name:
            disp.text("No Satellite", 0, 2)
            disp.text("Data", 0, 14)
            disp.show()
            return
        
        # Title + Satellite name on one line
        mode_str = "Tracking" if self.tracking else "Select"
        sat_name = self.satellite_name[:8]  # Shorter to fit on one line
        disp.text(f"{mode_str} {sat_name}", 0, 2)
        
        # AoV/EQX positions (integer degrees)
        aov_int = int(g.aov_position_deg % 360)
        eqx_int = int(g.eqx_position_deg % 360)
        disp.text(f"AoV:{aov_int:3d} EQX:{eqx_int:3d}", 0, 14)
        
        if self.fetching:
            # Show fetching message
            disp.text("Fetching TLE...", 0, 26)
            disp.text("Please wait", 0, 38)
        elif self.tracking and self.sgp4:
            # Catch-up status based on physical hardware feedback
            catching_up = False
            # Use same robust comparison as OrbitMode
            aov_target = g.aov_position_deg % 360
            aov_actual = g.aov_motor.output_degrees % 360 if g.aov_motor else 0
            eqx_target = g.eqx_position_deg % 360
            eqx_actual = g.eqx_motor.output_degrees % 360 if g.eqx_motor else 0

            if g.aov_motor:
                diff_aov = abs(aov_target - aov_actual)
                if diff_aov > 180: diff_aov = abs(diff_aov - 360)
                if diff_aov > 2.0:
                    catching_up = True
            
            if not catching_up and g.eqx_motor:
                diff_eqx = abs(eqx_target - eqx_actual)
                if diff_eqx > 180: diff_eqx = abs(diff_eqx - 360)
                if diff_eqx > 2.0:
                    catching_up = True
                
            # Always show tracking info, ignore catch-up warning
            if True:
                # Show position
                # LLA Line: Lat (-90 to +90), Lon (-180 to +180), Alt
                lon_180 = self.lon_deg
                if lon_180 > 180:
                    lon_180 -= 360
                lla_str = f"LLA:{self.lat_deg:+3.0f} {lon_180:+4.0f} {self.alt_km:4.0f}"
                disp.text(lla_str, 0, 26)
            
            disp.text(f"TLE: {self.tle_age}", 0, 50)
        else:
            # Selection mode - show instructions
            disp.text("Dial: Select", 0, 32)
            disp.text("Press: Track", 0, 44)
            disp.text(f"TLE: {self.tle_age}", 0, 56)
        
        if self.tracking and self.sgp4:
            # LLA is at y=26, so IP goes to y=38
            # Careful not to overlap with TLE at y=50 if we moved TLE...
            # Actually TLE is at y=50 in tracking loop (line 1487)
            # So IP at 38 is perfect (26+12=38, 38+12=50)
            utils.draw_network_status(disp, 0, 38)
        else:
            utils.draw_network_status(disp)
            
        disp.show()



# ==========================================
# TrackLL Mode (Front Face Tracking)
# ==========================================
class TrackLLMode(SGP4Mode):
    """
    Tracking Mode that forces the solution to the "Front Face" of the device.
    Uses SGP4 to get Lat/Lon, then calculates Virtual Inclination.
    """
    def __init__(self):
        super().__init__()
        # Ensure we use the current selected satellite from SGP4Mode
        self.mode_name = "Track LL"

    def enter(self):
        # We reuse SGP4Mode's enter to setup the propagator
        super().enter()
        self.track_mode = "VIRTUAL" # Just a label
        if g.disp:
            g.disp.fill(0)
            g.disp.text("Front Face", 0, 0)
            g.disp.text("Tracking Init...", 0, 12)
            g.disp.show()
            
    def render(self, disp):
        # Override render to show we are in TrackLL
        disp.fill(0)
        disp.text("FRONT FACE", 0, 0)
        
        if self.tracking and self.propagator:
             # Show Lat/Lon
            la_str = f"Lat: {self.lat_deg:+.2f}"
            disp.text(la_str, 0, 16)
            
            lo_str = f"Lon: {self.lon_deg:+.2f}"
            disp.text(lo_str, 0, 28)
            
            disp.text(f"Alt: {self.alt_km:.0f}km", 0, 40)
            if self.tle_age != "OK":
                 disp.text(f"TLE: {self.tle_age}", 0, 52)
        else:
             disp.text("Waiting...", 0, 20)
             
        utils.draw_network_status(disp)
        disp.show()

    def update_background(self, now_ms):
        """Update satellite position and motors."""
        if not self.propagator or not self.tracking:
            return
        
        # 1. Update target orientation from propagator
        ts = utils.get_timestamp()
        
        # Throttle updates to ~1Hz or when second changes to save CPU/Bus
        if ts == self.last_unix:
             return
        
        self.last_unix = ts
        
        try:
            # MicroSGP4.get_aov_eqx returns (aov, eqx, lat, lon)
            aov, eqx, lat, lon = self.propagator.get_aov_eqx(ts)
            self.alt_km = self.propagator.get_altitude()
            
            self.lat_deg = lat
            self.lon_deg = lon
            
            # 3. Solve Virtual Inclination (Force Front Face)
            virt_aov, virt_eqx = utils.calculate_virtual_inclination(
                lat, lon, 
                g.orbital_inclination_deg, 
                current_aov=g.aov_position_deg, 
                force_ascending=True
            )
            
            if virt_aov is not None:
                # 4. Command Motors
                self.last_aov_angle = virt_aov
                self.last_eqx_angle = virt_eqx
                
                # Apply offsets/etc if needed, but set_nearest_degrees handles wrapping.
                if g.aov_motor:
                    g.aov_motor.set_nearest_degrees(virt_aov, direction_override=0)
                    g.aov_motor.update_present_position()
                    
                if g.eqx_motor:
                    g.eqx_motor.set_nearest_degrees(virt_eqx, direction_override=0)
                    g.eqx_motor.update_present_position()
        except AttributeError:
             print("TrackLL: Propagator missing method")
        except Exception as e:
            print(f"TrackLL Error: {e}")

    def update(self, now_ms):
        self.update_background(now_ms)
