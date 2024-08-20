

import os
import sys
import time
import subprocess
from gpiozero import Button

# GPIO pin definitions
right_button = Button(18, hold_time=3)  # Replace with your GPIO pin number
left_button = Button(17, hold_time=3)   # Replace with your GPIO pin number

def release_buttons():
    right_button.close()
    left_button.close()

def standby_mode(log_file):
    with open(log_file, 'a') as log:
        log.write(f"Entered stanby mode.\n")
    while True:
        if right_button.is_held:
            start_burst_mode(log_file)
        elif left_button.is_held and right_button.is_held:
            start_calibration_mode(log_file)
        elif left_button.is_held:
            stop_current_mode()
        time.sleep(0.1)  # Debounce delay

def start_burst_mode(log_file):
    release_buttons()
    subprocess.Popen(['python3', 'burst.py', log_file])

def start_calibration_mode(log_file):
    release_buttons()
    subprocess.Popen(['python3', 'calib.py', log_file])

def stop_current_mode():
    release_buttons()
    subprocess.run(['pkill', '-f', 'burst.py'])
    subprocess.run(['pkill', '-f', 'calib.py'])

def main(log_file):
    standby_mode(log_file)  # Enter standby mode

if __name__ == "__main__":
    main(sys.argv[1])