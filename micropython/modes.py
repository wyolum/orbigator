"""
Orbigator UI Modes
Mode-based architecture for clean UI state management
"""

import orb_globals as g
import orb_utils as utils
import time

class Mode:
    """Base class for UI modes."""
    
    def on_encoder_rotate(self, delta):
        pass
    
    def on_encoder_press(self):
        pass
    
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
        self.selection = 0
        self.items = ["Orbit!", "Align EQX", "Align AoV", "Set Period", "Settings"]
    
    def on_encoder_rotate(self, delta):
        # Default: CW (delta > 0) = Move Down (selection increases)
        move = 1 if delta > 0 else -1 if delta < 0 else 0
        self.selection = (self.selection + move) % len(self.items)
        print(f"Menu: {self.items[self.selection]}")
    
    def on_confirm(self):
        if self.selection == 0:
            return OrbitMode()
        elif self.selection == 1:
            return MotorEditorMode(target=0) # EQX
        elif self.selection == 2:
            return MotorEditorMode(target=1) # AoV
        elif self.selection == 3:
            return PeriodEditorMode()
        elif self.selection == 4:
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
        self.nudge_target = 0
        self.initialized = False
        self.last_saved_rev_eqx = 0
        self.last_saved_rev_aov = 0
    
    def enter(self):
        """Initialize orbital tracking and catch up if needed."""
        # 1. Sync internal Pico RTC to external RTC to ensure we have high-res local time
        utils.sync_system_time(g.rtc)
        
        # 2. Load state and reconstruct positions from hardware
        saved_ts, saved_eqx, saved_aov = utils.load_state()
        
        # 3. Calculate current rates
        aov_rate, eqx_rate_sec, eqx_rate_day, period_min = utils.compute_motor_rates(g.orbital_altitude_km)
        g.aov_rate_deg_sec = aov_rate
        g.eqx_rate_deg_sec = eqx_rate_sec
        g.eqx_rate_deg_day = eqx_rate_day
        g.orbital_period_min = period_min
        
        # 4. Calculate elapsed time since last save using high-res system time
        now = utils.get_timestamp()
        
        elapsed = now - saved_ts if saved_ts > 0 else 0
        print(f"Time Check: HighResNow={now:.3f}, SavedTS={saved_ts:.3f}, Gap={elapsed:.3f}s")
        
        if 0 < elapsed < 86400: # Only catch up if gap is reasonable (less than 1 day)
            # Calculate target absolute positions (where we SHOULD be physically)
            target_aov_abs = saved_aov + (aov_rate * elapsed)
            target_eqx_abs = saved_eqx + (eqx_rate_sec * elapsed)
            
            # Use modulo for the motor command phase
            target_aov_phase = target_aov_abs % 360
            target_eqx_phase = target_eqx_abs % 360
            
            print(f"  Catching up to: AoV={target_aov_abs:.3f}°, EQX={target_eqx_abs:.3f}°")
            
            # Set safe catch-up speed
            if g.aov_motor: g.aov_motor.set_speed_limit(10)
            if g.eqx_motor: g.eqx_motor.set_speed_limit(10)
            
            # Move motors
            if g.aov_motor: g.aov_motor.set_nearest_degrees(target_aov_phase)
            if g.eqx_motor: g.eqx_motor.set_nearest_degrees(target_eqx_phase)
            
            # Anchor current session to this snapshot
            g.run_start_aov_deg = target_aov_abs
            g.run_start_eqx_deg = target_eqx_abs
        else:
            print("Catch-up skipped or large gap.")
            g.run_start_aov_deg = g.aov_position_deg
            g.run_start_eqx_deg = g.eqx_position_deg
            
        g.run_start_time = now
        
        # Initial rev tracking for persistence
        self.last_saved_rev_eqx = int(g.eqx_position_deg // 360)
        self.last_saved_rev_aov = int(g.aov_position_deg // 360)
        
        self.initialized = True
        print(f"Orbit logic active: AoV={g.aov_rate_deg_sec:.6f} deg/s, EQX={g.eqx_rate_deg_sec:.6f} deg/s")
    
    def on_encoder_rotate(self, delta):
        d = delta # CW = Nudge Forward
        if self.nudge_target == 0:
            g.run_start_aov_deg += d * 1.0
            print(f"AoV nudge: {d:+.0f} deg")
        else:
            g.run_start_eqx_deg += d * 1.0
            print(f"EQX nudge: {d:+.0f} deg")
    
    def on_encoder_press(self):
        self.nudge_target = (self.nudge_target + 1) % 2
        print(f"Nudge: {'EQX' if self.nudge_target == 1 else 'AoV'}")
    
    def on_confirm(self):
        return None
        
    def on_back(self):
        utils.save_state()
        return MenuMode()
    
    def update(self, dt):
        if not self.initialized:
            return
        
        # Use high-resolution system time for smooth integration
        now = utils.get_timestamp()
        elapsed = now - g.run_start_time
        
        g.aov_position_deg = g.run_start_aov_deg + (g.aov_rate_deg_sec * elapsed)
        g.eqx_position_deg = g.run_start_eqx_deg + (g.eqx_rate_deg_sec * elapsed)
        
        if g.aov_motor:
            g.aov_motor.set_angle_degrees(g.aov_position_deg)
        if g.eqx_motor:
            g.eqx_motor.set_angle_degrees(g.eqx_position_deg)
            
        # Revolution-based persistence: Save state when a motor passes 360° boundary
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
        
        disp.text(f"Alt: {g.orbital_altitude_km:.3f} km", 0, 34)
        disp.text(f"AoV: {g.aov_position_deg % 360:.1f} deg", 0, 46)
        disp.text(f"EQX: {g.eqx_position_deg % 360:.1f} deg", 0, 56)
        disp.show()


class PeriodEditorMode(Mode):
    """Editor for orbital period in hh:mm:ss format."""
    
    def __init__(self):
        total_sec = int(g.orbital_period_min * 60)
        self.hh = total_sec // 3600
        self.mm = (total_sec % 3600) // 60
        self.ss = total_sec % 60
        self.field = 0 # 0=H, 1=M, 2=S
    
    def on_encoder_rotate(self, delta):
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
    
    def __init__(self):
        self.selection = 0
        self.items = ["Set Altitude", "Set Inclination", "Set Zulu Time", "Motor ID Test", "Back"]
    
    def on_encoder_rotate(self, delta):
        # Default: CW = Move Down
        move = 1 if delta > 0 else -1 if delta < 0 else 0
        self.selection = (self.selection + move) % len(self.items)
        
    def on_confirm(self):
        if self.selection == 0:
            return AltitudeEditorMode()
        elif self.selection == 1:
            return InclinationEditorMode()
        elif self.selection == 2:
            return DatetimeEditorMode()
        elif self.selection == 3:
            print("Running Motor ID Test...")
            if g.eqx_motor: g.eqx_motor.flash_led(1)
            time.sleep_ms(500)
            if g.aov_motor: g.aov_motor.flash_led(2)
            return None
        elif self.selection == 4:
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

class AltitudeEditorMode(Mode):
    """Editor for orbital altitude."""
    def __init__(self):
        self.alt = int(g.orbital_altitude_km)
        
    def on_encoder_rotate(self, delta):
        d = delta * 10 # CW = increase
        self.alt = max(200, min(2000, self.alt + d))
        
    def on_confirm(self):
        g.orbital_altitude_km = float(self.alt)
        g.orbital_period_min = utils.compute_period_from_altitude(g.orbital_altitude_km)
        utils.save_state()
        return SettingsMode()
        
    def on_back(self):
        return SettingsMode()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("SET ALTITUDE", 0, 0)
        alt_str = f"{self.alt} km"
        w = len(alt_str) * 8
        disp.fb.fill_rect(40, 24, w+4, 10, 1)
        disp.fb.text(alt_str, 42, 25, 0)
        disp.text("Step: 10 km", 10, 45)
        disp.text("Confirm to Save", 10, 56)
        disp.show()

class InclinationEditorMode(Mode):
    """Editor for orbital inclination."""
    def __init__(self):
        # Store as 10x integer for easy encoder step (0.1 deg)
        self.inc_x10 = int(g.orbital_inclination_deg * 10)
        
    def on_encoder_rotate(self, delta):
        d = delta # CW = increase
        # Range 0 to 180 (most common 0 to 99)
        self.inc_x10 = max(0, min(1800, self.inc_x10 + d))
        
    def on_confirm(self):
        g.orbital_inclination_deg = float(self.inc_x10) / 10.0
        utils.save_state()
        return SettingsMode()
        
    def on_back(self):
        return SettingsMode()
        
    def render(self, disp):
        disp.fill(0)
        disp.text("SET INCLINATION", 0, 0)
        inc_str = f"{self.inc_x10/10.0:.1f} deg"
        w = len(inc_str) * 8
        disp.fb.fill_rect(30, 24, w+4, 10, 1)
        disp.fb.text(inc_str, 32, 25, 0)
        disp.text("Step: 0.1 deg", 10, 45)
        disp.text("Confirm to Save", 10, 56)
        disp.show()

class DatetimeEditorMode(Mode):
    """Editor for system date and time."""
    def __init__(self, next_mode=None):
        self.next_mode = next_mode if next_mode else SettingsMode()
        t = utils.get_timestamp(g.rtc)
        # Pico 2000 epoch: (Y, M, D, H, M, S, WD, YD)
        lt = time.localtime(t)
        self.year = lt[0] if lt[0] >= 2024 else 2024
        self.month = lt[1]
        self.day = lt[2]
        self.hour = lt[3]
        self.minute = lt[4]
        self.field = 0 # 0=Y, 1=M, 2=D, 3=H, 4=Min
        
    def on_encoder_rotate(self, delta):
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
        utils.set_datetime(self.year, self.month, self.day, self.hour, self.minute, 0, g.rtc)
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
        
        date_str = "{:04d}-{:02d}-{:02d}".format(self.year, self.month, self.day)
        time_str = "{:02d}:{:02d}Z".format(self.hour, self.minute)
        
        disp.text(f"D: {date_str}", 0, 20)
        disp.text(f"T: {time_str}", 0, 32)
        
        # Visual cursor
        if self.field <= 2: # Date fields
             x = 24 + (self.field * 24 if self.field == 0 else 40 + (self.field-1)*24)
             # Simplify: just show field name
             pass
        
        fields = ["Year", "Month", "Day", "Hour", "Minute"]
        disp.text(f"Edit: {fields[self.field]}", 0, 48)
        disp.text("Confirm >> Next", 0, 58)
        disp.show()

class MotorEditorMode(Mode):
    """Manual adjustment of absolute motor positions."""
    def __init__(self, target=0):
        self.target = target # 0=EQX, 1=AoV
        self.pos = g.eqx_position_deg if target == 0 else g.aov_position_deg
        self.label = "SET EQX ANGLE" if target == 0 else "SET AOV ANGLE"
        
    def on_encoder_rotate(self, delta):
        d = delta # CW = Increase
        self.pos += d
        # Live movement for alignment
        m = g.eqx_motor if self.target == 0 else g.aov_motor
        if m:
            m.set_nearest_degrees(self.pos)
            
    def on_confirm(self):
        if self.target == 0: g.eqx_position_deg = self.pos
        else: g.aov_position_deg = self.pos
        utils.save_state()
        return MenuMode() # Return to main menu instead of settings
        
    def on_back(self):
        return MenuMode()
        
    def render(self, disp):
        disp.fill(0)
        disp.text(self.label, 0, 0)
        pos_str = f"{self.pos:.1f} deg"
        w = len(pos_str) * 8
        disp.fb.fill_rect(20, 24, w+4, 10, 1)
        disp.fb.text(pos_str, 22, 25, 0)
        
        disp.text("Dial to Move Motor", 0, 45)
        disp.text("Confirm to Save", 0, 56)
        disp.show()
