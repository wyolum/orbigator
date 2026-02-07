import random

def snap_to_nearest(raw, saved):
    """
    Recover the absolute position from a relative reading and a saved absolute state.
    raw: 0-4095
    saved: large absolute integer
    """
    # Number of full rotations in the saved state
    revs = saved // 4096
    
    # Candidates are the raw value in the current, previous, or next revolution
    candidates = [
        (revs - 1) * 4096 + raw,
        (revs) * 4096 + raw,
        (revs + 1) * 4096 + raw
    ]
    
    # Pick the one closest to the saved state
    best = min(candidates, key=lambda x: abs(x - saved))
    return best

class MotorSimulator:
    def __init__(self, gear_ratio):
        self.gear_ratio = gear_ratio
        self.absolute_ticks = 0
        self.sram_ticks = 0
        
    def move(self, delta_ticks):
        self.absolute_ticks += delta_ticks
        print(f"Moving {delta_ticks:5d} ticks. Absolute: {self.absolute_ticks:8d}, Output: {self.get_output_deg():.2f}°")
        
    def save_to_sram(self):
        self.sram_ticks = self.absolute_ticks
        print(f" [SRAM SAVE] {self.sram_ticks}")
        
    def power_loss(self):
        print("\n--- POWER LOSS ---")
        # When powered off, the physical position is maintained, 
        # but the motor controller loses track of the revolution count.
        pass
        
    def boot(self):
        print("--- BOOTING ---")
        # Motor hardware only provides 0-4095
        raw_reading = self.absolute_ticks % 4096
        
        # Recovery logic
        recovered_ticks = snap_to_nearest(raw_reading, self.sram_ticks)
        
        print(f" Hardware Reading: {raw_reading:4d}")
        print(f" SRAM Recovery:    {self.sram_ticks:8d} (saved) -> {recovered_ticks:8d} (recovered)")
        
        if recovered_ticks == self.absolute_ticks:
            print(" ✓ SUCCESS: Absolute orientation recovered perfectly!")
        else:
            print(f" ✗ FAILURE: Mismatch! Expected {self.absolute_ticks}, got {recovered_ticks}")
            
        return recovered_ticks

    def get_output_deg(self):
        # 4096 ticks = 360 motor deg
        motor_deg = self.absolute_ticks * (360.0 / 4096.0)
        return motor_deg / self.gear_ratio

def run_test():
    sim = MotorSimulator(gear_ratio=120/14)
    
    # Test case 1: Multiple rotations forward
    print("\nTest Case 1: Standard Movement")
    for _ in range(5):
        sim.move(random.randint(500, 5000))
        sim.save_to_sram()
    
    sim.power_loss()
    sim.boot()
    
    # Test case 2: Backward movement
    print("\nTest Case 2: Backward Movement")
    sim.move(-15000)
    sim.save_to_sram()
    sim.power_loss()
    sim.boot()
    
    # Test case 3: Edge case - boundary of rotation
    print("\nTest Case 3: Near 4096 Boundary")
    sim.absolute_ticks = 4090
    sim.save_to_sram()
    sim.move(20) # Crosses 4096, absolute 4110
    sim.power_loss() # raw will be 14
    sim.boot()

    # Test case 4: Moving without saving (should handle drift < 180 motor degrees)
    print("\nTest Case 4: Recovering from unsaved small motion (< 180° motor)")
    sim.move(1000)
    sim.save_to_sram()
    sim.move(500) # Unsaved movement
    sim.power_loss()
    sim.boot() # Should still snap to the correct one

if __name__ == "__main__":
    run_test()
