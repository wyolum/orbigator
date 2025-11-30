from machine import Pin
import time

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

def rotate(steps, direction=1, delay_ms=2):
    """
    steps: number of half-steps
    direction: +1 or -1
    """
    idx = 0
    n = len(half_step)

    for _ in range(steps):
        output_step(half_step[idx])
        time.sleep_ms(delay_ms)
        # advance index explicitly
        if direction > 0:
            idx = (idx + 1) % n
        else:
            idx = (idx - 1 + n) % n

def release():
    IN1.value(0)
    IN2.value(0)
    IN3.value(0)
    IN4.value(0)

STEPS_PER_REV = 4096  # typical for 28BYJ-48 in half-step

print("Starting stepper test...")

while True:
    print("Forward (direction=+1) 1 rev...")
    rotate(STEPS_PER_REV, direction=+1, delay_ms=1)
    release()
    time.sleep(2)
    print("Reverse (direction=-1) 1 rev...")
    rotate(STEPS_PER_REV, direction=-1, delay_ms=1)
    release()
    time.sleep(2)
