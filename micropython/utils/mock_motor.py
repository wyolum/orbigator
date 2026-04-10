"""
Mock Motor for Web Development
Simulates DynamixelMotor interface without hardware
"""

class MockMotor:
    def __init__(self, motor_id, name, gear_ratio=1.0):
        self.motor_id = motor_id
        self.name = name
        self.gear_ratio = gear_ratio
        self.target_degrees = 0.0
        self.present_output_degrees = 0.0
        self.speed_limit = 10
        self.current_velocity_limit = 10
        self.consecutive_failures = 0
        self.p_gain = 600
        self.i_gain = 0
        self.d_gain = 0
        print(f"MockMotor initialized: {name} (ID {motor_id}, ratio {gear_ratio:.2f})")
    
    def set_nearest_degrees(self, target_deg):
        """Simulate setting target position"""
        self.target_degrees = target_deg
        # Instantly "move" to target for simulation
        self.present_output_degrees = target_deg
    
    def get_angle_degrees(self):
        """Return current position"""
        return self.present_output_degrees
    
    def update_present_position(self, force=False):
        """Simulate position update"""
        # In mock mode, position is always at target
        pass
    
    def set_speed_limit(self, speed):
        """Set speed limit"""
        self.speed_limit = speed
    
    def set_pid_gains(self, p=0, i=0, d=0):
        """Set PID gains (no-op for mock)"""
        pass
    
    def home(self, target_deg=0):
        """Simulate homing"""
        self.set_nearest_degrees(target_deg)
        print(f"{self.name} homed to {target_deg}°")
    
    def stop(self):
        """Stop motor (no-op for mock)"""
        pass
    
    def flash_led(self, count=1):
        """Flash LED (no-op for mock)"""
        print(f"{self.name} LED flash x{count}")
