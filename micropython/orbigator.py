# Orbigator - Orbital Mechanics Simulator
# Pico 2 | DYNAMIXEL XL330-M288-T motors
# ------------------------------------------------------------------

import machine, time, math, json
from machine import Pin, I2C
import framebuf
from ds323x import DS323x
from dynamixel_motor import DynamixelMotor
from absolute_motor import AbsoluteDynamixel
from dynamixel_extended_utils import set_extended_mode
import orb_globals as g
import orb_utils as utils
import pins
from modes import MenuMode, OrbitMode, DatetimeEditorMode, SGP4Mode
import _thread  # For I2C lock
import capabilities
# Set to False for web development without motors
ENABLE_MOTORS = True

# ---------------- Load Configuration ----------------
try:
    with open("orbigator_config.json", "r") as f:
        config_data = json.load(f)
    print("Configuration loaded from orbigator_config.json")
except Exception as e:
    print(f"Config load error: {e}. Using defaults.")
    config_data = {
        "motors": {
            "eqx": {"id": 1,
                    "gear_ratio_num": 120.0,
                    "gear_ratio_den": 14.0,
                    "pid": {"p": 600, "i": 0, "d": 0},
                    "speed_limit": 50, "offset_deg": 0.0},
            "aov": {"id": 2,
                    "gear_ratio_num": 1.0,
                    "gear_ratio_den": 1.0,
                    "pid": {"p": 600, "i": 0, "d": 0},
                    "speed_limit": 20,
                    "offset_deg": 0.0}
        },
        "system": {"detent_div": 4,
                   "debounce_ms": 200,
                   "oled": {"width": 128, "height": 64}}
    }
    
    # ---------------- Identify Capabilities (R4.2) ----------------
caps = capabilities.get_capabilities()
g.caps = caps # Store for mode/UI access
print(f"Hardware Identity: {caps.hw_type}")
print(f"Features: WiFi={caps.has_wifi}, ",
      f"Web={caps.has_web_server}, "
      f"NTP={caps.has_ntp}")

# Hardware Configuration
mc = config_data.get("motors", {})
EQX_MOTOR_ID = mc.get("eqx", {}).get("id", 1)
AOV_MOTOR_ID = mc.get("aov", {}).get("id", 2)
EQX_GEAR_RATIO = mc.get("eqx", {}).get("gear_ratio_num", 120.0) / mc.get("eqx", {}).get("gear_ratio_den", 14.0)
AOV_GEAR_RATIO = mc.get("aov", {}).get("gear_ratio_num", 1.0) / mc.get("aov", {}).get("gear_ratio_den", 1.0)

DETENT_DIV = config_data.get("system", {}).get("detent_div", 4)
DEBOUNCE_MS = 300 

# 1. CORE SUBSYSTEMS (RTC, Cache, Motors) - (R4.3)
i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400_000)
addrs = i2c.scan()

# Initialize Globals
print(f"Orbigator Booting... System Time: {time.time()}")
utils.init_software_clock() 
if g.i2c_lock is None: g.i2c_lock = _thread.allocate_lock()
if g.uart_lock is None: g.uart_lock = _thread.allocate_lock()

# Display (Simplified logic for brevity in refactor)
# Display 
try:
    from sh1106 import SH1106_I2C
except ImportError:
    # Fallback if file missing
    print("Warning: sh1106.py missing, using dummy display")
    class SH1106_I2C:
        def __init__(self, w,h,i2c,addr=0x3C): pass
        def fill(self,c): pass 
        def text(self,s,x,y,c=1): pass
        def degree(self,x,y,c=1): pass
        def show(self): pass
        def line(self,x1,y1,x2,y2,c=1): pass
        def pixel(self,x,y,c=1): pass


OLED_W = config_data.get("system", {}).get("oled", {}).get("width", 128)
OLED_H = config_data.get("system", {}).get("oled", {}).get("height", 64)
try:
    if addrs:
        disp = SH1106_I2C(OLED_W, OLED_H, i2c, addr=addrs[0])
        g.disp = disp
    else: raise Exception("No display")
except Exception as _disp_err:
    print(f"Display init failed: {_disp_err}")
    class DummyDisp:
        def __init__(self):
            self.is_sleeping = False
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
        def sleep(self): self.is_sleeping = True
        def wake(self): self.is_sleeping = False
    disp = DummyDisp(); g.disp = disp

# RTC Init
RTC_ADDR = 0x68
if RTC_ADDR in addrs:
    try:
        rtc = DS323x(i2c, addr=RTC_ADDR, has_sram=True)
        g.rtc = rtc
        utils.sync_system_time(rtc)
        print("RTC found and initialized.")
    except Exception as e:
        print(f"RTC init failed: {e}")
        g.rtc = None
