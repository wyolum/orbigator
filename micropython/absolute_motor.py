"""
Absolute Motor System
=====================
Implements 'Persistence Follows the Drive Gear' architecture.

Layers:
1. PersistentDrive: Physical truth (ticks, storage, identity).
2. AxisKinematics: Logic transforms (ticks <-> degrees, calibration).
3. AbsoluteDynamixel: Behavior composition & hardware control.
"""

import struct
import time

class AxisKinematics:
    """
    Pure logic layer for coordinate transforms.
    Manages gear ratio, zero offsets, and unit conversions.
    """
    TICKS_PER_REV_DYNAMIXEL = 4096
    
    def __init__(self, gear_ratio=1.0, ticks_per_rev=4096):
        self.gear_ratio = gear_ratio
        self.ticks_per_rev = ticks_per_rev
        # Ticks per degree of OUTPUT shaft
        # Motor revs per output rev = gear_ratio
        # Motor ticks per output rev = ticks_per_rev * gear_ratio
        self.ticks_per_degree = (self.ticks_per_rev * self.gear_ratio) / 360.0
        self.offset_degrees = 0.0

    def ticks_to_degrees(self, ticks):
        """Convert absolute motor ticks to output degrees (logical)."""
        raw_deg = ticks / self.ticks_per_degree
        return raw_deg + self.offset_degrees

    def degrees_to_ticks(self, degrees):
        """Convert output degrees (logical) to absolute motor ticks."""
        # logical = raw + offset  =>  raw = logical - offset
        raw_deg = degrees - self.offset_degrees
        return int(raw_deg * self.ticks_per_degree)

    def calculate_offset(self, current_ticks, desired_degrees):
        """
        Calculate the offset_degrees required to make 'current_ticks' 
        align with 'desired_degrees'.
        
        current_deg_raw = ticks / TPD
        desired = current_deg_raw + offset
        offset = desired - current_deg_raw
        """
        current_deg_raw = current_ticks / self.ticks_per_degree
        new_offset = desired_degrees - current_deg_raw
        # Normalize offset? Usually not needed for absolute linear math, 
        # but prevents it from growing infinitely if we keep recalibrating wrapping?
        # Let's keep it simple float.
        return new_offset


class PersistentDrive:
    """
    Physical layer: Manages raw motor ticks and NVRAM persistence.
    Enforces 'Identity Protection' and 'Dual-Trigger Checkpointing'.
    """
    # Magic Header: ASCII 'PD' + Version 1 -> 0x5044, 0x0001
    STORAGE_MAGIC = 0x5044
    SCHEMA_VERSION = 1
    # Layout: [Magic:H][Version:H][Ticks:i][Hash:I][Reserved:I] = 16 bytes
    RECORD_SIZE = 16
    
    # Checkpoint triggers
    TRIGGER_DISTANCE_TICKS = 100  # Save if moved > ~8 degrees (at 1:1)
    TRIGGER_TIME_SEC = 300       # Save every 5 minutes regardless of movement

    def __init__(self, persist_backend, identity_hash=0):
        self.persist = persist_backend
        self.identity_hash = identity_hash
        
        self._abs_ticks = 0
        self._last_saved_ticks = 0
        self._last_saved_time = time.time()
        
        # Hydrate
        self.loaded_valid = self._load_state()
        if not self.loaded_valid:
            # First boot or corruption or identity mismatch
            # Assume 0 or caller will recover()
            self._save_state(force=True)

    @property
    def ticks(self):
        return self._abs_ticks

    def update(self, hw_phase_ticks):
        """
        Update state logic given current hardware phase (0-4095).
        Expected to be called frequently.
        """
        # Note: This class primarily holds the *absolute* ticks. 
        # Integration with hardware phase to update _abs_ticks happens 
        # in the Behavior layer (recover/sync) or here?
        # Design note says "operate exclusively in ticks".
        # If we passed in just 'hw_phase_ticks', we'd need to do the stitching/recovery logic here 
        # to know if we crossed a turn boundary.
        # But usually 'update' implies "I commanded X, or I read absolute X".
        # Let's assume the Behavior layer handles the stitching (reading multi-turn registers or software stitching)
        # and tells us the new signed Absolute Ticks.
        # 
        # WAIT. If we are replacing existing AbsoluteDynamixel which did stitching...
        # Dynamixel Extended Position Mode handles multi-turn internally as a 32-bit int.
        # So we typically read a signed int from hardware directly.
        # So 'hw_abs_ticks' is the input.
        pass

    def set_ticks(self, ticks):
        """Update the tracked physical position (usually from hardware read)."""
        self._abs_ticks = ticks
        self._check_checkpoint()

    def _check_checkpoint(self):
        """Check if save is required based on dual triggers."""
        # 1. Distance Trigger
        delta_dist = abs(self._abs_ticks - self._last_saved_ticks)
        if delta_dist > self.TRIGGER_DISTANCE_TICKS:
            self._save_state()
            return

        # 2. Time Trigger
        now = time.time()
        delta_time = now - self._last_saved_time
        if delta_time > self.TRIGGER_TIME_SEC:
            self._save_state()

    def _save_state(self, force=False):
        if not self.persist: return
        
            # Pack: Magic(H), Ver(H), Ticks(i), Hash(I), Reserved(I)
        data = struct.pack("<HHiII", 
            self.STORAGE_MAGIC, 
            self.SCHEMA_VERSION, 
            self._abs_ticks, 
            int(self.identity_hash), 
            0) # Reserved
            
        self.persist.write(0, data)
        self._last_saved_ticks = self._abs_ticks
        self._last_saved_time = time.time()

    def _load_state(self):
        if not self.persist: return False
        
        data = self.persist.read(0, self.RECORD_SIZE)
        if not data or len(data) < self.RECORD_SIZE: return False
        
        magic, ver, ticks, saved_hash, _ = struct.unpack("<HHiiI", data)
        
        if magic != self.STORAGE_MAGIC:
            return False
            
        if saved_hash != self.identity_hash:
            print(f"PersistentDrive: Identity mismatch (Saved {saved_hash:x} != Curr {self.identity_hash:x}). Resetting.")
            return False
            
        self._abs_ticks = ticks
        self._last_saved_ticks = ticks
        self._last_saved_time = time.time()
        return True


