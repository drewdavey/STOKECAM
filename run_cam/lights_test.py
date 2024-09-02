
from picamera2 import Picamera2
from gpiozero import Button, LED
from signal import pause
import subprocess
from settings import *
from datetime import datetime, timezone
from time import sleep
import os
os.environ['GPIOZERO_PIN_FACTORY'] = os.environ.get('GPIOZERO_PIN_FACTORY', 'mock')

green = LED(12)

# LED(12).close()

# right_button = Button(18, hold_time=3)  # 
# left_button = Button(17, hold_time=3)   # 

# while not (right_button.is_held and left_button.is_held):
#     green.on()
# green.off()
green.on()

process = subprocess.Popen(['python3', 'sub_lights.py'])
    
while not process.poll() is None:  # Check if standby.py is still running
    right_button = Button(18, hold_time=5) 
    left_button = Button(17, hold_time=5)
    if (right_button.is_held and left_button.is_held):
        green.close()
        right_button.close()
        left_button.close()
        exit()