else:
    print("RTC: Absent.")
    g.rtc = None

# Encoder + Buttons
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
    raw_count -= d; state = s
enc_a.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)
enc_b.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=_enc_isr)

button_events = []
last_btn_times = {}
def _button_isr(pin):
    global button_events, last_btn_times
    now = time.ticks_ms()
    pid = id(pin)
    if time.ticks_diff(now, last_btn_times.get(pid, 0)) > DEBOUNCE_MS:
        last_btn_times[pid] = now; button_events.append(pin)
enc_btn.irq(trigger=Pin.IRQ_FALLING, handler=_button_isr)
BACK_BTN.irq(trigger=Pin.IRQ_FALLING, handler=_button_isr)
CONFIRM_BTN.irq(trigger=Pin.IRQ_FALLING, handler=_button_isr)

# 2. NETWORKING / NTP (R4.4) - ONLY ON PICO 2W
if caps.has_wifi:
    try:
        import networking
        wifi_cfg = None
        try:
            with open("wifi_config.json", "r") as f:
                wifi_cfg = json.load(f)
        except OSError:
            print("Networking: wifi_config.json not found. Skipping auto-connect.")
            
        if wifi_cfg:
            ip = networking.connect_wifi(wifi_cfg["ssid"], wifi_cfg["password"], display=disp)
            if ip:
                if caps.has_ntp:
                    import ntp_sync
                    ntp_sync.sync_ntp(display=disp)
    except Exception as e:
        print(f"Networking/NTP guarded error: {e}")
else:
    print("Networking: Disabled (Pico 2 or Override). Skipping Wi-Fi/NTP.")

# 3. STATE CACHE (R4.3)
state_info = utils.load_state()
default_mode_id = "SGP4" if caps.has_wifi else "ORBIT"
g.current_mode_id = state_info.get("mode_id", default_mode_id)
g.last_save_timestamp = state_info.get("timestamp", 0)
saved_sat_name = state_info.get("sat_name", None)

# ---------------- Motor Init ----------------
if ENABLE_MOTORS:
    print("\nInitializing DYNAMIXEL motors...")
    
    # Motors initialized by AbsoluteDynamixel class (includes reboot & mode set)
    
    aov_offset = mc["aov"].get("offset_deg", 0.0)
    eqx_offset = mc["eqx"].get("offset_deg", 0.0)
    
    # AoV: SRAM Slot 1 (starts at 0x80 + 10 = 0x8A)
    # Direction 1 = Forward Only
    from absolute_motor import AbsoluteDynamixel
    aov_motor = AbsoluteDynamixel(AOV_MOTOR_ID, g.rtc, gear_ratio=AOV_GEAR_RATIO, 
                                  sram_slot=1, offset_degrees=aov_offset, direction=1)
    aov_motor.name = "AoV"
    g.aov_motor = aov_motor
    
    # EQX: SRAM Slot 0 (starts at 0x80)
    # Direction None = Shortest Path
    eqx_motor = AbsoluteDynamixel(EQX_MOTOR_ID, g.rtc, gear_ratio=EQX_GEAR_RATIO, 
                                  sram_slot=0, offset_degrees=eqx_offset, direction=None)
    eqx_motor.name = "EQX"
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
    
    # EQX & AoV now handle persistence internally via AbsoluteDynamixel
else:
    print("\nMotors DISABLED - Using mock motors for web development")
    from mock_motor import MockMotor
    g.aov_motor = MockMotor(AOV_MOTOR_ID, "AoV", gear_ratio=AOV_GEAR_RATIO)
    g.eqx_motor = MockMotor(EQX_MOTOR_ID, "EQX", gear_ratio=EQX_GEAR_RATIO)

# ---------------- Mode Selection (R4.5) ----------------
import modes
g.ui = modes.ModeStack()

if g.current_mode_id == "SGP4" or default_mode_id == "SGP4":
    # If SGP4 is requested (or default), try to set it up
    # If standard boot, verify SGP4 works?
    mode = SGP4Mode()
    g.ui.set_root(mode)
    if saved_sat_name:
        mode.select_satellite_by_name(saved_sat_name)
elif g.current_mode_id == "DATETIME":
    # Booting into Date/Time editor (wizard)
    # We push Orbit as root, then push Datetime
    g.ui.set_root(OrbitMode())
    dt_mode = DatetimeEditorMode()
    # Logic in modes.py handles next_mode if needed, or we just rely on pop()
    # But DatetimeEditorMode on boot typically leads to OrbitMode.
    # If we push it on top of OrbitMode, popping it returns to OrbitMode. Perfect.
    g.ui.push(dt_mode)
