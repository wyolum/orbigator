"""
Orbigator Global State
Shared state accessible by both orbigator.py and modes.py
Breaks circular import dependency
"""

# Motor objects (set by orbigator.py during initialization)
aov_motor = None
eqx_motor = None

# Hardware objects
rtc = None
disp = None
i2c_lock = None  # Thread lock for I2C bus synchronization
uart_lock = None # Thread lock for UART bus synchronization

# Orbital parameters
orbital_altitude_km = 400.0
orbital_period_min = 92.0
orbital_inclination_deg = 51.6
orbital_eccentricity = 0.0  # 0.0 = circular, 0.9 = highly elliptical
orbital_periapsis_deg = 0.0  # Argument of periapsis (0-360°)
orbital_rev_count = 0        # Total completed orbits

# Motor rates
aov_rate_deg_sec = 0.0
eqx_rate_deg_sec = 0.0
eqx_rate_deg_day = 0.0

# Position tracking
aov_position_deg = 0.0
eqx_position_deg = 0.0

# Run tracking
last_save_timestamp = 0 # Stores timestamp from last successful load
run_start_time = 0
run_start_ticks = 0
run_start_aov_deg = 0.0
run_start_eqx_deg = 0.0
initialized_orbit = False

# Motor health tracking
motor_health_ok = True  # Global health flag
motor_offline_id = None  # ID of offline motor (if any)
motor_offline_error = ""  # Error description

# UI Mode tracking
current_mode_id = "SGP4" # ORBIT, SGP4, MENU, etc.
current_mode = None # The actual Mode instance (e.g. OrbitMode())
next_mode = None # For requesting mode changes from other threads (e.g. Web Server)
web_server_enabled = True # Whether the web server should be running (Pico 2W)
ui = None # The Mode Stack Interface

# OLED Idle / Burn-In Prevention
last_input_ticks = 0       # ticks_ms of last user input
oled_timeout_ms  = 120_000 # 2 min default; 0 = never sleep

# Overhead Alert Radar
observer_lat    = None  # float or None
observer_lon    = None  # float or None
observer_frame  = None  # ObserverFrame instance (precomputed ENU vectors)
overhead_watcher = None # OverheadWatcher instance
radar_display   = None  # RadarDisplay instance

# Display Mode (HUD or FOV)
display_mode = "HUD"

