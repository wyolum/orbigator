from machine import Pin
import time
import math

# ULN2003 input pins → Pico GPIOs
IN1 = Pin(2, Pin.OUT)
IN2 = Pin(3, Pin.OUT)
IN3 = Pin(22, Pin.OUT)
IN4 = Pin(26, Pin.OUT)

# Standard 28BYJ-48 half-step sequence (IN1, IN2, IN3, IN4)
half_step = [
    (1,0,0,0),
    (1,1,0,0),
    (0,1,0,0),
    (0,1,1,0),
    (0,0,1,0),
    (0,0,1,1),
    (0,0,0,1),
    (1,0,0,1),
]

def output_step(seq):
    IN1.value(seq[0])
    IN2.value(seq[1])
    IN3.value(seq[2])
    IN4.value(seq[3])

def get_delay(step_in_phase, phase_steps, v_start, v_end):
    """
    Get delay for a step within accel/decel phase.
    Uses smoothstep: v = v_start + (v_end - v_start) * (3p² - 2p³)
    """
    p = (step_in_phase + 0.5) / phase_steps
    blend = p * p * (3.0 - 2.0 * p)
    v = v_start + (v_end - v_start) * blend
    return int(1_000_000 / v)

def rotate_smooth(steps, direction=1, max_speed_hz=500, min_speed_hz=50, jerk=10000):
    """
    Rotate with S-curve profile, computed on-the-fly (no arrays).
    
    steps: total half-steps to rotate
    direction: +1 or -1
    max_speed_hz: cruise speed (steps/sec)
    min_speed_hz: start/end speed (steps/sec)
    jerk: rate of change of acceleration (steps/sec³)
          Higher jerk = faster/shorter accel ramp
          Lower jerk = slower/gentler accel ramp
    """
    if steps == 0:
        return
    
    idx = 0
    n = len(half_step)
    
    # Calculate accel distance from jerk using S-curve formula:
    # accel_distance = (v_start + v_end) * sqrt(delta_v / jerk)
    delta_v = max_speed_hz - min_speed_hz
    accel_steps = int((min_speed_hz + max_speed_hz) * math.sqrt(delta_v / jerk))
    
    # Ensure we have at least a few steps for accel/decel
    accel_steps = max(accel_steps, 10)
    
    decel_steps = accel_steps
    
    # Clamp if not enough total steps
    if accel_steps + decel_steps > steps:
        accel_steps = steps // 2
        decel_steps = steps - accel_steps
    
    cruise_steps = steps - accel_steps - decel_steps
    cruise_delay = int(1_000_000 / max_speed_hz)
    
    print(f"Jerk={jerk}: accel={accel_steps}, cruise={cruise_steps}, decel={decel_steps}")
    
    last_time_us = time.ticks_us()
    
    # === ACCELERATION ===
    for i in range(accel_steps):
        delay_us = get_delay(i, accel_steps, min_speed_hz, max_speed_hz)
        
        output_step(half_step[idx])
        while time.ticks_diff(time.ticks_us(), last_time_us) < delay_us:
            pass
        last_time_us = time.ticks_us()
        
        if direction > 0:
            idx = (idx + 1) % n
        else:
            idx = (idx - 1 + n) % n
    
    # === CRUISE ===
    for _ in range(cruise_steps):
        output_step(half_step[idx])
        while time.ticks_diff(time.ticks_us(), last_time_us) < cruise_delay:
            pass
        last_time_us = time.ticks_us()
        
        if direction > 0:
            idx = (idx + 1) % n
        else:
            idx = (idx - 1 + n) % n
    
    # === DECELERATION (mirror of accel) ===
    for i in range(decel_steps - 1, -1, -1):
        delay_us = get_delay(i, decel_steps, min_speed_hz, max_speed_hz)
        
        output_step(half_step[idx])
        while time.ticks_diff(time.ticks_us(), last_time_us) < delay_us:
            pass
        last_time_us = time.ticks_us()
        
        if direction > 0:
            idx = (idx + 1) % n
        else:
            idx = (idx - 1 + n) % n

def release():
    IN1.value(0)
    IN2.value(0)
    IN3.value(0)
    IN4.value(0)

STEPS_PER_REV = 4096

print("Starting stepper - adjustable jerk S-curve")
max_speed_hz = 500
min_speed_hz = 50
jerk = 1000
n_rev = 2
print('ready')
#time.sleep(5)
while True:
    rotate_smooth(STEPS_PER_REV * n_rev, direction=+1,
                  max_speed_hz=max_speed_hz, min_speed_hz=min_speed_hz, jerk=jerk)
    release()
    time.sleep(5)
    
    rotate_smooth(STEPS_PER_REV * n_rev, direction=-1,
                  max_speed_hz=max_speed_hz, min_speed_hz=min_speed_hz, jerk=jerk)
    release()
    time.sleep(5)
    break
    