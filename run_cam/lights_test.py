
from gpiozero import Button, LED
import subprocess
from time import sleep
from subprocess import Popen
from signal import SIGINT



right_button = Button(18, hold_time=3)  
left_button = Button(17, hold_time=3)
# right_button.close()
# left_button.close()
# right_button = Button(18, hold_time=3)  
# left_button = Button(17, hold_time=3)

green = LED(12)

# green.on()

# while True:
#     if (right_button.is_held and left_button.is_held): 
#         right_button.close()
#         left_button.close() 
#         process = subprocess.Popen(['python3', 'sub_lights.py'])
#         process.wait()
#         right_button = Button(18, hold_time=3)  
#         left_button = Button(17, hold_time=3)
#         sleep(1)


# if (right_button.is_held and left_button.is_held): 
#     right_button.close()
#     left_button.close() 
#     process = subprocess.Popen(['python3', 'sub_lights.py'])
#     process.wait()
#     right_button = Button(18, hold_time=3)  
#     left_button = Button(17, hold_time=3)
#     sleep(1)

def start_subprocess():
    global child_process, left_button, right_button
    if child_process is None:
        # Close buttons to free up GPIO pins
        left_button.close()
        right_button.close()
        
        # Start child process
        child_process = Popen(['python', 'sub_lights.py'])
        sleep(0.5)  # Debounce delay

        # Reinitialize buttons after subprocess starts
        left_button = Button(17)
        right_button = Button(18)
        left_button.when_pressed = stop_subprocess
        right_button.when_pressed = start_subprocess

def stop_subprocess():
    global child_process, left_button, right_button
    if child_process is not None:
        child_process.send_signal(SIGINT)
        child_process.wait()

        # Close and reinitialize buttons after subprocess ends
        left_button.close()
        right_button.close()
        left_button = Button(17)
        right_button = Button(18)
        left_button.when_pressed = stop_subprocess
        right_button.when_pressed = start_subprocess
        
        child_process = None
        sleep(0.5)  # Debounce delay

left_button.when_held = start_subprocess
right_button.when_pressed = stop_subprocess

def monitor_condition():
    while True:
        # Placeholder for condition to control green light
        green.on()
        sleep(1)  # Check every second

try:
    monitor_condition()
except KeyboardInterrupt:
    # Everything will clean up itself due to gpiozero's built-in cleanup
    pass
