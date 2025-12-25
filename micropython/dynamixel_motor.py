"""
DYNAMIXEL Motor Abstraction Layer for Orbigator

Provides a clean interface for controlling Dynamixel motors with optional gear ratios.
Handles position tracking in output degrees (e.g., globe position for EQX motor).

IMPORTANT: When you edit this file, remember to upload the updated file to the Pico 2
           for changes to take effect! Use Thonny or mpremote to transfer the file.
"""

from dynamixel_extended_utils import read_present_position, write_dword, write_byte
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
    
    def __init__(self, motor_id, name, gear_ratio=1.0):
        """
        Initialize motor.
        
        Args:
            motor_id: Dynamixel ID (1 for EQX, 2 for AoV)
            name: Human-readable name for debugging
            gear_ratio: Output rotation / Motor rotation (e.g., 120/11 for EQX ring gear)
        """
        self.motor_id = motor_id
        self.name = name
        self.gear_ratio = gear_ratio
        
        # Read current motor position on initialization
        motor_ticks = read_present_position(motor_id)
        
        if motor_ticks is None:
            raise RuntimeError(f"Failed to read position from motor {motor_id} ({name})")
        
        # Convert to motor degrees
        self.motor_degrees = motor_ticks / self.TICKS_PER_MOTOR_DEGREE
        
        # Track output position (accounting for gear ratio)
        self.output_degrees = self.motor_degrees / gear_ratio
        
        print(f"Motor {motor_id} ({name}) initialized:")
        print(f"  Motor position: {self.motor_degrees:.2f}°")
        print(f"  Output position: {self.output_degrees:.2f}°")
        print(f"  Gear ratio: {gear_ratio:.3f}:1")
    
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
        success = write_dword(self.motor_id, self.ADDR_PROFILE_VELOCITY, velocity)
        if success:
            print(f"  Speed limit set: velocity={velocity} (higher=faster)")
        else:
            print(f"Warning: Failed to set speed limit for motor {self.motor_id}")
        return success
    
    def set_angle_degrees(self, output_degrees):
        """
        Set the output angle in degrees.
        
        For geared motors (EQX), this is the globe position.
        For direct drive (AoV), this is the motor position.
        
        Args:
            output_degrees: Desired output angle in degrees
        """
        # Convert output degrees to motor degrees
        motor_degrees = output_degrees * self.gear_ratio
        
        # Convert motor degrees to ticks
        motor_ticks = int(motor_degrees * self.TICKS_PER_MOTOR_DEGREE)
        
        # Send to motor
        success = write_dword(self.motor_id, self.ADDR_GOAL_POSITION, motor_ticks)
        
        if success:
            # Update tracking
            self.output_degrees = output_degrees
            self.motor_degrees = motor_degrees
        else:
            print(f"Warning: Failed to set position for motor {self.motor_id} ({self.name})")
        
        return success
    
    def set_nearest_degrees(self, target_degrees):
        """
        Set the output angle using the shortest path (nearest route).
        
        This method uses get_new_pos() to calculate the shortest path to the target,
        preventing the motor from wrapping the long way around 0°/360°.
        
        For example:
        - Current: 358°, Target: 2° → Moves forward +4° (not backward -356°)
        - Current: 10°, Target: 350° → Moves backward -20° (not forward +340°)
        
        Args:
            target_degrees: Desired output angle in degrees (0-360)
        
        Returns:
            True if successful, False otherwise
        """
        from dynamixel_extended_utils import get_new_pos
        
        # Get current position
        current_degrees = self.output_degrees
        
        # Calculate shortest path using get_new_pos
        new_degrees = get_new_pos(current_degrees, target_degrees)
        
        # Command the motor
        return self.set_angle_degrees(new_degrees)
    
    def get_angle_degrees(self):
        """
        Read current output angle in degrees.
        
        Returns:
            Current output angle, or None on error
        """
        motor_ticks = read_present_position(self.motor_id)
        
        if motor_ticks is None:
            return None
        
        # Convert to motor degrees
        motor_degrees = motor_ticks / self.TICKS_PER_MOTOR_DEGREE
        
        # Convert to output degrees
        output_degrees = motor_degrees / self.gear_ratio
        
        # Update tracking
        self.motor_degrees = motor_degrees
        self.output_degrees = output_degrees
        
        return output_degrees
    
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
