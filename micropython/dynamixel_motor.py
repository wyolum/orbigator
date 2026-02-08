"""
DYNAMIXEL Motor - Extended Position Mode with EQX Recovery
==========================================================
Supports multi-turn positioning (>360°) and RTC SRAM recovery for EQX.
"""

from dynamixel_extended_utils import (
    read_present_position, write_dword, write_byte, ping_motor,
    set_extended_mode
)
import time
import struct


class DynamixelMotor:
    """Dynamixel motor controller with extended position mode and EQX recovery."""
    
    # Constants
    TICKS_PER_REV = 4096
    TICKS_PER_DEGREE = 4096.0 / 360.0
    
    # Register addresses
    ADDR_TORQUE_ENABLE = 64
    ADDR_GOAL_POSITION = 116
    ADDR_PROFILE_VELOCITY = 112
    ADDR_POSITION_P_GAIN = 84
    ADDR_POSITION_I_GAIN = 82
    ADDR_POSITION_D_GAIN = 80
    
    # SRAM Checkpoint Constants
    SRAM_MAGIC = 0xDEAD
    SRAM_ADDR_EQX = 0x14
    CHECKPOINT_INTERVAL_TICKS = 512  # 45 degrees
    
    def __init__(self, motor_id, name, gear_ratio=1.0, rtc=None, 
                 offset_degrees=0.0, direction=None, recovery_direction=1,
                 last_known_pos=None, last_abs_ticks=None):
        """
        Initialize motor with 'mod 4096' hardware and absolute software tracking.
        """
        self.motor_id = motor_id
        self.name = name
        self.gear_ratio = gear_ratio
        self.rtc = rtc
        self.offset_degrees = offset_degrees
        self.direction = direction # None (Any), 1 (Forward Only), -1 (Reverse Only)
        self.recovery_direction = recovery_direction
        self._last_checkpoint_ticks = 0
        
        # 1. Reset hardware counter to current phase (0-4095)
        self._init_hardware()
        
        # 2. Read hardware starting point (will be 0-4095 due to reset)
        h_pos = read_present_position(motor_id)
        if h_pos is None:
            raise RuntimeError(f"Failed to read motor {motor_id}")
            
        # 3. Recover software absolute position (stitched from SRAM)
        if self.name == "EQX" and self.rtc:
            self._raw_ticks = self._try_recovery(h_pos)
        else:
            self._raw_ticks = h_pos
            
        # 4. Calculate hardware/software offset to prevent jumps
        # hw_pos = sw_pos + offset => offset = hw_pos - sw_pos
        self._hw_offset = h_pos - self._raw_ticks
            
        self._last_checkpoint_ticks = self._raw_ticks
        self.output_degrees = (self._raw_ticks / self.TICKS_PER_REV) * 360.0 / self.gear_ratio
        
        print(f"  [{name}] Init: software={self._raw_ticks}, hardware={h_pos}, offset={self._hw_offset}")

    @staticmethod
    def wrap_180(deg):
        """Wrap degrees to +/- 180 range."""
        return (deg + 180) % 360 - 180

    def _init_hardware(self):
        """Reset hardware counter to phase (0-4095)."""
        from dynamixel_extended_utils import write_byte, clear_multi_turn, ping_motor
        
        if not ping_motor(self.motor_id):
            print(f"  [{self.name}] Error: Motor {self.motor_id} not responding")
            return

        # FORCE HARDWARE RESET TO PHASE (0-4095)
        write_byte(self.motor_id, 64, 0) # Torque OFF
        time.sleep_ms(50)
        
        # Try Instruction 0x0A (Clear Multi-Turn) - clean way to reset counter
        if clear_multi_turn(self.motor_id):
             print(f"  [{self.name}] Counter cleared via Instruction 0x0A")
        else:
            # Fallback for older firmware
            write_byte(self.motor_id, 11, 3) # Mode 3 (Standard)
            time.sleep_ms(100)
            write_byte(self.motor_id, 11, 4) # Mode 4 (Extended)
            time.sleep_ms(100)
            print(f"  [{self.name}] Counter reset via Mode toggle")
        
        write_byte(self.motor_id, 64, 1) # Torque ON
        time.sleep_ms(50)

    def _try_recovery(self, current_phase_ticks):
        """Recover wrapped position from RTC SRAM with deep telemetry."""
        data = self.rtc.read_sram(self.SRAM_ADDR_EQX, 12)
        if not data:
            print(f"  [{self.name}] No SRAM data found")
            return current_phase_ticks
            
        try:
            timestamp, magic, s_phase, s_deg = struct.unpack("<IHHf", data)
            if magic != self.SRAM_MAGIC:
                print(f"  [{self.name}] SRAM magic mismatch: {magic:04X}")
                return current_phase_ticks
            
            # Phase Stitch Logic (short path delta)
            CPR = self.TICKS_PER_REV
            delta_ticks = (current_phase_ticks - s_phase + CPR//2) % CPR - CPR//2
            
            # Convert motor delta to gear degrees
            delta_gear_deg = (delta_ticks / self.gear_ratio / self.TICKS_PER_DEGREE)
            recovered_eqx = self.wrap_180(s_deg + delta_gear_deg)
            
            # Reconstruct absolute software ticks
            recovered_abs_ticks = int(recovered_eqx * self.gear_ratio * self.TICKS_PER_DEGREE)
            
            print(f"  [{self.name}] RECOVERY TELEMETRY (T={timestamp}):")
            print(f"     SRAM: {s_deg:.2f}° @ phase {s_phase}")
            print(f"     BOOT: phase {current_phase_ticks} (dt={delta_ticks} ticks, {delta_gear_deg:.2f} deg)")
            print(f"     FINAL: {recovered_eqx:.2f}° (wrapped)")
            
            return recovered_abs_ticks
        except Exception as e:
            print(f"  [{self.name}] Recovery error: {e}")
            return current_phase_ticks

    def _save_checkpoint(self, h_pos_sync=None):
        """Save current position with precise hardware-software sync."""
        if self.rtc and self.name == "EQX":
            import utime
            dt = self.rtc.datetime()
            now = utime.mktime(dt) if dt else 0
            
            if h_pos_sync is None:
                from dynamixel_extended_utils import read_present_position
                h_pos_sync = read_present_position(self.motor_id)
            
            if h_pos_sync is not None:
                # Calculate software degrees exactly for this hardware tick
                s_ticks = h_pos_sync - self._hw_offset
                deg = (s_ticks / self.TICKS_PER_REV) * 360.0 / self.gear_ratio
                
                gear_phase = self.wrap_180(deg)
                phase_mod = h_pos_sync % self.TICKS_PER_REV
                
                data = struct.pack("<IHHf", now, self.SRAM_MAGIC, int(phase_mod), gear_phase)
                if self.rtc.write_sram(self.SRAM_ADDR_EQX, data):
                    self._last_checkpoint_ticks = s_ticks
                    # print(f"  [{self.name}] Saved: {gear_phase:.2f}° @ {phase_mod}")

    @property
    def position(self):
        """Current position in output degrees."""
        return self.output_degrees
    
    @property
    def position_ticks(self):
        """Get current position in raw ticks."""
        return self._raw_ticks
    
    def update_position(self):
        """Read hardware and update software position."""
        from dynamixel_extended_utils import read_present_position
        h_pos = read_present_position(self.motor_id)
        if h_pos is not None:
            # Sync software absolute tick from hardware
            self._raw_ticks = h_pos - self._hw_offset
            self.output_degrees = (self._raw_ticks / self.TICKS_PER_REV) * 360.0 / self.gear_ratio
            
            # Checkpoint every 45 degrees
            if self.name == "EQX" and abs(self._raw_ticks - self._last_checkpoint_ticks) >= self.CHECKPOINT_INTERVAL_TICKS:
                self._save_checkpoint(h_pos)
                
        return self.output_degrees
    
    def set_position(self, target_degrees, direction_override=None):
        """
        Set absolute position in degrees.
        Handles calibration offset and optional direction constraints.
        """
        from dynamixel_extended_utils import write_dword
        
        # Apply calibration offset to target
        target_calibrated = target_degrees + self.offset_degrees
        
        # Calculate optimal path
        current = self.output_degrees + self.offset_degrees # Internal tracking is raw
        delta = self.wrap_180(target_calibrated - current)
        
        # Apply direction constraints (Cable Safety)
        effective_dir = direction_override if direction_override is not None else self.direction
        
        if effective_dir == 1: # Forward Only
            if delta < -0.1: delta += 360 # If negative move, go 'long way'
        elif effective_dir == -1: # Reverse Only
            if delta > 0.1: delta -= 360
            
        safe_target = current + delta
        
        # Translate to hardware space via offset
        target_abs_ticks = int(safe_target * self.gear_ratio * self.TICKS_PER_DEGREE)
        hw_goal = target_abs_ticks + self._hw_offset
        
        if write_dword(self.motor_id, 116, int(hw_goal)):
            return True
        return False
    
    def set_speed(self, speed_percent):
        """
        Set profile velocity (0-100%).
        For XL330-M288-T, max velocity is ~445 (at 5V).
        """
        from dynamixel_extended_utils import write_dword
        val = int((speed_percent / 100.0) * 445)
        # Ensure it's at least 1 if speed_percent > 0 to prevent 0 (infinity) speed
        if speed_percent > 0 and val == 0: val = 1
        
        if write_dword(self.motor_id, 112, val):
            # Telemetry for verification
            print(f"  [{self.name}] Profile Velocity set to {val} ({speed_percent}%)")
            return True
        return False
    
    # --- API ALIASES for orbigator.py compatibility ---
    
    def set_speed_limit(self, speed_percent):
        """Alias for set_speed for orbigator.py compatibility."""
        return self.set_speed(speed_percent)
        
    def set_pid_gains(self, p=None, i=None, d=None):
        """Alias for set_pid for orbigator.py compatibility."""
        return self.set_pid(p, i, d)
        
    def update_present_position(self, force=False):
        """Alias for update_position for orbigator.py compatibility."""
        # 'force' is ignored as update_position always reads from hardware
        return self.update_position()
        
    def set_nearest_degrees(self, target_degrees, direction_override=None):
        """
        Move to target angle via shortest path (handling multiple turns).
        This updates the internal 360-mod tracking to enable continuous rotation.
        """
        current_deg = self.output_degrees
        
        # Calculate shortest delta (-180 to 180)
        delta = self.wrap_180(target_degrees - current_deg)
        
        # Apply Direction Constraints if any
        effective_dir = direction_override if direction_override is not None else self.direction
        if effective_dir == 1: # Forward Only
            if delta < -0.1: delta += 360
        elif effective_dir == -1: # Reverse Only
            if delta > 0.1: delta -= 360
            
        target_abs = current_deg + delta
        return self.set_position(target_abs, direction_override)
    
    def enable_torque(self, enable=True):
        from dynamixel_extended_utils import write_byte
        write_byte(self.motor_id, 64, 1 if enable else 0)
    
    def disable_torque(self):
        self.enable_torque(False)
    
    def ping(self):
        """Check if motor responds."""
        return ping_motor(self.motor_id)
    
    def set_pid(self, p=None, i=None, d=None):
        """Set PID gains."""
        from dynamixel_extended_utils import write_word
        if p is not None: write_word(self.motor_id, 84, p)
        if i is not None: write_word(self.motor_id, 82, i)
        if d is not None: write_word(self.motor_id, 80, d)
    
    def __repr__(self):
        return f"DynamixelMotor({self.name}, {self.output_degrees:.1f}°)"
