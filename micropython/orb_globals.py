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

# Orbital parameters
orbital_altitude_km = 400.0
orbital_period_min = 92.0
orbital_inclination_deg = 51.6

# Motor rates
aov_rate_deg_sec = 0.0
eqx_rate_deg_sec = 0.0
eqx_rate_deg_day = 0.0

# Position tracking
aov_position_deg = 0.0
eqx_position_deg = 0.0

# Run tracking
run_start_time = 0
run_start_ticks = 0
run_start_aov_deg = 0.0
run_start_eqx_deg = 0.0

# Motor health tracking
motor_health_ok = True  # Global health flag
motor_offline_id = None  # ID of offline motor (if any)
motor_offline_error = ""  # Error description
