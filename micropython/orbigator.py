# Orbigator - Orbital Mechanics Simulator
# Pico 2 | DYNAMIXEL XL330-M288-T motors
# ------------------------------------------------------------------

import machine, time, math, json
from machine import Pin, I2C
import framebuf
from ds323x import DS323x
from dynamixel_motor import DynamixelMotor
from dynamixel_extended_utils import set_extended_mode
import orb_globals as g
import orb_utils as utils
import pins
from modes import MenuMode, OrbitMode, DatetimeEditorMode, SGP4Mode
import _thread  # For I2C lock


# ---------------- Hardware Config ----------------
# Set to False for web development without motors
ENABLE_MOTORS = True

# Load Configuration
try:
    with open("orbigator_config.json", "r") as f:
        config_data = json.load(f)
    print("Configuration loaded from orbigator_config.json")
except Exception as e:
    print(f"Config load error: {e}. Using defaults.")
    # Fallback/Default Config
    config_data = {
        "motors": {
            "eqx": {"id": 1, "gear_ratio_num": 120.0, "gear_ratio_den": 14.0, "pid": {"p": 600, "i": 0, "d": 0}, "speed_limit": 50, "offset_deg": 0.0},
            "aov": {"id": 2, "gear_ratio_num": 1.0, "gear_ratio_den": 1.0, "pid": {"p": 600, "i": 0, "d": 0}, "speed_limit": 20, "offset_deg": 0.0}
        },
        "system": {"detent_div": 4, "debounce_ms": 200, "oled": {"width": 128, "height": 64}}
    }

# Extract Config
mc = config_data["motors"]
EQX_MOTOR_ID = mc["eqx"]["id"]
AOV_MOTOR_ID = mc["aov"]["id"]
EQX_GEAR_RATIO = mc["eqx"]["gear_ratio_num"] / mc["eqx"]["gear_ratio_den"]
AOV_GEAR_RATIO = mc["aov"]["gear_ratio_num"] / mc["aov"]["gear_ratio_den"]

DETENT_DIV = config_data["system"]["detent_div"]
DEBOUNCE_MS = 300 # Increased from 200 to filter noise

print("\n--- Motor Configuration ---")
for m_name, m_cfg in mc.items():
    ratio = m_cfg['gear_ratio_num'] / m_cfg['gear_ratio_den']
    print(f"  {m_name.upper()}: ID={m_cfg['id']}, Ratio={ratio:.2f}:1, Limit={m_cfg['speed_limit']}")
print("---------------------------\n")

# ---------------- OLED Init ----------------
OLED_W = config_data["system"]["oled"]["width"]
OLED_H = config_data["system"]["oled"]["height"]
i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400_000)
addrs = i2c.scan()

# Initialize Globals
print(f"Orbigator Booting... System Time: {time.time()}")
utils.init_software_clock() # Guarantee clock advancement from this point
if g.i2c_lock is None:
    g.i2c_lock = _thread.allocate_lock()
if g.uart_lock is None:
    g.uart_lock = _thread.allocate_lock()



