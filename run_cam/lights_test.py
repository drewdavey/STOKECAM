
from gpiozero import Button, LED
import subprocess
from time import sleep

right_button = Button(18, hold_time=3)  
left_button = Button(17, hold_time=3)

green = LED(12)

green.on()

while True:
    if (right_button.is_held and left_button.is_held): 
        right_button.close()
        left_button.close() 
        process = subprocess.Popen(['python3', 'sub_lights.py'])
        process.wait()
        right_button = Button(18, hold_time=3)  
        left_button = Button(17, hold_time=3)
        sleep(1)