from machine import Pin
from time import sleep
led = Pin("LED", Pin.OUT)  # Pico/Pico 2 maps "LED" to the onboard LED
while True:
    led.toggle()
    sleep(0.5)