class AbsoluteDynamixel:
    """
    Behavior layer: Composes PersistentDrive and Kinematics.
    Controls a Dynamixel motor with absolute degrees API.
    """
    ADDR_GOAL_POSITION = 116
    
    def __init__(self, motor_id, rtc, gear_ratio=1.0, sram_slot=0, offset_degrees=0.0, direction=1):
        self.motor_id = motor_id
        
        # 1. Setup Kinematics (Transform)
        self.kinematics = AxisKinematics(gear_ratio=gear_ratio)
        self.kinematics.offset_degrees = offset_degrees
        
        # 2. Setup Persistence (Physical)
        from persistence import SRAM
        # Calculate base address (16 bytes per slot)
        # Old slot 0 was 0x80 (len 10). Slot 1 was 0x8A.
        # New aligned slots: Slot 0 @ 0x80, Slot 1 @ 0x90 (16 bytes = 0x10)
        base_addr = 0x80 + (sram_slot * 16)
        persist_backend = SRAM(rtc, base_addr, PersistentDrive.RECORD_SIZE)
        
        # Generate identity hash logic (simple sum for now, or based on gear ratio)
        # If gear ratio changes, encoding changes.
        # Hash = ID + int(GearRatio * 100)
        id_hash = motor_id + int(gear_ratio * 1000)
        self.drive = PersistentDrive(persist_backend, identity_hash=id_hash)
        
        self.direction = direction # 1 or -1, used for shortest path logic preference
        
        # 3. Hardware Initialization
        self._init_hardware()
        
        # 4. Recovery
        # If persistence was invalid (identity changed), we rely on HW.
        # Ideally we read HW phase and stitch.
        # Dynamixel Extended Mode keeps its own multi-turn counter as long as power is maintained.
        # If power cycled, we lose turn count? 
        # XL330 manual: "Multi-turn... resets to 0 when power is turned on." (Unless backup used?)
        # Wait, if motor resets to 0, we MUST recover turn count from Persistence.
        
        self._recover_position()

    def _init_hardware(self):
        from dynamixel_extended_utils import reboot_motor, set_extended_mode, ping_motor
        try:
            if not ping_motor(self.motor_id):
                print(f"Motor {self.motor_id} missing on bus.")
                pass # Don't crash, update() will fail later gracefully
            
            reboot_motor(self.motor_id)
            set_extended_mode(self.motor_id)
        except Exception as e:
            print(f"Motor {self.motor_id} Init Error: {e}")

    def _recover_position(self):
        """
        Recover absolute multi-turn position by fusing Persistence with Hardware Phase.
        Design Note: "Recovered_position must lie within a bounded delta"
        """
        from dynamixel_extended_utils import read_present_position, write_byte, write_dword
        
        # 1. Read raw hardware position (likely near 0 if fresh boot, or random if manual move)
        # Actually XL330 'Present Position' in Extended mode IS absolute tracked by motor... 
        # BUT resets on power loss.
        # So we read it as "Phase" effectively (0-4095) + Volatile Turns.
        
        raw_hw = read_present_position(self.motor_id)
        if raw_hw is None:
            return # Can't recover
            
        CPR = 4096
        current_phase = raw_hw % CPR
        
        # 2. Get Persisted Guess
        saved_ticks = self.drive.ticks
        
        # 3. Stitching (Bounded Delta Recovery)
        # Find k such that (k * CPR + phase) is closest to saved_ticks
        revs = saved_ticks // CPR
        candidates = [(revs + d) * CPR + current_phase for d in (-1, 0, 1)]
        best_guess = min(candidates, key=lambda c: abs(c - saved_ticks))
        
        # 4. Safety Check (e.g. 0.5 rev limit)
        delta = abs(best_guess - saved_ticks)
        if delta > (CPR // 2) and self.drive.loaded_valid:
            print(f"WARNING: Motor {self.motor_id} moved > 0.5 rev ({delta} ticks) while off.")
            # Policy: "Do not automatically command motion"? 
            # For now, we accept the new reality (best guess) but log it.
            
        # 5. Apply to Hardware (Offsetting)
        # We want the motor to treat current physical position as 'best_guess'.
        # XL330 doesn't verify "Set Present Position".
        # Instead, we maintain a `hw_offset` in software? 
        # OR we use the Dynamixel "Homing Offset" register? (Register 20)
        # OR we just subtract in `_command`.
        # Prev solution used `_hw_offset`. Let's stick to that for reliability.
        
        # If hardware says 50, and we think it's 4146.
        # Real = HW + Offset => 4146 = 50 + Offset => Offset = 4096.
        self._hw_offset = best_guess - raw_hw
        
        # Update Drive with the reconstructed truth
        self.drive.set_ticks(best_guess)
        
        # Force save to sync timestamps
        # self.drive.checkpoint(force=True) # Drive handles logic

    @property
    def position_deg(self):
        """Current logical position in degrees."""
        self.update()
        return self.kinematics.ticks_to_degrees(self.drive.ticks)

    def update(self):
        """Sync software state with hardware."""
        from dynamixel_extended_utils import read_present_position
        raw = read_present_position(self.motor_id)
        if raw is not None:
            true_ticks = raw + self._hw_offset
            self.drive.set_ticks(true_ticks)
        return self.kinematics.ticks_to_degrees(self.drive.ticks)

    def goto(self, degrees):
        """Absolute move to logical degrees."""
        target_ticks = self.kinematics.degrees_to_ticks(degrees)
        self._command(target_ticks)

    def mod_goto(self, mod_deg):
        """Shortest path move to mod coordinate."""
        current_deg = self.position_deg
        
        target = mod_deg % 360
        current_mod = current_deg % 360
        
        delta = ((target - current_mod) + 180) % 360 - 180
        
        # Direction preference override? (Optional)
        # If needed, implement 'direction' check here.
        
        self.goto(current_deg + delta)

    def _command(self, target_ticks):
        from dynamixel_extended_utils import write_dword
        # Convert absolute ticks to hardware target
        hw_goal = target_ticks - self._hw_offset 
        # Wait, if True = HW + Off, then HW = True - Off.
        # Previous calc: Offset = True - HW. Correct.
        
        write_dword(self.motor_id, self.ADDR_GOAL_POSITION, int(hw_goal))
        
        # Optimistic update or wait for read?
        # Update drive immediately to prevent stutter logic
        self.drive.set_ticks(target_ticks)

    def home(self):
        self.goto(0)

    # --- Compatibility ---
    def set_speed_limit(self, speed_percent):
        from dynamixel_extended_utils import write_dword
        val = int((speed_percent / 100.0) * 445) # 445 is roughly limit for XL330? Check specs.
        if val < 1: val = 1
        write_dword(self.motor_id, 112, val)

    def set_pid_gains(self, p=None, i=None, d=None):
        from dynamixel_extended_utils import write_word
        # XL330 addresses: D=80, I=82, P=84
        if d is not None: write_word(self.motor_id, 80, d)
        if i is not None: write_word(self.motor_id, 82, i)
        if p is not None: write_word(self.motor_id, 84, p)

    def set_nearest_degrees(self, degrees):
        """Compatibility alias for mod_goto."""
        self.mod_goto(degrees)

    def update_present_position(self, force=False):
        """Compatibility alias for update()."""
        return self.update()

    @property
    def output_degrees(self):
        """Compatibility alias for position_deg."""
        return self.position_deg

    @property
    def offset_degrees(self):
        return self.kinematics.offset_degrees
    
    @offset_degrees.setter
    def offset_degrees(self, value):
        self.kinematics.offset_degrees = value

    def get_angle_degrees(self):
        """Compatibility alias for update()."""
        return self.update()

    def enable_torque(self, enable=True):
        from dynamixel_extended_utils import write_byte
        write_byte(self.motor_id, 64, 1 if enable else 0)
    
    def stop(self):
        self.update()
        self._command(self.drive.ticks)
