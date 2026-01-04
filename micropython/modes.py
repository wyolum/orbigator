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
import propagators


class Mode:
    """Base class for UI modes."""
    def __init__(self):
        self.debug_counter = 0
    
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        pass
    
    def on_encoder_press(self):
        return self.on_confirm()
    
    def on_confirm(self):
        return None
    
    def on_back(self):
        return None
    
    def update(self, dt):
        pass
    
    def render(self, disp):
        pass
    
    def enter(self):
        pass
    
    def exit(self):
        pass


class MenuMode(Mode):
    """Main menu mode."""
    
    def __init__(self):
        super().__init__()
        self.selection = 0
        # Build menu items - only include Track Satellite if WiFi available
        self.items = ["Orbit!", "Set Period", "Settings"]
        
        # Check for WiFi hardware
        try:
            import network
            wlan = network.WLAN(network.STA_IF)
            # Insert Track Satellite after Orbit! if WiFi available
            self.items.insert(1, "Track Satellite")
        except:
            pass  # No WiFi, skip Track Satellite option
            
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
            return OrbitMode()
        elif item == "Track Satellite":
            return SGP4Mode()
        elif item == "Set Period":
            return PeriodEditorMode()
        elif item == "Settings":
            return SettingsMode()
        return None
    
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
        self.last_saved_rev_eqx = 0
        self.last_saved_rev_aov = 0
        self.last_command_ticks = 0
        self.last_target_aov = 0.0
        self.last_target_eqx = 0.0
        self.last_unix = 0  # Cache for propagator math
        self.tracking = True # Toggle with Confirm button
        self.last_aov_angle = 0.0
        self.last_eqx_angle = 0.0
        self.nudge_manager = input_utils.NudgeManager()
        self.last_aov_wrapped = 0.0  # Track wrapped AoV for south point detection
    
    def enter(self) :
        """Initialize orbital tracking and catch up if needed."""
        g.current_mode_id = "ORBIT"
        
        if g.aov_motor:
            g.aov_motor.set_speed_limit(2)
        if g.eqx_motor:
            g.eqx_motor.set_speed_limit(10)
            
        # Check if we are resuming an active session (Menu -> Orbit) or starting fresh (Boot -> Orbit)
        if g.initialized_orbit:
            if g.orbital_eccentricity > 0.001:
                # Elliptical Orbit Resume Strategy: BACKDATE TIME
                true_anomaly = (g.aov_position_deg - g.orbital_periapsis_deg) % 360.0
                M_rad = utils.compute_mean_from_true_anomaly(true_anomaly, g.orbital_eccentricity)
                period_sec = g.orbital_period_min * 60.0
                n = 2.0 * math.pi / period_sec
                elapsed_needed = M_rad / n
                
                now_ticks = time.ticks_ms()
                g.run_start_ticks = time.ticks_add(now_ticks, -int(elapsed_needed * 1000))
                current_turns = (g.aov_position_deg // 360) * 360.0
                g.run_start_aov_deg = current_turns
            else:
                # Circular Orbit Resume Strategy: RESET TIME
                g.run_start_ticks = time.ticks_ms()
                g.run_start_aov_deg = g.aov_position_deg
                g.run_start_eqx_deg = g.eqx_position_deg
            
            # Initialize propagator
            self.propagator = propagators.KeplerPropagator(
                g.orbital_altitude_km, g.orbital_inclination_deg, 
                g.orbital_eccentricity, g.orbital_periapsis_deg,
                g.run_start_aov_deg, g.run_start_eqx_deg, g.run_start_time
            )
            self.initialized = True
            return

        # Start Fresh Tracking
        if not g.initialized_orbit:
            state_dict = utils.load_state()
            saved_ts = state_dict.get("timestamp", 0)
            saved_eqx = state_dict.get("eqx_position_deg", g.eqx_position_deg)
            saved_aov = state_dict.get("aov_position_deg", g.aov_position_deg)
            g.initialized_orbit = True
        else:
            saved_ts = 0
            saved_eqx = g.eqx_position_deg
            saved_aov = g.aov_position_deg
        
        aov_rate, eqx_rate_sec, eqx_rate_day, period_min = utils.compute_motor_rates(g.orbital_altitude_km)
        g.aov_rate_deg_sec = aov_rate
        g.eqx_rate_deg_sec = eqx_rate_sec
        g.eqx_rate_deg_day = eqx_rate_day
        g.orbital_period_min = period_min
        
        now = utils.get_timestamp()
        elapsed = now - saved_ts if saved_ts > 0 else 0
        if elapsed > 300: # 5 min limit for catch-up
             elapsed = 0; saved_ts = 0
        
        if elapsed > 0 and saved_ts > 0:
            if g.orbital_eccentricity > 0.001:
                true_old = (saved_aov - g.orbital_periapsis_deg) % 360.0
                M_old = utils.compute_mean_from_true_anomaly(true_old, g.orbital_eccentricity)
                period_sec = g.orbital_period_min * 60.0
                n = 2.0 * math.pi / period_sec
                M_new = M_old + (n * elapsed)
                t_new = M_new / n
                expected_phase, _ = utils.compute_elliptical_position(
                    t_new, period_sec, g.orbital_eccentricity, g.orbital_periapsis_deg
                )
                saved_turns = (saved_aov // 360) * 360
                expected_aov = saved_turns + expected_phase
            else:
                expected_aov = saved_aov + (g.aov_rate_deg_sec * elapsed)
            expected_eqx = saved_eqx + (g.eqx_rate_deg_sec * elapsed)
            
            # Shortest Path Catch-up
            curr_aov_w = g.aov_position_deg % 360
            curr_eqx_w = g.eqx_position_deg % 360
            exp_aov_w = expected_aov % 360
            exp_eqx_w = expected_eqx % 360
            
            d_aov = utils.get_shortest_path_delta(curr_aov_w, exp_aov_w)
            d_eqx = utils.get_shortest_path_delta(curr_eqx_w, exp_eqx_w)
            
            g.run_start_aov_deg = g.aov_position_deg + d_aov
            g.run_start_eqx_deg = g.eqx_position_deg + d_eqx
            g.aov_position_deg = g.run_start_aov_deg
            g.eqx_position_deg = g.run_start_eqx_deg
        else:
            g.run_start_aov_deg = g.aov_position_deg
            g.run_start_eqx_deg = g.eqx_position_deg
            
        g.run_start_time = now
        g.run_start_ticks = time.ticks_ms()
        self.propagator = propagators.KeplerPropagator(
            g.orbital_altitude_km, g.orbital_inclination_deg, 
            g.orbital_eccentricity, g.orbital_periapsis_deg,
            g.run_start_aov_deg, g.run_start_eqx_deg, g.run_start_time
        )
        self.last_saved_rev_eqx = int(g.eqx_position_deg // 360)
        self.last_saved_rev_aov = int(g.aov_position_deg // 360)
        self.initialized = True

    def on_encoder_rotate(self, delta):
        # Apply accelerated nudging policy
        delta = self.nudge_manager.get_delta(delta)
        
        if self.nudge_target == 0:
            g.run_start_aov_deg += delta
            if self.propagator: self.propagator.nudge_aov(delta)
        else:
            g.run_start_eqx_deg += delta
            if self.propagator: self.propagator.nudge_eqx(delta)
    
    def on_encoder_press(self):
        self.nudge_target = (self.nudge_target + 1) % 2
    
    def on_confirm(self):
        self.tracking = not self.tracking
        if not self.tracking:
            if g.aov_motor: g.aov_motor.stop()
            if g.eqx_motor: g.eqx_motor.stop()
        return None
        
    def on_back(self):
        # Note: on_back shouldn't call save_state() directly as orbigator.py 
        # handles it after the mode transition is confirmed.
        return MenuMode()
    
    def update(self, now_ms):
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
            # Diagnostic: Check for mathematical jumps in the propagator targets
            diff_aov = abs(aov_angle - self.last_target_aov)
            diff_eqx = abs(eqx_angle - self.last_target_eqx)
            
            if self.last_command_ticks != 0: # Skip first run diagnostic
                # Ignore jumps that look like a 360->0 or 0->360 wrap
                is_wrap_aov = diff_aov > 350
                is_wrap_eqx = diff_eqx > 350
                
                if (diff_aov > 2.0 and not is_wrap_aov) or (diff_eqx > 2.0 and not is_wrap_eqx):
                    dt_ms = time.ticks_diff(now_ms, self.last_command_ticks)
                    print(f"\n[MOTION ALERT] @ TS:{now_unix} (dt={dt_ms}ms)")
                    print(f"  AoV: {self.last_target_aov:8.2f} -> {aov_angle:8.2f} (Δ={diff_aov:7.2f}°, Turn {int(aov_angle//360)})")
                    print(f"  EQX: {self.last_target_eqx:8.2f} -> {eqx_angle:8.2f} (Δ={diff_eqx:7.2f}°, Turn {int(eqx_angle//360)})")
            
            self.last_target_aov = aov_angle
            self.last_target_eqx = eqx_angle
            self.last_command_ticks = now_ms
            
            if g.eqx_motor:
                g.eqx_motor.set_nearest_degrees(eqx_angle % 360)
                g.eqx_motor.update_present_position(force=True) # Poll hardware after move
            if g.aov_motor:
                g.aov_motor.set_nearest_degrees(aov_angle % 360)
                g.aov_motor.update_present_position(force=True) # Poll hardware after move

            # Update shared state for display
            g.aov_position_deg = aov_angle
            g.eqx_position_deg = eqx_angle

        # Revolution counter: increment when crossing south point (AoV = 270°)
        current_aov_wrapped = g.aov_position_deg % 360
        # Detect south point crossing: previous < 270 and current >= 270
        if self.last_aov_wrapped < 270 and current_aov_wrapped >= 270:
            g.orbital_rev_count += 1
            print(f"South point crossed! Rev count: {g.orbital_rev_count}")
            utils.save_state()
        self.last_aov_wrapped = current_aov_wrapped
        
        # Persistence check for motor position changes
        cur_rev_eqx = int(g.eqx_position_deg // 360)
        cur_rev_aov = int(g.aov_position_deg // 360)
        if cur_rev_eqx != self.last_saved_rev_eqx or cur_rev_aov != self.last_saved_rev_aov:
            utils.save_state()
            self.last_saved_rev_eqx = cur_rev_eqx
            self.last_saved_rev_aov = cur_rev_aov
    
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
        aov_actual = g.aov_motor.present_output_degrees % 360 if g.aov_motor else 0
        eqx_target = g.eqx_position_deg % 360
        eqx_actual = g.eqx_motor.present_output_degrees % 360 if g.eqx_motor else 0
        
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
        return MenuMode()
    
    def on_back(self):
        if self.field > 0:
            self.field -= 1
            return None
        return MenuMode()
    
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
        self.items = ["Set Altitude", "Set Inclination", "Set Eccentricity", "Set Periapsis", "Set Rev Count", "Set Zulu Time", "Home Motors", "Calibrate EQX", "Motor ID Test", "Back"]
    
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        # Default: CW = Move Down
        move = 1 if delta > 0 else -1 if delta < 0 else 0
        self.selection = (self.selection + move) % len(self.items)
        
    def on_confirm(self):
        if self.selection == 0:
            return AltitudeEditorMode()
        elif self.selection == 1:
            return InclinationEditorMode()
        elif self.selection == 2:
            return EccentricityEditorMode()
        elif self.selection == 3:
            return PeriapsisEditorMode()
        elif self.selection == 4:
            return RevCountEditorMode()
        elif self.selection == 5:
            return DatetimeEditorMode()
        elif self.selection == 6:
            return HomingMode()
        elif self.selection == 7:
            return EQXCalibrationMode()
        elif self.selection == 8:
            print("Running Motor ID Test...")
            if g.eqx_motor: g.eqx_motor.flash_led(1)
            time.sleep_ms(500)
            if g.aov_motor: g.aov_motor.flash_led(2)
            return None
        elif self.selection == 9:
            return MenuMode()
        return None
    
    def on_back(self):
        return MenuMode()
    
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

class EQXCalibrationMode(Mode):
    """
    Manually calibrate EQX zero point by entering the TRUE physical angle using a numeric editor.
    Offset = Raw_Angle - User_Defined_True_Angle
    """
    def __init__(self):
        super().__init__()
        # Fields: 0=Sign, 1=Hundreds, 2=Tens, 3=Ones
        self.sign = 1 # 1 or -1
        self.hundreds = 0
        self.tens = 0
        self.ones = 0
        self.field = 0
        
        # Pre-populate with current logical angle if available
        if g.eqx_motor and g.eqx_motor.present_output_degrees is not None:
             curr = g.eqx_motor.present_output_degrees
             val = int(round(curr))
             
             if val < 0:
                 self.sign = -1
                 val = abs(val)
             else:
                 self.sign = 1
                 
             val = val % 360 # Wrap to safe range
             if val > 180:   # Prefer -180 to 180 representation
                 val = val - 360
                 self.sign = -1
                 val = abs(val)
                 
             self.hundreds = (val // 100) % 10
             self.tens = (val // 10) % 10
             self.ones = val % 10 
        
    def on_encoder_rotate(self, delta):
        delta = input_utils.normalize_encoder_delta(delta)
        d = delta
        
        if self.field == 0:
            if d != 0: self.sign *= -1
        elif self.field == 1:
            self.hundreds = (self.hundreds + d) % 2 # 0-1
        elif self.field == 2:
            self.tens = (self.tens + d) % 10
        elif self.field == 3:
            self.ones = (self.ones + d) % 10
            
    def on_encoder_press(self):
        self.field = (self.field + 1) % 4
        
    def on_confirm(self):
        if self.field < 3:
            self.field += 1
            return None
            
        # 1. Calculate the user-specified TRUE angle
        user_deg = float(self.sign * (self.hundreds * 100 + self.tens * 10 + self.ones))
        
        if not g.eqx_motor:
            print("No EQX motor to calibrate")
            return SettingsMode(selection=7)
            
        # 2. Get current Raw angle
        # Current logic: present_deg = raw - offset
        # So: raw = present_deg + offset
        current_offset = g.eqx_motor.offset_degrees
        current_logical = g.eqx_motor.get_angle_degrees() # This uses current offset
        if current_logical is None: current_logical = 0.0
        
        raw_deg = current_logical + current_offset
        
        # 3. Calculate NEW offset
        # Target: user_deg = raw_deg - new_offset
        # => new_offset = raw_deg - user_deg
        new_offset = raw_deg - user_deg
        
        print(f"Calib: User={user_deg} Raw={raw_deg} OldOff={current_offset} NewOff={new_offset}")
        
        # 4. Apply and Save
        g.eqx_motor.offset_degrees = new_offset
        
        # Save to hardware config
        success = utils.save_motor_calibration("eqx", new_offset)
        
        if success:
             print("Calibration Saved.")
        
        return SettingsMode(selection=7)
        
    def on_back(self):
        if self.field > 0:
            self.field -= 1
            return None
        return SettingsMode(selection=7)

    def render(self, disp):
        disp.fill(0)
        disp.text("CALIBRATE EQX", 0, 0)
        
        # Draw editor
        # Format: [+/-] [0] [0] [0]
        x_base = 20
        y_pos = 20
        
        # Sign
        s_char = "E" if self.sign > 0 else "W"
        if self.field == 0:
            disp.fb.fill_rect(x_base, y_pos-1, 10, 10, 1)
            disp.fb.text(s_char, x_base+1, y_pos, 0)
        else:
            disp.fb.text(s_char, x_base+1, y_pos, 1)
            
        # Hundreds
        if self.field == 1:
            disp.fb.fill_rect(x_base+12, y_pos-1, 10, 10, 1)
            disp.fb.text(str(self.hundreds), x_base+13, y_pos, 0)
        else:
            disp.fb.text(str(self.hundreds), x_base+13, y_pos, 1)
            
        # Tens
        if self.field == 2:
            disp.fb.fill_rect(x_base+24, y_pos-1, 10, 10, 1)
            disp.fb.text(str(self.tens), x_base+25, y_pos, 0)
        else:
            disp.fb.text(str(self.tens), x_base+25, y_pos, 1)
            
        # Ones
        if self.field == 3:
            disp.fb.fill_rect(x_base+36, y_pos-1, 10, 10, 1)
            disp.fb.text(str(self.ones), x_base+37, y_pos, 0)
        else:
            disp.fb.text(str(self.ones), x_base+37, y_pos, 1)
            
        disp.text("deg", x_base+50, y_pos)
        
        # Show Current Raw for reference
        # We need raw, which is (present + offset)
        raw_val = 0.0
        if g.eqx_motor:
             curr = g.eqx_motor.present_output_degrees
             if curr is None: curr = 0.0
             raw_val = curr + g.eqx_motor.offset_degrees
             
        disp.text(f"Raw: {raw_val:.1f}", 0, 40)
        disp.text("Confirm to Set", 0, 54)
        disp.show()

class HomingMode(Mode):
    """Commands motors to zero position."""
    def __init__(self):
        super().__init__()
        self.start_time = time.ticks_ms()
        self.sent_command = False
        self.success = False
        
    def enter(self):
        print("Homing motors...")
        
    def update(self, dt):
        # Send command once
        if not self.sent_command:
            if g.eqx_motor: g.eqx_motor.home(0)
            if g.aov_motor: g.aov_motor.home(90)
            self.sent_command = True
            
        # Poll actual positions
        if g.aov_motor: g.aov_motor.update_present_position()
        if g.eqx_motor: g.eqx_motor.update_present_position()
        
        # Check actual positions
        aov = g.aov_motor.present_output_degrees if g.aov_motor else 0
        eqx = g.eqx_motor.present_output_degrees if g.eqx_motor else 0
        
        # Consider complete if both within 1 degrees of 0
        if abs(aov) < 1.0 and abs(eqx) < 1.0:
            self.success = True
            
    def on_back(self):
        if not self.success:
            g.aov_motor.stop()
            g.eqx_motor.stop()
            
        return SettingsMode(selection=6)  # Home Motors is index 6
        
    def on_confirm(self):
        return SettingsMode(selection=6)
        
    def render(self, disp):
        disp.fill(0)
        
        # Show actual positions
        aov = utils.wrap_phase_deg(g.aov_motor.present_output_degrees if g.aov_motor else 0)
        eqx = utils.wrap_phase_deg(g.eqx_motor.present_output_degrees if g.eqx_motor else 0)
        
        if self.success:
            disp.text("HOMING COMPLETE", 0, 10)
            disp.text("Motors at ZERO", 0, 22)
            disp.text("Press Confirm", 0, 40)
        else:
            disp.text("HOMING MOTORS...", 0, 10)
            disp.text("Please wait", 0, 22)
        
        disp.text(f"A:{aov:.1f} E:{eqx:.1f}", 0, 54)
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
        return SettingsMode(selection=0)  # Altitude is index 0
        
    def on_back(self):
        return SettingsMode(selection=0)
        
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
        return SettingsMode(selection=1)  # Inclination is index 1
        
    def on_back(self):
        return SettingsMode(selection=1)
        
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
        return self.next_mode
        
    def on_back(self):
        if self.field > 0:
            self.field -= 1
            return None
        return self.next_mode
        
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
        return SettingsMode(selection=2)  # Eccentricity is index 2
        
    def on_back(self):
        return SettingsMode(selection=2)
        
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
        return SettingsMode(selection=3)  # Periapsis is index 3
        
    def on_back(self):
        return SettingsMode(selection=3)
        
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
        return SettingsMode(selection=4)  # Rev Count is index 4
        
    def on_back(self):
        if self.field > 0:
            self.field -= 1
            return None
        return SettingsMode(selection=4)
        
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
        
        return MenuMode()  # Return to menu
        
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
        self.nudge_manager = input_utils.NudgeManager()
        
        # Check WiFi availability
        try:
            import network
            wlan = network.WLAN(network.STA_IF)
            self.has_wifi = True
        except:
            self.has_wifi = False
            print("SGP4 Mode: WiFi not available - TLE refresh disabled")
        
    def enter(self):
        """Initialize SGP4 tracking mode."""
        g.current_mode_id = "SGP4"
        
        # Re-assert speed limits for safety
        if g.aov_motor:
            g.aov_motor.set_speed_limit(2)
        if g.eqx_motor:
            g.eqx_motor.set_speed_limit(10)
        from satellite_catalog import get_satellite_count, get_satellite_name
        import sgp4
        import orb_utils as utils
        
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
        import orb_utils as utils
        
        self.satellite_index = index
        self.satellite_name = get_satellite_name(index)
        norad_id = get_satellite_norad(index)
        
        # Check if TLE is in cache
        if self.satellite_name in self.tle_cache:
            tle_data = self.tle_cache[self.satellite_name]
            line1 = tle_data["line1"]
            line2 = tle_data["line2"]
            last_fetch = tle_data.get("last_fetch", 0)
            self.tle_age = utils.get_tle_age_str(last_fetch)
            
            # Check if update needed
            if utils.tle_needs_update(last_fetch):
                print(f"TLE for {self.satellite_name} is stale, needs update")
                self.tle_age += " OLD"
        else:
            # No TLE in cache - need to fetch
            print(f"No TLE for {self.satellite_name}, need to fetch")
            self.tle_age = "missing"
            return
        
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
        import propagators
        self.inclination = inc
        self.sgp4 = sgp4.SGP4()
        self.sgp4.init(epoch_year, epoch_day, bstar, inc, raan, ecc, argp, m, n)
        self.propagator = propagators.SGP4Propagator(self.sgp4)
        self.tracking = True # Start tracking automatically on selection
        
        print(f"Loaded {self.satellite_name}: epoch {epoch_year} day {epoch_day:.2f}")
    
    def _fetch_tle(self):
        """Fetch TLE data via WiFi (WiFi hardware required)."""
        if not self.has_wifi:
            return
            
        # ... logic ... (keep existing _fetch_tle code, or skipping it if I don't see it)
        # Wait, I am replacing LINES, I need to see the file to append safely or insert.
        # I'll rely on ViewFile response first.
    
    def set_manual_tle(self, name, line1, line2):
        """Set TLE manually from API."""
        import sgp4
        import orb_utils as utils
        
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
            self.propagator = propagators.SGP4Propagator(self.sgp4)
            
            print(f"Manual TLE set for {name}")
            return True, "TLE loaded successfully"
        except Exception as e:
            print(f"Manual TLE error: {e}")
            return False, str(e)
        import json
        import time
        
        # Check for WiFi hardware first
        if not self.has_wifi:
            print("WiFi not available - cannot fetch TLE")
            g.disp.fill(0)
            g.disp.text("No WiFi!", 0, 0)
            g.disp.text("Cannot fetch TLE", 0, 12)
            g.disp.show()
            time.sleep(2)
            return False # Indicate failure
        
        self.fetching = True
        g.disp.fill(0)
        g.disp.text("Fetching TLE...", 0, 0)
        g.disp.text("Please wait", 0, 12)
        g.disp.show()
        print(f"Fetching TLE for {self.satellite_name}...")
        
        # Load WiFi config
        try:
            with open("wifi_config.json", "r") as f:
                config = json.load(f)
            ssid = config["ssid"]
            password = config["password"]
        except:
            print("No WiFi config found - run wifi_setup.py first")
            self.fetching = False
            return False
        
        # Connect to WiFi
        import wifi_setup
        ip = wifi_setup.connect_wifi(ssid, password)
        if not ip:
            print("WiFi connection failed")
            self.fetching = False
            return False
        
        print(f"Connected to {ssid} ({ip})")
        
        # Fetch TLE
        import tle_fetch
        import orb_utils as utils
        tle_data = tle_fetch.fetch_tle(self.satellite_name)
        if not tle_data:
            print("TLE fetch failed")
            self.fetching = False
            return False
        
        # Update cache
        name, line1, line2 = tle_data
        self.tle_cache[self.satellite_name] = {
            "line1": line1,
            "line2": line2,
            "last_fetch": int(utils.get_timestamp())
        }
        utils.save_tle_cache(self.tle_cache)
        
        # Reload satellite
        self._load_satellite(self.satellite_index)
        
        self.fetching = False
        print(f"✓ TLE updated for {self.satellite_name}")
        return True
    
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
            if self.has_wifi:
                self._fetch_tle()
            else:
                # No WiFi hardware
                import time
                print("WiFi not available")
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
        return MenuMode()
    
    def update(self, now_ms):
        """Update satellite position and motors."""
        if not self.propagator or not self.tracking:
            return
        
        # print(f"SGP4 Update: {getattr(self, 'satellite_name', 'UNK')} track={self.tracking}")
        
        # 1. Update target orientation from propagator (cache by second)
        now_unix = utils.get_timestamp()
        if now_unix != self.last_unix:
            self.last_aov_angle, self.last_eqx_angle, self.lat_deg, self.lon_deg = self.propagator.get_aov_eqx(now_unix)
            self.alt_km = self.propagator.get_altitude()
            
            # print(f"SGP4 Calc: AoV={self.last_aov_angle:.1f} EQX={self.last_eqx_angle:.1f} | Lat={self.lat_deg:.2f} Lon={self.lon_deg:.2f} @ {now_unix}")

            g.aov_position_deg = self.last_aov_angle
            g.eqx_position_deg = self.last_eqx_angle
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
                    print(f"\n[SGP4 JUMP] {self.satellite_name} @ {now_unix} (dt={dt_ms}ms)")
                    print(f"  AoV: {self.last_target_aov:7.2f} -> {aov_angle:7.2f} (Δ={diff_aov:6.2f}°)")
                    print(f"  EQX: {self.last_target_eqx:7.2f} -> {eqx_angle:7.2f} (Δ={diff_eqx:6.2f}°)")
            
            self.last_target_aov = aov_angle
            self.last_target_eqx = eqx_angle
            self.last_command_ticks = now_ms
            
            if g.aov_motor:
                g.aov_motor.set_nearest_degrees(aov_angle)
                g.aov_motor.update_present_position(force=True) # Poll hardware after move
            
            if g.eqx_motor:
                g.eqx_motor.set_nearest_degrees(eqx_angle)
                g.eqx_motor.update_present_position(force=True) # Poll hardware after move
    
    def render(self, disp):
        """Render SGP4 mode display."""
        disp.fill(0)
        
        if not self.satellite_name:
            disp.text("No Satellite", 0, 0)
            disp.text("Data", 0, 12)
            disp.show()
            return
        
        # Title
        mode_str = "TRACKING" if self.tracking else "SELECT"
        disp.text(f"{mode_str}", 0, 0)
        
        # Satellite name (truncate if needed)
        sat_name = self.satellite_name[:16]
        disp.text(sat_name, 0, 12)
        
        if self.fetching:
            # Show fetching message
            disp.text("Fetching TLE...", 0, 24)
            disp.text("Please wait", 0, 36)
        elif self.tracking and self.sgp4:
            # Catch-up status based on physical hardware feedback
            catching_up = False
            # Use same robust comparison as OrbitMode
            aov_target = g.aov_position_deg % 360
            aov_actual = g.aov_motor.present_output_degrees % 360 if g.aov_motor else 0
            eqx_target = g.eqx_position_deg % 360
            eqx_actual = g.eqx_motor.present_output_degrees % 360 if g.eqx_motor else 0

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
                
            if catching_up:
                # Show actual positions during catch-up (replacing Lat/Lon area)
                act_a = aov_actual % 360
                act_e = eqx_actual % 360
                disp.text("** CATCHING UP **", 0, 24)
                disp.text(f"A{act_a:3.0f} / E{act_e:3.0f} Act", 0, 34)
                disp.degree(4*8, 34)  # After A###
                disp.degree(13*8, 34) # After E###
            else:
                # Show position
                la_str = f"Lat: {self.lat_deg:+.2f}"
                disp.text(la_str, 0, 24)
                disp.degree(len(la_str)*8 + 1, 24)
                
                lo_str = f"Lon: {self.lon_deg:+.2f}"
                disp.text(lo_str, 0, 34)
                disp.degree(len(lo_str)*8 + 1, 34)
            
            disp.text(f"Alt: {self.alt_km:.0f}km", 0, 44)
            disp.text(f"TLE: {self.tle_age}", 0, 54)
        else:
            # Selection mode - show instructions
            disp.text("Dial: Select", 0, 30)
            disp.text("Press: Track", 0, 42)
            disp.text(f"TLE: {self.tle_age}", 0, 54)
        
        disp.show()

