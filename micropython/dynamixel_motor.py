"""
DYNAMIXEL Motor Abstraction Layer for Orbigator
Mode-Locked Version: Stable Absolute Tracking with Hardware Reset Detection
"""

from dynamixel_extended_utils import (
    read_present_position, write_dword, write_byte, get_new_pos, 
    read_byte, set_extended_mode
)
import time

class DynamixelMotor:
    # Constants
    TICKS_PER_REV = 4096
    TICKS_PER_MOTOR_DEGREE = 4096.0 / 360.0
    ADDR_OPERATING_MODE = 11
    ADDR_TORQUE_ENABLE = 64
    ADDR_GOAL_POSITION = 116
    ADDR_LED = 65
    ADDR_PROFILE_VELOCITY = 112
    ADDR_POSITION_D_GAIN = 80
    ADDR_POSITION_I_GAIN = 82
    ADDR_POSITION_P_GAIN = 84
    
    def __init__(self, motor_id, name, gear_ratio=1.0, offset_degrees=0.0, 
                 direction=None, recovery_direction=None, 
                 last_known_pos=None, last_abs_ticks=None):
        self.motor_id = motor_id
        self.name = name
        self.gear_ratio = gear_ratio
        self.offset_degrees = offset_degrees
        self.direction = direction          # Movement constraint (Slew Direction)
        self.recovery_direction = recovery_direction # Turn-count resolution (Boot Direction)
        
        self.consecutive_failures = 0
        self.MAX_FAILURES_BEFORE_OFFLINE = 5
        self.current_velocity_limit = None
        self.present_output_degrees = 0.0
        self.last_present_read_ticks = 0
        
        # Absolute Mapping State
        self.absolute_ticks = 0
        self.hw_to_abs_offset = 0
        self.last_raw_ticks = 0
        
        # Turn tracking
        self.current_turn = 0
        self.on_turn_change = None
        
        # 1. Read initial hardware position
        motor_ticks = read_present_position(motor_id)
        if motor_ticks is None:
            raise RuntimeError(f"Failed to read position from motor {motor_id} ({name})")
            
        # 2. Recover multi-turn state (The "Stitch")
        recovered_abs = 0
        if last_abs_ticks is not None:
             print(f"  [{name}] Absolute Recovery: HW={motor_ticks}, Saved={last_abs_ticks}")
             recovered_abs = self._recover_abs_ticks_logic(motor_ticks, last_abs_ticks)
        elif last_known_pos is not None:
            target_motor_ticks = (last_known_pos + self.offset_degrees) * self.gear_ratio * self.TICKS_PER_MOTOR_DEGREE
            n_revs = round((target_motor_ticks - motor_ticks) / self.TICKS_PER_REV)
            recovered_abs = int(motor_ticks + (n_revs * self.TICKS_PER_REV))
            print(f"  [{name}] Legacy Recovery: Abs={recovered_abs}")
        else:
            recovered_abs = int(motor_ticks)

        # 3. Establish the Zero-Drift Offset
        # absolute_ticks = hardware_ticks + hw_to_abs_offset
        self.hw_to_abs_offset = recovered_abs - motor_ticks
        self.last_raw_ticks = motor_ticks
        self.absolute_ticks = recovered_abs
        
        # Derived orientation state
        self.output_degrees = (self.absolute_ticks * (360.0 / self.TICKS_PER_REV) / self.gear_ratio) - self.offset_degrees
        self.present_output_degrees = self.output_degrees
        self.current_turn = int(self.output_degrees // 360)
        self.last_present_read_ticks = time.ticks_ms()
        
        print(f"  [{name}] Stitched: Offset={self.hw_to_abs_offset}, Output={self.output_degrees:.2f}°")

    def _recover_abs_ticks_logic(self, raw_ticks, saved_ticks):
        """
        Bounded-delta recovery: compute unique delta from modulo.
        
        Boot recovery ALWAYS uses shortest path because:
        - Cache is written at least once per motor revolution
        - Therefore |delta| < half revolution is always correct
        """
        CPR = self.TICKS_PER_REV  # 4096
        
        saved_mod = saved_ticks % CPR
        hw_mod = raw_ticks % CPR
        d_mod = (hw_mod - saved_mod) % CPR  # 0..4095
        
        # ALWAYS use shortest path for boot recovery
        # d_mod=4095 means -1, d_mod=1 means +1
        delta = d_mod if d_mod <= (CPR // 2) else d_mod - CPR
        
        ext_now = saved_ticks + delta
        
        print(f"  [{self.name}] Recovery: saved_mod={saved_mod}, hw_mod={hw_mod}, delta={delta}")
        
        return ext_now

    def _retry_operation(self, operation, operation_name, max_retries=3):
        backoff_ms = [10, 20, 40]
        for attempt in range(max_retries):
            result = operation()
            if result is not None:
                self.consecutive_failures = 0
                return result
            if attempt < max_retries - 1:
                time.sleep_ms(backoff_ms[attempt])
        self.consecutive_failures += 1
        return None
    
    def set_speed_limit(self, velocity=100):
        if self.current_velocity_limit == velocity: return True
        success = write_dword(self.motor_id, self.ADDR_PROFILE_VELOCITY, velocity)
        if success: self.current_velocity_limit = velocity
        return success
    
    def set_nearest_degrees(self, target_degrees, direction_override=None):
        """Move to nearest stage using the stable absolute mapping."""
        # 1. Normalize and resolve target in global space
        target_degrees = target_degrees % 360
        current_sw_output = self.output_degrees
        
        # Use provided override, or instance default (Slew direction)
        effective_direction = direction_override if direction_override is not None else self.direction
        
        new_sw_output = get_new_pos(current_sw_output, target_degrees, effective_direction)
        delta_output = new_sw_output - current_sw_output
        
        # 2. Threshold check
        if abs(delta_output) < 0.05: return True

        # 3. Calculate target in hardware space
        target_abs_ticks = int(((new_sw_output + self.offset_degrees) * self.gear_ratio) * self.TICKS_PER_MOTOR_DEGREE)
        target_hw_ticks = target_abs_ticks - self.hw_to_abs_offset
        
        if abs(delta_output) > 5.0:
            print(f"  [{self.name}] Target: {target_degrees:.1f} (Path: {delta_output:+.1f}°)")
            
        def _write_op():
            return write_dword(self.motor_id, self.ADDR_GOAL_POSITION, target_hw_ticks)
        
        return self._retry_operation(_write_op, "write position")

    def get_angle_degrees(self):
        """Read current position and map via the stable offset. Detects reboots."""
        def _read_operation():
            # 1. Check Operating Mode for Reset Detection
            # If motor reboots, mode reverts to 3 (Joint). We want 4 (Extended).
            mode = read_byte(self.motor_id, self.ADDR_OPERATING_MODE)
            if mode is not None and mode != 4:
                print(f"  [{self.name}] Hardware Reset Detected! Re-initializing...")
                set_extended_mode(self.motor_id)
                write_byte(self.motor_id, self.ADDR_TORQUE_ENABLE, 1) # Ensure torque on
                
                # Re-read position after mode switch
                raw_ticks = read_present_position(self.motor_id)
                if raw_ticks is not None:
                    # RE-STITCH using specific recovery logic
                    new_abs = self._recover_abs_ticks_logic(raw_ticks, self.absolute_ticks)
                    self.hw_to_abs_offset = new_abs - raw_ticks
                    self.absolute_ticks = new_abs
                    self.last_raw_ticks = raw_ticks
                    print(f"  [{self.name}] Re-stitched: Offset={self.hw_to_abs_offset}")
            
            # 2. Read Present Position
            raw_ticks = read_present_position(self.motor_id)
            if raw_ticks is None: return None
            
            # 3. Apply stable offset mapping
            self.absolute_ticks = raw_ticks + self.hw_to_abs_offset
            self.last_raw_ticks = raw_ticks
            
            self.output_degrees = (self.absolute_ticks * (360.0 / self.TICKS_PER_REV) / self.gear_ratio) - self.offset_degrees
            self.present_output_degrees = self.output_degrees
            self.last_present_read_ticks = time.ticks_ms()
            
            new_turn = int(self.output_degrees // 360)
            if new_turn != self.current_turn:
                self.current_turn = new_turn
                if self.on_turn_change: self.on_turn_change()
                
            return self.output_degrees
        
        return self._retry_operation(_read_operation, "read position")

    def update_present_position(self, force=False):
        now = time.ticks_ms()
        if not force and time.ticks_diff(now, self.last_present_read_ticks) < 500:
            return self.present_output_degrees
        return self.get_angle_degrees()

    def stop(self):
        current_pos = self.update_present_position(force=True)
        return self.set_nearest_degrees(current_pos, direction_override=0) if current_pos is not None else False

    def home(self, target_degrees=0):
        """Move motor to a home position (default 0°)."""
        return self.set_nearest_degrees(target_degrees, direction_override=0)

    def relax(self):
        return write_byte(self.motor_id, 64, 0)

    def enable_torque(self):
        return write_byte(self.motor_id, 64, 1)

    def set_pid_gains(self, p=None, i=None, d=None):
        from dynamixel_extended_utils import write_word
        if p is not None: write_word(self.motor_id, self.ADDR_POSITION_P_GAIN, p)
        if i is not None: write_word(self.motor_id, self.ADDR_POSITION_I_GAIN, i)
        if d is not None: write_word(self.motor_id, self.ADDR_POSITION_D_GAIN, d)
        return True

    def __repr__(self):
        return f"Motor({self.name}, {self.output_degrees:.1f}°)"
