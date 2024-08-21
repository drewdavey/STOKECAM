

import os
import sys
import time
import subprocess
from picamera2 import Picamera2
from gpiozero import Button
from signal import pause

# GPIO pin definitions
right_button = Button(18, hold_time=3)  # 
left_button = Button(17, hold_time=3)   # 

cam0 = Picamera2(0)
cam1 = Picamera2(1)

bursting = False

def burst(log_file):

    global bursting

    log = open(log_file, 'a')
    log.write(f"Starting burst.\n")
    
    cam0.start()
    cam1.start()
    # start_time = time.time()
    
    while right_button.is_pressed:
        cam0.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
        cam1.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
        # time.sleep(interval)
    
    cam0.stop()
    cam1.stop()
    # cam0.close()
    # cam1.close()
    log.write("Stopping burst.\n")
    log.close()

    bursting = False

def numFrames(log_file):
    if not bursting:
        log = open(log_file, 'a')
        log.write(f"Entered numFrames mode.\n")
        log.close()

def exit_standby(log_file):
    log = open(log_file, 'a')
    log.write(f"BOTH BUTTONS HELD.\n")
    log.close()
    right_button.close()
    left_button.close()
    sys.exit(0)

def standby(log_file):
    # right_button = Button(18, hold_time=3) 
    # left_button = Button(17, hold_time=3)

    log = open(log_file, 'a')
    log.write(f"Entered standby mode.\n")
    log.close()

    # while True:
    #     if left_button.is_held and right_button.is_held:
            # right_button.close()
            
        # right_button.when_held = start_burst_mode(log_file)
        # elif left_button.is_held and right_button.is_held:
        #     # start_calibration_mode(log_file)
        # elif left_button.is_held:

    global bursting

    while True:
        if right_button.is_pressed and not bursting:
            bursting = True
            burst(log_file)
        
        if left_button.is_pressed:
            numFrames(log_file)

        if right_button.is_held and left_button.is_held:
            exit_standby(log_file)
            
    # right_button.when_pressed = burst(log_file)
    # left_button.when_pressed = numFrames(log_file)

    # if left_button.is_held and right_button.is_held:
    #     exit_standby(log_file)

    # # Keep the script running to listen for button events
    # pause()

if __name__ == "__main__":
    standby(sys.argv[1])