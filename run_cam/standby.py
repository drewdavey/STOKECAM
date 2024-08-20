

import os
import sys
import time
import subprocess
from gpiozero import Button

# GPIO pin definitions
right_button = Button(17)  # Replace with your GPIO pin number
left_button = Button(27)   # Replace with your GPIO pin number

def standby_mode(log_file):
    with open(log_file, 'a') as log:
        log.write(f"Entering stanby mode.\n")
    while True:
        if right_button.is_held:
            start_burst_mode(log_file)
        elif left_button.is_held and right_button.is_held:
            start_calibration_mode(log_file)
        elif left_button.is_held:
            stop_current_mode()
        time.sleep(0.1)  # Debounce delay

def start_burst_mode(log_file):
    subprocess.Popen(['python3', 'burst.py', log_file])

def start_calibration_mode(log_file):
    subprocess.Popen(['python3', 'calib.py', log_file])

def stop_current_mode():
    subprocess.run(['pkill', '-f', 'burst.py'])
    subprocess.run(['pkill', '-f', 'calib.py'])

def main(log_file):
    standby_mode(log_file)  # Enter standby mode

if __name__ == "__main__":
    main(sys.argv[1])