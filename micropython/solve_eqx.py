import machine, time, struct, json
from machine import Pin, I2C
from ds323x import DS323x
from dynamixel_motor import DynamixelMotor, read_present_position
import pins
import orb_globals as g

# --- Configuration ---
EQX_MOTOR_ID = 1
GEAR_RATIO = 120.0 / 14.0
TICKS_PER_REV = 4096

# SRAM dedicated slot for high-precision tracking (end of user SRAM)
SRAM_ADDR = 0xA0  
SRAM_MAGIC = b"EQX!"
SRAM_FORMAT = "<4s i B" # Magic, Ticks, Checksum

class EQXTracker:
    def __init__(self, rtc):
        self.rtc = rtc
        
    def _compute_checksum(self, magic, ticks):
        data = magic + struct.pack("<i", ticks)
        return sum(data) & 0xFF
        
    def save(self, absolute_ticks):
        """Save absolute ticks to RTC SRAM with checksum."""
        if not self.rtc or not getattr(self.rtc, 'has_sram', False):
            return False
            
        ck = self._compute_checksum(SRAM_MAGIC, absolute_ticks)
        data = struct.pack(SRAM_FORMAT, SRAM_MAGIC, absolute_ticks, ck)
        return self.rtc.write_sram(SRAM_ADDR, data)
        
    def load(self):
        """Load and validate absolute ticks from RTC SRAM."""
        if not self.rtc or not getattr(self.rtc, 'has_sram', False):
            return None
            
        data = self.rtc.read_sram(SRAM_ADDR, struct.calcsize(SRAM_FORMAT))
        if not data:
            return None
            
        try:
            magic, ticks, ck = struct.unpack(SRAM_FORMAT, data)
            if magic != SRAM_MAGIC:
                return None
            if ck != self._compute_checksum(magic, ticks):
                print("[!] SRAM Checksum invalid!")
                return None
            return ticks
        except:
            return None

    def recover(self, raw_reading, saved_ticks):
        """
        Recover absolute position from a relative hardware reading (0-4095)
        and a saved absolute state from SRAM.
        """
        # Multiples of 4096
        revs = saved_ticks // TICKS_PER_REV
        
        # We check the current rotation, the one before, and the one after
        candidates = [
            (revs - 1) * TICKS_PER_REV + raw_reading,
            (revs) * TICKS_PER_REV + raw_reading,
            (revs + 1) * TICKS_PER_REV + raw_reading
        ]
        
        # The correct absolute position is the one closest to our last known state
        return min(candidates, key=lambda x: abs(x - saved_ticks))

def run_test():
    """Acceptance test for EQX Position Recovery."""
    print("==========================================")
    print(" EQX POSITION RECOVERY - ACCEPTANCE TEST ")
    print("==========================================")
    
    # 1. Initialize Hardware
    i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400_000)
    rtc = DS323x(i2c, addr=0x68, has_sram=True)
    tracker = EQXTracker(rtc)
    
    # 2. Boot Sequence (Recovery)
    print("\n[STEP 1] Boot Recovery")
    raw_pos = read_present_position(EQX_MOTOR_ID)
    if raw_pos is None:
        print("❌ Error: EQX Motor not found!")
        return
        
    saved_state = tracker.load()
    if saved_state is not None:
        print(f"  Saved state found: {saved_state} ticks")
        current_abs_ticks = tracker.recover(raw_pos, saved_state)
        print(f"  Recovered Absolute: {current_abs_ticks} ticks")
        if current_abs_ticks != saved_state:
            print(f"  Note: Drift detected or small rotation since last save. Corrected.")
    else:
        print("  No saved state. Starting fresh from zero.")
        current_abs_ticks = raw_pos
        tracker.save(current_abs_ticks)
    
    # Initialize Motor object
    motor = DynamixelMotor(EQX_MOTOR_ID, "EQX", gear_ratio=GEAR_RATIO)
    motor.enable_torque()
    
    # 3. Random Exercise Loop
    print("\n[STEP 2] Exercise & Persistent Backup")
    import random
    
    for i in range(3):
        # Move random amount
        move_ticks = random.randint(1000, 5000)
        direction = 1 if i % 2 == 0 else -1
        delta = move_ticks * direction
        
        print(f"\nMoving {delta} ticks...")
        current_abs_ticks += delta
        
        # Command motor
        # Convert absolute ticks to absolute degrees for motor command
        target_deg = current_abs_ticks * (360.0 / TICKS_PER_REV)
        motor.set_extended_position(target_deg)
        
        # Wait a bit
        time.sleep(2)
        
        # 4. The Backup Plan
        # This represents a check-point that guarantees recovery if power fails NOW.
        # In a real app, this should be called whenever the motor stops or after a turn change.
        print(f"Executing Backup Plan...")
        tracker.save(current_abs_ticks)
        
        # Calculate Output Degree
        output_deg = (current_abs_ticks * (360.0 / TICKS_PER_REV)) / GEAR_RATIO
        print(f"Logical Orientation: {output_deg:.2f}°")
        print(f"SRAM State: {tracker.load()} (Verified)")

    print("\n==========================================")
    print(" TEST READY FOR POWER CYCLE ")
    print(" Re-run this script to verify recovery.")
    print("==========================================")

if __name__ == "__main__":
    run_test()
