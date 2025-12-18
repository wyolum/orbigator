"""
DYNAMIXEL Motor Abstraction Layer for Orbigator

Provides a clean interface for controlling Dynamixel motors with optional gear ratios.
Handles position tracking in output degrees (e.g., globe position for LAN motor).
"""

from dynamixel_extended_utils import read_present_position, write_dword

class DynamixelMotor:
    """
    Abstraction for a Dynamixel motor with optional gear ratio.
    
    All angles are in OUTPUT degrees (e.g., globe position for geared motors).
    The class automatically handles gear ratio conversions.
    """
    
    # Constants
    TICKS_PER_MOTOR_DEGREE = 4096.0 / 360.0  # Motor encoder resolution
    ADDR_GOAL_POSITION = 116
    
    def __init__(self, motor_id, name, gear_ratio=1.0):
        """
        Initialize motor.
        
        Args:
            motor_id: Dynamixel ID (1 for LAN, 2 for AoV)
            name: Human-readable name for debugging
            gear_ratio: Output rotation / Motor rotation (e.g., 120/11 for LAN ring gear)
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
    
    def set_angle_degrees(self, output_degrees):
        """
        Set the output angle in degrees.
        
        For geared motors (LAN), this is the globe position.
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
    
    def __repr__(self):
        return f"DynamixelMotor(id={self.motor_id}, name='{self.name}', output={self.output_degrees:.1f}°, gear_ratio={self.gear_ratio:.3f})"
