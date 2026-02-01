"""
DYNAMIXEL Motor Abstraction Layer for Orbigator

Provides a clean interface for controlling Dynamixel motors with optional gear ratios.
Handles position tracking in output degrees (e.g., globe position for EQX motor).

IMPORTANT: When you edit this file, remember to upload the updated file to the Pico 2
           for changes to take effect! Use Thonny or mpremote to transfer the file.
"""

from dynamixel_extended_utils import read_present_position, write_dword, write_byte, get_new_pos
import time

class DynamixelMotor:
    """
    Abstraction for a Dynamixel motor with optional gear ratio.
    
    All angles are in OUTPUT degrees (e.g., globe position for geared motors).
    The class automatically handles gear ratio conversions.
    """
    
    # Constants
    TICKS_PER_MOTOR_DEGREE = 4096.0 / 360.0  # Motor encoder resolution
    ADDR_GOAL_POSITION = 116
    ADDR_LED = 65  # LED control register
    ADDR_PROFILE_VELOCITY = 112  # Speed limit (0=unlimited, higher=faster)
    ADDR_POSITION_D_GAIN = 80
    ADDR_POSITION_I_GAIN = 82
    ADDR_POSITION_P_GAIN = 84
    
    
    def __init__(self, motor_id, name, gear_ratio=1.0, offset_degrees=0.0, direction=None, last_known_pos=None):
        """
        Initialize motor.
        
        Args:
            motor_id: Dynamixel ID
            name: Debug name
            gear_ratio: Output/Motor ratio
            offset_degrees: Zero offset
            direction: Constraint
            last_known_pos: Last known OUTPUT degrees (for restoring multi-turn state on geared motors)
        """
        self.motor_id = motor_id
        self.name = name
        self.gear_ratio = gear_ratio
        self.offset_degrees = offset_degrees
        self.direction = direction
        
        # Communication resilience
        self.consecutive_failures = 0
        self.MAX_FAILURES_BEFORE_OFFLINE = 5
        
        # Tracking speed limit and physical position
        self.current_velocity_limit = None
        self.present_output_degrees = 0.0
        self.last_present_read_ticks = 0
        
        # Turn change detection (for SRAM persistence)
        self.current_turn = 0  # Will be set after position read
        self.on_turn_change = None  # Callback when turn count changes
        
        # Read current motor position on initialization
        motor_ticks = read_present_position(motor_id)
        
        if motor_ticks is None:
            raise RuntimeError(f"Failed to read position from motor {motor_id} ({name})")
            
        # Convert to motor degrees
        self.motor_degrees = motor_ticks / self.TICKS_PER_MOTOR_DEGREE
            
        # Handle Position Restoration after power cycle
        # After power loss, motor only knows 0-360°. We adjust the offset so the
        # current physical position corresponds to the saved output position.
        # This way, no motor movement is required.
        if last_known_pos is not None:
            # Raw motor position from hardware (0-360° after power cycle)
            raw_motor_deg = self.motor_degrees
            
            # Calculate offset so that: (raw_motor / ratio) - offset = saved_output
            # Rearranging: offset = (raw_motor / ratio) - saved_output
            new_offset = (raw_motor_deg / self.gear_ratio) - last_known_pos
            
            print(f"  Restoring position: Raw motor={raw_motor_deg:.1f}°, Saved output={last_known_pos:.1f}°")
            print(f"  Calculated offset: {new_offset:.4f}° (was {self.offset_degrees})")
            
            # Apply the new offset - motor stays physically where it is
            self.offset_degrees = new_offset

        # Recalculate output with the offset
        self.output_degrees = (self.motor_degrees / gear_ratio) - self.offset_degrees
        self.present_output_degrees = self.output_degrees
        self.current_turn = int(self.output_degrees // 360)  # Initialize turn count
        self.last_present_read_ticks = time.ticks_ms()
        print(f"  Gear ratio: {self.gear_ratio:.3f}:1")
        if direction == 1:
            print(f"  Direction constraint: FORWARD-ONLY")
        elif direction == -1:
            print(f"  Direction constraint: BACKWARD-ONLY")
        else:
            print(f"  Direction constraint: SHORTEST PATH")
    
    def _retry_operation(self, operation, operation_name, max_retries=3):
        """
        Retry wrapper for DYNAMIXEL operations with exponential backoff.
        
        Args:
            operation: Callable that returns result or None on failure
            operation_name: Human-readable name for logging
            max_retries: Maximum number of attempts (default 3)
        
        Returns:
            Operation result, or None if all retries failed
        """
        backoff_ms = [10, 20, 40]  # Exponential backoff
        
        for attempt in range(max_retries):
            result = operation()
            if result is not None:
                # Success - reset failure counter
                if self.consecutive_failures > 0:
                    print(f"Motor {self.motor_id} ({self.name}): Communication restored")
                self.consecutive_failures = 0
                return result
            
            # Failure - log and backoff
            if attempt < max_retries - 1:
                delay = backoff_ms[attempt] if attempt < len(backoff_ms) else backoff_ms[-1]
                print(f"Motor {self.motor_id} ({self.name}): {operation_name} failed (attempt {attempt+1}/{max_retries}), retrying in {delay}ms...")
                time.sleep_ms(delay)
        
        # All retries failed
        self.consecutive_failures += 1
        print(f"Motor {self.motor_id} ({self.name}): {operation_name} FAILED after {max_retries} attempts (consecutive failures: {self.consecutive_failures})")
        return None
    
    def set_speed_limit(self, velocity=100):
        """
        Set maximum speed limit for the motor.
        
        This prevents the satellite pointer from moving too fast.
        Higher values = faster movement, lower values = slower movement.
        
        Args:
            velocity: Profile velocity (0-32767)
                     0 = no limit (DANGEROUS: Magnets will fly off!)
                     20-50 = Very fast (Too fast for globe)
                     10 = Safety Maximum (Use for catch-up)
                     5 = Moderate speed
                     1-2 = Smooth simulation speed
        
        Returns:
            True if successful, False otherwise
        """
        # Optimization: Don't write or print if already at target
        if self.current_velocity_limit == velocity:
            return True
            
        success = write_dword(self.motor_id, self.ADDR_PROFILE_VELOCITY, velocity)
        if success:
            self.current_velocity_limit = velocity
            print(f"  Speed limit set: velocity={velocity} (higher=faster)")
        else:
            print(f"Warning: Failed to set speed limit for motor {self.motor_id}")
        return success
    
    def set_angle_degrees(self, output_degrees):
        """
        Set the output angle in degrees with retry logic.
        
        For geared motors (EQX), this is the globe position.
        For direct drive (AoV), this is the motor position.
        
        Args:
            output_degrees: Desired output angle in degrees
        
        Returns:
            True if successful, False otherwise
        """
        # Convert output degrees to motor degrees
        # Output = (Motor / Ratio) - Offset  =>  Motor = (Output + Offset) * Ratio
        motor_degrees = (output_degrees + self.offset_degrees) * self.gear_ratio
        
        # Command the motor with retry logic
        def _write_operation():
            motor_ticks = int(motor_degrees * self.TICKS_PER_MOTOR_DEGREE)
            success = write_dword(self.motor_id, self.ADDR_GOAL_POSITION, motor_ticks)
            return success if success else None
        
        result = self._retry_operation(_write_operation, "write position")
        
        if result:
            # Update tracking
            self.output_degrees = output_degrees
            self.motor_degrees = motor_degrees
            
            # Check for turn change (triggers SRAM save)
            new_turn = int(self.output_degrees // 360)
            if new_turn != self.current_turn:
                self.current_turn = new_turn
                if self.on_turn_change:
                    self.on_turn_change()
            
            return True
        else:
            # If we fail, try to read back the actual position to keep software track in sync
            self.get_angle_degrees()
            return False
            
    def home(self, angle_deg=0):
        """
        Home the motor (move output shaft to 0 degrees).
        Convenience wrapper around set_angle_degrees(0).
        """
        print(f"Homing Motor {self.motor_id} ({self.name})...")
        return self.set_nearest_degrees(angle_deg)
    
    def set_nearest_degrees(self, target_degrees, direction_override=None):
        """
        Set the output angle respecting the motor's direction constraint.
        
        This method uses get_new_pos() to calculate the path to the target:
        - If direction=None/0: Uses shortest path (can go forward or backward)
        - If direction=1: Always moves forward (positive direction)
        - If direction=-1: Always moves backward (negative direction)
        
        Args:
            target_degrees: Desired output angle in degrees (normally 0-360)
            direction_override: Optional override for this specific move (None uses instance direction)
        
        Returns:
            True if successful, False otherwise
        """
        # Use override if provided, otherwise use instance direction
        effective_direction = direction_override if direction_override is not None else self.direction
        
        # Calculate new absolute position using the standardized utility with direction constraint
        new_degrees = get_new_pos(self.output_degrees, target_degrees, effective_direction)
        
        # Log large moves for troubleshooting
        delta = new_degrees - self.output_degrees
        if abs(delta) > 90:
            print(f"DEBUG: Large move on {self.name} (ID {self.motor_id}): Δ={delta:.2f}°")
            
        # Command the motor
        return self.set_angle_degrees(new_degrees)

    
    def get_angle_degrees(self):
        """
        Read current output angle in degrees with retry logic.
        
        Returns:
            Current output angle, or None on error
        """
        def _read_operation():
            motor_ticks = read_present_position(self.motor_id)
            
            if motor_ticks is None:
                return None
            
            # Convert to motor degrees
            motor_degrees = motor_ticks / self.TICKS_PER_MOTOR_DEGREE
            
            # Convert to output degrees
            # Output = (Motor / Ratio) - Offset
            output_degrees = (motor_degrees / self.gear_ratio) - self.offset_degrees
            
            # Update tracking
            self.motor_degrees = motor_degrees
            self.output_degrees = output_degrees
            self.present_output_degrees = output_degrees
            self.last_present_read_ticks = time.ticks_ms()
            
            return output_degrees
        
        return self._retry_operation(_read_operation, "read position")

    def update_present_position(self, force=False):
        """
        Poll the motor's actual physical position from hardware.
        
        This is throttled to once every 500ms unless force=True to protect
        bus bandwidth for time-critical motion commands.
        
        Returns:
            Current physical output degrees
        """
        now = time.ticks_ms()
        if not force and time.ticks_diff(now, self.last_present_read_ticks) < 500:
            return self.present_output_degrees
            
        # Read from hardware
        return self.get_angle_degrees()
    
    def move_relative_degrees(self, delta_output_degrees):
        """
        Move by a relative amount from current position.
        
        Args:
            delta_output_degrees: Amount to move in output degrees
        """
        new_output_degrees = self.output_degrees + delta_output_degrees
        return self.set_angle_degrees(new_output_degrees)
    
    def flash_led(self, count=1, on_time_ms=200, off_time_ms=200):
        """
        Flash the motor's LED for visual identification.
        
        Args:
            count: Number of times to flash (default=1)
            on_time_ms: Time LED stays on in milliseconds (default=200)
            off_time_ms: Time LED stays off between flashes (default=200)
        
        Returns:
            True if successful, False otherwise
        """
        for i in range(count):
            # Turn LED on
            if not write_byte(self.motor_id, self.ADDR_LED, 1):
                print(f"Warning: Failed to turn on LED for motor {self.motor_id}")
                return False
            time.sleep_ms(on_time_ms)
            
            # Turn LED off
            if not write_byte(self.motor_id, self.ADDR_LED, 0):
                print(f"Warning: Failed to turn off LED for motor {self.motor_id}")
                return False
            
            # Wait before next flash (except after last flash)
            if i < count - 1:
                time.sleep_ms(off_time_ms)
        
        return True
    
    def __repr__(self):
        return f"DynamixelMotor(id={self.motor_id}, name='{self.name}', output={self.output_degrees:.1f}°, gear_ratio={self.gear_ratio:.3f})"

    def stop(self):
        """Stop motor in place by setting goal to current present position."""
        # Force a fresh read from hardware
        current_pos = self.update_present_position(force=True)
        if current_pos is not None:
            # Command the motor to stay at this exact spot
            self.set_angle_degrees(current_pos)
            print(f"STOPPED: Motor {self.motor_id} ({self.name}) holding at {current_pos:.2f}°")
            return True
        return False

    def relax(self):
        """Disable torque so the motor can be moved freely by hand."""
        # ADDR_TORQUE_ENABLE = 64
        if write_byte(self.motor_id, 64, 0):
            print(f"RELAXED: Motor {self.motor_id} ({self.name}) torque disabled.")
            return True
        return False
        
    def get_pid_gains(self):
        """Read current PID gains from the motor."""
        from dynamixel_extended_utils import read_word
        p = read_word(self.motor_id, self.ADDR_POSITION_P_GAIN)
        i = read_word(self.motor_id, self.ADDR_POSITION_I_GAIN)
        d = read_word(self.motor_id, self.ADDR_POSITION_D_GAIN)
        self.p_gain, self.i_gain, self.d_gain = p, i, d
        return p, i, d
        
    def set_pid_gains(self, p=None, i=None, d=None):
        """
        Set PID gains for the position control loop.
        
        Args:
            p: Proportional gain (default 800)
            i: Integral gain (default 0)
            d: Derivative gain (default 0)
        """
        from dynamixel_extended_utils import write_word
        
        success = True
        if p is not None:
            if write_word(self.motor_id, self.ADDR_POSITION_P_GAIN, p):
                self.p_gain = p
            else:
                success = False
                print(f"  ✗ Failed to set P gain for motor {self.motor_id}")
        
        if i is not None:
            if write_word(self.motor_id, self.ADDR_POSITION_I_GAIN, i):
                self.i_gain = i
            else:
                success = False
                print(f"  ✗ Failed to set I gain for motor {self.motor_id}")
                
        if d is not None:
            if write_word(self.motor_id, self.ADDR_POSITION_D_GAIN, d):
                self.d_gain = d
            else:
                success = False
                print(f"  ✗ Failed to set D gain for motor {self.motor_id}")
                
        if success:
            print(f"  ✓ PID gains updated for motor {self.motor_id}: P={p}, I={i}, D={d}")
        return success

    def enable_torque(self):
        """Re-enable torque to resume computer control."""
        if write_byte(self.motor_id, 64, 1):
            print(f"ACTIVE: Motor {self.motor_id} ({self.name}) torque enabled.")
            return True
        return False
