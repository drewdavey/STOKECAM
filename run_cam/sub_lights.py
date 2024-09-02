
import sys
import time
from picamera2 import Picamera2
from gpiozero import Button, LED
from signal import pause
from settings import *

# GPIO pin definitions
yellow = LED(16)
red = LED(26)
right_button = Button(18, hold_time=3)  # 
left_button = Button(17, hold_time=3)   # 

def exit_standby():
    red.close()
    yellow.close() # Close the lights
    right_button.close() 
    left_button.close() # Close the buttons
    sys.exit(0)

def standby():
    yellow.on()

    while not (right_button.is_held and left_button.is_held):

        while right_button.is_pressed and not left_button.is_pressed:
            red.on()
        while left_button.is_pressed and not right_button.is_pressed:
            red.on()
        red.off()
        time.sleep(0.2)

    exit_standby()

if __name__ == "__main__":
    standby()