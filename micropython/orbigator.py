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
from modes import MenuMode, OrbitMode, DatetimeEditorMode
import _thread  # For I2C lock


# ---------------- Hardware Config ----------------
AOV_MOTOR_ID = 2
EQX_MOTOR_ID = 1
EQX_GEAR_RATIO = 120.0 / 14.0
AOV_GEAR_RATIO = 1.0

DETENT_DIV = 4
DEBOUNCE_MS = 200

# ---------------- OLED Init ----------------
OLED_W, OLED_H = 128, 64
i2c = I2C(pins.I2C_ID, sda=Pin(pins.I2C_SDA_PIN), scl=Pin(pins.I2C_SCL_PIN), freq=400_000)
addrs = i2c.scan()

# Initialize Globals
print(f"Orbigator Booting... System Time: {time.time()}")
# Initialize global lock if not already done
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
        def fill(self,c): pass
        def text(self,s,x,y,c=1): pass
        def show(self): pass
    disp = DummyDisp(); g.disp = disp

# ---------------- RTC Init ----------------
RTC_ADDR = 0x68
if RTC_ADDR in addrs:
    try:
        # First try as DS3232 (has SRAM)
        rtc = DS323x(i2c, addr=RTC_ADDR, has_sram=True)
        # Probe SRAM stickiness to confirm it's real memory (DS3232 only)
        test_val = 0x5A
        rtc.write_sram(rtc.SRAM_START, bytes([test_val]))
        read_back = rtc.read_sram(rtc.SRAM_START, 1)
        
        if read_back and read_back[0] == test_val:
            # Second test value to be absolutely sure
            rtc.write_sram(rtc.SRAM_START, bytes([0xA5]))
            read_back = rtc.read_sram(rtc.SRAM_START, 1)
            if read_back and read_back[0] == 0xA5:
                print("RTC: DS3232 detected (SRAM verified).")
                rtc.has_sram = True
            else:
                rtc.has_sram = False
        else:
            print("RTC: No SRAM persistence, falling back to DS3231 mode.")
            rtc.has_sram = False
        
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
                    ntptime.settime()
                    t = machine.RTC().datetime()
                    utils.set_datetime(t[0], t[1], t[2], t[4], t[5], t[6], g.rtc)
                    print(f"✓ NTP Sync OK: {ip}")
                    sync_done = True
                except Exception as e:
                    print(f"NTP Sync failed: {e}")
                    # Prompt for Retry/Ignore
                    prompting = True
                    button_events.clear()
                    while prompting:
                        disp.fill(0)
                        disp.text("[Back] Ignore", 0, 0)
                        disp.text("   NTP Failed", 0, 24)
                        disp.text("[Confirm] Retry", 0, 54)
                        # disp.text(f"Err: {str(e)[:16]}", 0, 36) # Error might clutter, maybe skip or put small?
                        # User reduced layout suggests simple. I'll omit error details or put them very small if needed, but request implies simple.
                        # Let's stick to the requested 3 lines.
                        disp.show()
                        
                        if button_events:
                            btn = button_events.pop(0)
                            if btn == CONFIRM_BTN:
                                prompting = False # Loop back to retry WiFi+NTP
                            elif btn == BACK_BTN:
                                prompting = False
                                sync_done = True # Proceed with RTC
                        time.sleep_ms(50)
            else:
                print("WiFi connection failed during boot.")
                # Also prompt on WiFi failure? Or just proceed?
                # For now, let's proceed to allow offline use without being stuck.
                sync_done = True
    except Exception as e:
        print(f"WiFi/Time setup error: {e}")

# ---------------- Motor Init ----------------
print("\nInitializing DYNAMIXEL motors...")
set_extended_mode(AOV_MOTOR_ID)
set_extended_mode(EQX_MOTOR_ID)

aov_motor = DynamixelMotor(AOV_MOTOR_ID, "AoV", gear_ratio=AOV_GEAR_RATIO)
g.aov_motor = aov_motor
eqx_motor = DynamixelMotor(EQX_MOTOR_ID, "EQX", gear_ratio=EQX_GEAR_RATIO)
g.eqx_motor = eqx_motor

aov_motor.set_pid_gains(p=600, d=0)
aov_motor.set_speed_limit(2) # Capped at 2 or 3 for safety
eqx_motor.set_pid_gains(p=600, d=0)
eqx_motor.set_speed_limit(10) # Capped at 10 for safety

# ---------------- State and Loop ----------------
# Load state and reconstruct positions
state_info = utils.load_state()
saved_mode_id = state_info.get("mode_id", "ORBIT")
saved_sat_name = state_info.get("sat_name", None)

# Check for RTC reset (e.g. battery failure)
# Check for RTC reset (Year < 2024 invalid implies dead battery or fresh Pico)
lt = time.localtime()
if lt[0] < 2024:
    print(f"RTC Year {lt[0]} invalid! Prompting for time.")
    g.current_mode = DatetimeEditorMode(next_mode=OrbitMode())
else:
    # Resume last mode
    if saved_mode_id == "SGP4":
        import modes
        g.current_mode = modes.SGP4Mode()
        g.current_mode.enter()
        if saved_sat_name:
            g.current_mode.select_satellite_by_name(saved_sat_name)
    else:
        # Default to OrbitMode
        g.current_mode = OrbitMode()
        g.current_mode.enter()

last_detent = 0
last_display_update = 0

print("Orbigator Ready.")

# ---------------- Start Web Server in Background (Pico 2W only) ----------------
if has_wifi:
    print("WiFi hardware detected.")
else:
    print("NO WiFi HARDWARE.  Confirmed")

if has_wifi:
    import _thread

    def start_web_server():
        """Start web server in background thread"""
        try:
            import network
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                import web_server
                web_server.start_server(port=80)
            else:
                print("Web server skipped: No WiFi connection.")
        except Exception as e:
            print(f"Web server error: {e}")

    # Start web server in separate thread
    # Start web server in separate thread
    try:
        _thread.start_new_thread(start_web_server, ())
        print("Web server thread started")
    except Exception as e:
        print(f"Failed to start web server thread: {e}")

# ---------------- Main Loop ----------------
while True:
    time.sleep_ms(10)
    now = time.ticks_ms()
    
    # 0. Check for Requested Mode Change (from Web Server)
    if g.next_mode:
        print(f"Switching mode via API...")
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
                print(f"Transition: {type(g.current_mode).__name__} -> {type(new_mode).__name__}")
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
    
    # 6. Update and Render
    g.current_mode.update(now)
    
    if time.ticks_diff(now, last_display_update) >= 200:
        last_display_update = now
        g.current_mode.render(g.disp)
