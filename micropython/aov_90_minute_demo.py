from machine import Pin
import time
import math
import _thread

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

STEPS_PER_REV = 4096

def output_step(seq):
    IN1.value(seq[0])
    IN2.value(seq[1])
    IN3.value(seq[2])
    IN4.value(seq[3])

def release():
    IN1.value(0)
    IN2.value(0)
    IN3.value(0)
    IN4.value(0)

def get_delay(step_in_phase, phase_steps, v_start, v_end):
    p = (step_in_phase + 0.5) / phase_steps
    blend = p * p * (3.0 - 2.0 * p)
    v = v_start + (v_end - v_start) * blend
    return int(1_000_000 / v)

def rotate_smooth(steps, direction=1, max_speed_hz=500, min_speed_hz=50, jerk=1000):
    """Fast rotation with S-curve acceleration."""
    if steps == 0:
        return
    
    idx = 0
    n = len(half_step)
    
    delta_v = max_speed_hz - min_speed_hz
    accel_steps = int((min_speed_hz + max_speed_hz) * math.sqrt(delta_v / jerk))
    accel_steps = max(accel_steps, 10)
    decel_steps = accel_steps
    
    if accel_steps + decel_steps > steps:
        accel_steps = steps // 2
        decel_steps = steps - accel_steps
    
    cruise_steps = steps - accel_steps - decel_steps
    cruise_delay = int(1_000_000 / max_speed_hz)
    
    last_time_us = time.ticks_us()
    
    for i in range(accel_steps):
        delay_us = get_delay(i, accel_steps, min_speed_hz, max_speed_hz)
        output_step(half_step[idx])
        while time.ticks_diff(time.ticks_us(), last_time_us) < delay_us:
            pass
        last_time_us = time.ticks_us()
        idx = (idx + direction) % n
    
    for _ in range(cruise_steps):
        output_step(half_step[idx])
        while time.ticks_diff(time.ticks_us(), last_time_us) < cruise_delay:
            pass
        last_time_us = time.ticks_us()
        idx = (idx + direction) % n
    
    for i in range(decel_steps - 1, -1, -1):
        delay_us = get_delay(i, decel_steps, min_speed_hz, max_speed_hz)
        output_step(half_step[idx])
        while time.ticks_diff(time.ticks_us(), last_time_us) < delay_us:
            pass
        last_time_us = time.ticks_us()
        idx = (idx + direction) % n


def motor_thread(minutes_per_rev, direction):
    """Runs on core 1 — fast spin then slow continuous rotation."""
    delay_ms = int((minutes_per_rev * 60 * 1000) / STEPS_PER_REV)
    idx = 0
    n = len(half_step)
    
    # Then slow continuous
    print(f"[Thread] Slow rotation: 1 rev per {minutes_per_rev} min ({delay_ms} ms/step)")
    while True:
        output_step(half_step[idx])
        time.sleep_ms(delay_ms)
        idx = (idx + direction) % n


# === MAIN ===
# Fast rotation first
print("[Thread] Fast rotation: 1 rev")
rotate_smooth(int(STEPS_PER_REV), direction=-1)
print("Starting motor thread on core 1")
_thread.start_new_thread(motor_thread, (90, -1))

# Main loop on core 0
counter = 0
while True:
    time.sleep(60)
    counter += 1
    print(f"[Main] Still going... ({counter * 60} seconds elapsed)")