else:
    # Default to Orbit
    g.ui.set_root(OrbitMode())

def _arm_overhead_alert(lat, lon):
    from observer_frame import ObserverFrame
    from overhead_watcher import OverheadWatcher
    from radar_display import RadarDisplay
    g.observer_lat = lat
    g.observer_lon = lon
    g.observer_frame   = ObserverFrame(lat, lon)
    g.overhead_watcher = OverheadWatcher()
    g.radar_display    = RadarDisplay()
    print(f"Overhead Alert: armed at ({lat:.1f}, {lon:.1f})")

# Try WiFi auto-fetch first (Pico 2W)
if g.caps.has_wifi:
    try:
        loc = utils.fetch_observer_location()
        if loc:
            _arm_overhead_alert(*loc)
    except Exception as e:
        print(f"Overhead Alert WiFi fetch failed: {e}")

# Fall back to saved location (works on non-WiFi hardware)
if g.observer_frame is None and g.observer_lat is not None:
    try:
        _arm_overhead_alert(g.observer_lat, g.observer_lon)
    except Exception as e:
        print(f"Overhead Alert init failed: {e}")
        g.observer_frame = None

    
# ---------------- Synchronous Alignment ----------------
if ENABLE_MOTORS and g.current_mode_id != "DATETIME":
    # 1. Get the TARGET position from the propagator
    print("\nCalculating initial satellite position...")
    
    active_mode = g.ui.current
    
    if hasattr(active_mode, 'propagator') and active_mode.propagator:
        result = active_mode.propagator.get_aov_eqx(utils.get_timestamp())
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
            print(f"  Catching up... AoV: {now_aov % 360:.1f}°->{target_aov:.1f}° (Err:{err_aov:.1f}) | EQX: {now_eqx % 360:.1f}°->{target_eqx:.1f}° (Err:{err_eqx:.1f})")
            time.sleep_ms(500)
    
    # Restore simulation speed
    aov_motor.set_speed_limit(mc["aov"]["speed_limit"])
    eqx_motor.set_speed_limit(mc["eqx"]["speed_limit"])

last_detent = 0
last_display_update = 0
print("Orbigator Ready.")

# ---------------- Start Web Server in Background (Pico 2W only) ----------------
if caps.has_wifi:
    status = "Starting web services..." if g.web_server_enabled else "Web services disabled."
    print(f"WiFi enabled. {status}")
    if g.web_server_enabled:
        utils.start_web_server_thread()
else:
    print("WiFi disabled or not present.")

# ---------------- Main Loop ----------------
try:
    while True:
        try:
            time.sleep_ms(10)
            now_ms = time.ticks_ms()
            
            # 0. Check for Requested Mode Change (from Web Server)
            if g.next_mode:
                print(f"Switching mode via API: -> {type(g.next_mode).__name__}")
                g.ui.set_root(g.next_mode)
                g.next_mode = None
                utils.save_state()
            
            # 1. Poll Encoder Rotation
            irq = machine.disable_irq(); rc = raw_count; machine.enable_irq(irq)
            d = rc // DETENT_DIV
            if d != last_detent:
                delta = d - last_detent
                last_detent = d
                g.ui.handle_input("ENC_ROTATE", delta)
            
            # 2. Process Button Events (ISR-driven)
            while button_events:
                try:
                    pin = button_events.pop(0)
                    
                    if pin == enc_btn:
                        g.ui.handle_input("ENC_PRESS")
                    elif pin == CONFIRM_BTN:
                        g.ui.handle_input("CONFIRM")
                    elif pin == BACK_BTN:
                        g.ui.handle_input("BACK")
                        
                except Exception as e:
                    print(f"Error handling button: {e}")
            
            # 3. Check Motor Health
            if not g.motor_health_ok and g.motor_offline_id is not None:
                # Transition to offline mode
                motor_name = "AoV" if g.motor_offline_id == 2 else "EQX"
                if not isinstance(g.ui.current, modes.MotorOfflineMode):
                     g.ui.push(modes.MotorOfflineMode(g.motor_offline_id, motor_name, g.motor_offline_error))
                
            # 4. Update and Render	
            g.ui.update(now_ms)
            
            if time.ticks_diff(now_ms, last_display_update) >= 200:
                last_display_update = now_ms
                g.ui.render(g.disp)
        
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