class SH1106_I2C:
    def __init__(self, w,h,i2c,addr=0x3C):
        self.width,self.height,self.i2c,self.addr = w,h,i2c,addr
        self.buffer = bytearray(w*h//8)
        self.fb = framebuf.FrameBuffer(self.buffer, w, h, framebuf.MONO_VLSB)
        def cmd(*cs):
            if g.i2c_lock:
                with g.i2c_lock:
                    for c in cs: self.i2c.writeto(self.addr, b'\x00'+bytes([c]))
            else:
                for c in cs: self.i2c.writeto(self.addr, b'\x00'+bytes([c]))
        cmd(0xAE,0x20,0x00,0x40,0xA1,0xC8,0x81,0x7F,0xA6,0xA8,0x3F,
            0xAD,0x8B,0xD3,0x00,0xD5,0x80,0xD9,0x22,0xDA,0x12,0xDB,0x35,0xAF)
        self.fill(0); self.show()
    def fill(self,c): self.fb.fill(c)
    def text(self,s,x,y,c=1): self.fb.text(s,x,y,c)
    def degree(self,x,y,c=1):
        self.fb.pixel(x+1, y, c)
        self.fb.pixel(x, y+1, c)
        self.fb.pixel(x+2, y+1, c)
        self.fb.pixel(x+1, y+2, c)
    def show(self):
        try:
            if g.i2c_lock:
                with g.i2c_lock:
                    for p in range(self.height//8):
                        self.i2c.writeto(self.addr, b'\x00'+bytes([0xB0+p,0x02,0x10]))
                        s = self.width*p; e = s+self.width
                        self.i2c.writeto(self.addr, b'\x40'+self.buffer[s:e])
            else:
                for p in range(self.height//8):
                    self.i2c.writeto(self.addr, b'\x00'+bytes([0xB0+p,0x02,0x10]))
                    s = self.width*p; e = s+self.width
                    self.i2c.writeto(self.addr, b'\x40'+self.buffer[s:e])
        except Exception as e:
            # Drop frame on bus error rather than crashing
            pass

try:
    if addrs:
        disp = SH1106_I2C(OLED_W, OLED_H, i2c, addr=addrs[0])
        g.disp = disp
    else:
        raise Exception("No display")
except Exception:
    class DummyDisp:
        def __init__(self):
            # Mock FrameBuffer attributes for modes.py compatibility
            class DummyFB:
                def text(self, *a, **k): pass
                def pixel(self, *a, **k): pass
                def line(self, *a, **k): pass
                def fill(self, *a, **k): pass
                def rect(self, *a, **k): pass
                def fill_rect(self, *a, **k): pass
                def hline(self, *a, **k): pass
                def vline(self, *a, **k): pass
            self.fb = DummyFB()
            
        def fill(self,c): pass
        def text(self,s,x,y,c=1): pass
        def degree(self,x,y,c=1): pass
        def show(self): pass
        def line(self,x1,y1,x2,y2,c=1): pass
        def pixel(self,x,y,c=1): pass
    disp = DummyDisp(); g.disp = disp

# ---------------- RTC Init ----------------
RTC_ADDR = 0x68
if RTC_ADDR in addrs:
    try:
        # First try as DS3232 (has SRAM)
        rtc = DS323x(i2c, addr=RTC_ADDR, has_sram=True)
        # Probe SRAM stickiness to confirm it's real memory (DS3232 only)
        # Use Read-Modify-Write-Restore strategy at the END of SRAM to avoid nuking the header
        target_addr = rtc.SRAM_END
        
        try:
            # Skip destructive write test to avoid corrupting saved state
            # target_addr = rtc.SRAM_END
            # ... (test code removed/commented)
            
            # Assume success if we initialized DS3232 without error
            rtc.has_sram = True
            print("RTC: DS3232 detected (SRAM assumes validated).")
            
        except Exception as e:
            print(f"SRAM Probe Error: {e}")
            rtc.has_sram = True # Optimistic fallback
        
        g.rtc = rtc
        utils.sync_system_time(rtc)
        if rtc.datetime() is not None:
            print("RTC found and initialized.")
    except Exception as e:
        print(f"RTC found in scan but init failed: {e}")
        g.rtc = None
else:
    print("RTC: No device found at 0x68 (DS3231/DS3232 absent).")
    g.rtc = None

# ---------------- Encoder + Buttons ----------------
enc_a = Pin(pins.ENC_A_PIN, Pin.IN, Pin.PULL_UP)
enc_b = Pin(pins.ENC_B_PIN, Pin.IN, Pin.PULL_UP)
enc_btn = Pin(pins.ENC_BTN_PIN, Pin.IN, Pin.PULL_UP)
BACK_BTN = Pin(pins.BACK_BTN_PIN, Pin.IN, Pin.PULL_UP)
CONFIRM_BTN = Pin(pins.CONFIRM_BTN_PIN, Pin.IN, Pin.PULL_UP)

state = (enc_a.value()<<1) | enc_b.value()
raw_count = 0
TRANS = (0,+1,-1,0,  -1,0,0,+1,  +1,0,0,-1,  0,-1,+1,0)

def _enc_isr(_):
    global state, raw_count
    s = (enc_a.value()<<1) | enc_b.value()
    d = TRANS[(state<<2)|s]
    raw_count -= d
    state = s

enc_a.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)
enc_b.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)

# Event queue for button presses
button_events = []
# Per-button debounce tracking
last_btn_times = {}

def _button_isr(pin):
    global button_events, last_btn_times
    now = time.ticks_ms()
    pin_id = id(pin)
    last_time = last_btn_times.get(pin_id, 0)
    if time.ticks_diff(now, last_time) > DEBOUNCE_MS:
        last_btn_times[pin_id] = now
        button_events.append(pin)

enc_btn.irq(trigger=Pin.IRQ_FALLING, handler=_button_isr)
BACK_BTN.irq(trigger=Pin.IRQ_FALLING, handler=_button_isr)
CONFIRM_BTN.irq(trigger=Pin.IRQ_FALLING, handler=_button_isr)

# ---------------- Startup Time Sync (Pico 2W only) ----------------
has_wifi = False
if True: ## False to disable wifi for debugging
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        has_wifi = True
    except Exception:
        has_wifi = False

if has_wifi:
    try:
        import wifi_setup
        with open("wifi_config.json", "r") as f:
            config = json.load(f)
        ssid = config["ssid"]
        password = config["password"]
        
        sync_done = False
        while not sync_done:
            disp.fill(0)
            disp.text("Orbigator", 0, 0)
            disp.text("Connecting...", 0, 16)
            disp.show()
            
            ip = wifi_setup.connect_wifi(ssid, password)
            if ip:
                disp.fill(0)
                disp.text("Orbigator", 0, 0)
                disp.text("Syncing Time...", 0, 16)
                disp.show()
                
                try:
                    import ntptime, machine
                    print("Settling network...")
                    time.sleep(4) # Give stack a moment
                    
                    for attempt in range(5):
                        try:
                            print(f"NTP Sync attempt {attempt+1}...")
                            ntptime.host = "pool.ntp.org" 
                            before_sync = time.time()
                            ntptime.settime()
                            after_sync = time.time()
                            t = machine.RTC().datetime()
                            utils.set_datetime(t[0], t[1], t[2], t[4], t[5], t[6], g.rtc)
                            
                            correction = after_sync - before_sync
                            print(f"✓ NTP Sync OK: {ip}")
                            print(f"  RTC Correction: {correction:+.1f}s")
                            sync_done = True
                            break
                        except Exception as e:
                            print(f"  Attempt {attempt+1} failed: {e}")
                            time.sleep(2)
                    
                    if not sync_done:
                        print("NTP Sync permanently failed. Proceeding with local/RTC time.")
                        sync_done = True
                except Exception as e:
                    print(f"WiFi/Time setup error: {e}")
                    sync_done = True
            else:
                print("WiFi connection failed during boot.")
                # Also prompt on WiFi failure? Or just proceed?
                # For now, let's proceed to allow offline use without being stuck.
                sync_done = True
    except Exception as e:
        print(f"WiFi/Time setup error: {e}")

# ---------------- State Loading ----------------
# Load state first so we can restore motor positions if needed
state_info = utils.load_state()
default_mode_id = "SGP4" if has_wifi else "ORBIT"
g.current_mode_id = state_info.get("mode_id", default_mode_id)
g.last_save_timestamp = state_info.get("timestamp", 0)
saved_sat_name = state_info.get("sat_name", None)

# ---------------- Motor Init ----------------
if ENABLE_MOTORS:
    print("\nInitializing DYNAMIXEL motors...")
    
    # Hard reset motors to clear any error states
    from dynamixel_extended_utils import reboot_motor, read_present_position
    reboot_motor(AOV_MOTOR_ID)
    reboot_motor(EQX_MOTOR_ID)
    
    # Verify motors reset to 0-4095 range after reboot
    aov_raw = read_present_position(AOV_MOTOR_ID)
    eqx_raw = read_present_position(EQX_MOTOR_ID)
    print(f"  [POST-REBOOT] AoV raw={aov_raw}, EQX raw={eqx_raw}")
    
    set_extended_mode(AOV_MOTOR_ID)
    set_extended_mode(EQX_MOTOR_ID)
    
    # Pass offset_degrees to constructor
    aov_offset = mc["aov"].get("offset_deg", 0.0)
    eqx_offset = mc["eqx"].get("offset_deg", 0.0)

    # Restore orientations from state if valid (V4 uses abs_ticks, Legacy uses deg)
    last_aov = state_info.get("aov_deg") if state_info.get("timestamp", 0) > 0 else None
    last_eqx = state_info.get("eqx_deg") if state_info.get("timestamp", 0) > 0 else None
    
    aov_abs = state_info.get("aov_abs_ticks")
    eqx_abs = state_info.get("eqx_abs_ticks")

    aov_motor = DynamixelMotor(AOV_MOTOR_ID, "AoV", gear_ratio=AOV_GEAR_RATIO,
                               offset_degrees=aov_offset, 
                               direction=1, # Slew: Forward Only (Cable Safety)
                               recovery_direction=1, # Boot: Direction-Aware
                               last_known_pos=last_aov, last_abs_ticks=aov_abs)
    g.aov_motor = aov_motor
    
    eqx_motor = DynamixelMotor(EQX_MOTOR_ID, "EQX", gear_ratio=EQX_GEAR_RATIO, 
                               offset_degrees=eqx_offset, 
                               direction=None, # Slew: Shortest Path
                               recovery_direction=1, # Boot: Direction-Aware
                               last_known_pos=last_eqx, last_abs_ticks=eqx_abs)
    g.eqx_motor = eqx_motor
    
    # Configure from loaded config
    aov_pid = mc["aov"]["pid"]
    aov_motor.set_pid_gains(p=aov_pid["p"], i=aov_pid["i"], d=aov_pid["d"])
    aov_motor.set_speed_limit(mc["aov"]["speed_limit"])
    
    eqx_pid = mc["eqx"]["pid"]
    eqx_motor.set_pid_gains(p=eqx_pid["p"], i=eqx_pid["i"], d=eqx_pid["d"])
    eqx_motor.set_speed_limit(mc["eqx"]["speed_limit"])
    
    # Explicitly enable torque to ensure motion
    print("Forcing Torque ON...")
    aov_motor.enable_torque()
    eqx_motor.enable_torque()
    
    # Wire up turn change callbacks for SRAM persistence
    aov_motor.on_turn_change = utils.save_state
    eqx_motor.on_turn_change = utils.save_state
else:
    print("\nMotors DISABLED - Using mock motors for web development")
    from mock_motor import MockMotor
    g.aov_motor = MockMotor(AOV_MOTOR_ID, "AoV", gear_ratio=AOV_GEAR_RATIO)
    g.eqx_motor = MockMotor(EQX_MOTOR_ID, "EQX", gear_ratio=EQX_GEAR_RATIO)

# ---------------- Hardware Detection ----------------
def check_wifi_available():
    try:
        import network
        # Check if WLAN class exists and can be instantiated
        if hasattr(network, 'WLAN'):
            return True
    except:
        pass
    return False

HAS_WIFI = check_wifi_available()

# ---------------- Mode Selection ----------------
# Select initial mode and initialize its parameters
# Priority: 1. SRAM saved mode, 2. Hardware-specific default
if g.current_mode_id == "SGP4":
    g.current_mode = SGP4Mode()
    g.current_mode.enter()
    if saved_sat_name:
        g.current_mode.select_satellite_by_name(saved_sat_name)
elif g.current_mode_id == "DATETIME":
    g.current_mode = DatetimeEditorMode(next_mode=OrbitMode())
    g.current_mode.enter()
elif g.current_mode_id == "ORBIT":
    g.current_mode = OrbitMode()
    g.current_mode.enter()
else:
    # Fallback/Default based on Hardware
    if HAS_WIFI:
        print("Hardware: Pico 2W detected. Defaulting to SGP4.")
        g.current_mode = SGP4Mode()
    else:
        print("Hardware: Pico 2 detected. Defaulting to Orbit Mode.")
        g.current_mode = OrbitMode()
    g.current_mode.enter()
    if g.current_mode_id == "SGP4" and saved_sat_name:
        g.current_mode.select_satellite_by_name(saved_sat_name)

# ---------------- Synchronous Alignment ----------------
if ENABLE_MOTORS and g.current_mode_id != "DATETIME":
    # 1. Get the TARGET position from the propagator
    print("\nCalculating initial satellite position...")
    
    if hasattr(g.current_mode, 'propagator') and g.current_mode.propagator:
        result = g.current_mode.propagator.get_aov_eqx(utils.get_timestamp())
        target_aov = result[0] % 360
        target_eqx = result[1] % 360
    else:
        # Fallback for modes without propagator
        target_aov = 0.0
        target_eqx = 0.0
    
    # 2. Log current hardware position vs target
    phys_eqx = eqx_motor.output_degrees % 360
    phys_aov = aov_motor.output_degrees % 360
    
    print(f"  [AoV] Hardware: {phys_aov:.1f}° → Target: {target_aov:.1f}°")
    print(f"  [EQX] Hardware: {phys_eqx:.1f}° → Target: {target_eqx:.1f}°")
    
    # Update globals
    g.eqx_position_deg = target_eqx
    g.aov_position_deg = target_aov

    # 3. Synchronous Alignment - motors will catch up to target
    print("Aligning Motors (Synchronous)...")
    disp.fill(0)
    disp.text("Aligning Motors", 0, 16)
    disp.show()

    # Use configured speed limits for alignment
    aov_motor.set_speed_limit(mc["aov"]["speed_limit"]) 
    eqx_motor.set_speed_limit(mc["eqx"]["speed_limit"])
    
    # Send initial command (should be near-zero delta)
    aov_motor.set_nearest_degrees(target_aov)
    eqx_motor.set_nearest_degrees(target_eqx)

    aligned = False
    start_align = time.ticks_ms()
    while not aligned and time.ticks_diff(time.ticks_ms(), start_align) < 20000: # 20s timeout
        # Poll actual positions
        now_aov = aov_motor.update_present_position(force=True)
        now_eqx = eqx_motor.update_present_position(force=True)
        
        # Check delta using phase-aware logic
        # target_aov is already normalized to % 360 in the mode update
        err_aov = abs((now_aov - target_aov + 180) % 360 - 180)
        err_eqx = abs((now_eqx - target_eqx + 180) % 360 - 180)
        
        if err_aov < 1.0 and err_eqx < 1.0:
            aligned = True
            print("✓ Sync Complete.")
        else:
            print(f"  Catching up... EQX Phase: {now_eqx % 360:.1f}° -> {target_eqx:.1f}°")
            time.sleep_ms(500)
    
    # Restore simulation speed
    aov_motor.set_speed_limit(mc["aov"]["speed_limit"])
    eqx_motor.set_speed_limit(mc["eqx"]["speed_limit"])

last_detent = 0
last_display_update = 0
print("Orbigator Ready.")

# ---------------- Start Web Server in Background (Pico 2W only) ----------------
if has_wifi:
    status = "Starting web services..." if g.web_server_enabled else "Web services disabled."
    print(f"WiFi hardware detected. {status}")
    if g.web_server_enabled:
        utils.start_web_server_thread()
else:
    print("No WiFi hardware detected.")

# ---------------- Main Loop ----------------
try:
    while True:
        try:
            time.sleep_ms(10)
            now = time.ticks_ms()
            
            # 0. Check for Requested Mode Change (from Web Server)
            if g.next_mode:
                print(f"Switching mode via API: {type(g.current_mode).__name__} -> {type(g.next_mode).__name__}")
                g.current_mode.exit()
                g.current_mode = g.next_mode
                g.next_mode = None
                g.current_mode.enter()
                utils.save_state() # Proactively save new mode from API
            
            # 1. Poll Encoder Rotation
            irq = machine.disable_irq(); rc = raw_count; machine.enable_irq(irq)
            d = rc // DETENT_DIV
            if d != last_detent:
                delta = d - last_detent
                last_detent = d
                g.current_mode.on_encoder_rotate(delta)
            
            # 2. Process Button Events (ISR-driven)
            while button_events:
                try:
                    pin = button_events.pop(0)
                    
                    new_mode = None
                    if pin == enc_btn:
                        new_mode = g.current_mode.on_encoder_press()
                    elif pin == CONFIRM_BTN:
                        new_mode = g.current_mode.on_confirm()
                    elif pin == BACK_BTN:
                        new_mode = g.current_mode.on_back()
                        
                    if new_mode:
                        btn_name = "ENC" if pin == enc_btn else "CONFIRM" if pin == CONFIRM_BTN else "BACK"
                        print(f"Transition via Button [{btn_name}]: {type(g.current_mode).__name__} -> {type(new_mode).__name__}")
                        g.current_mode.exit()
                        g.current_mode = new_mode
                        g.current_mode.enter()
                        utils.save_state()
                        print(f"Transition complete.")
                except Exception as e:
                    print(f"Error handling button: {e}")
            
            # 3. Check Motor Health
            if not g.motor_health_ok and g.motor_offline_id is not None:
                # Transition to offline mode
                motor_name = "AoV" if g.motor_offline_id == 2 else "EQX"
                g.current_mode.exit()
                import modes
                g.current_mode = modes.MotorOfflineMode(g.motor_offline_id, motor_name, g.motor_offline_error)
                g.current_mode.enter()
                
            # Note: SRAM persistence is now handled by motor.on_turn_change callback
            
            # 6. Update and Render	
            g.current_mode.update(now)
            
            if time.ticks_diff(now, last_display_update) >= 200:
                last_display_update = now
                g.current_mode.render(g.disp)
        
        except Exception as e:
            # Log crash but don't exit the loop
            import sys
            print(f"\nCRASH in main loop: {e}")
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"\n[{time.time()}] Crash: {e}\n")
                    sys.print_exception(e, f)
            except:
                pass
            time.sleep(1)  # Brief pause before continuing

except KeyboardInterrupt:
    print("\nInterrupted by user.")
finally:
    print("\nOrbigator Exiting... Saving State.")
    utils.save_state()
    print("State Saved. Goodbye.")
