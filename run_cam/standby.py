

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

cam0.start()
cam1.start()

bursting = False

def burst(log):

    global bursting

    log.write(f"Starting burst.\n")
    
    # start_time = time.time()
    
    while right_button.is_pressed:
        cam0.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
        cam1.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
        # time.sleep(interval)
    
    # cam0.close()
    # cam1.close()
    log.write("Stopping burst.\n")
 
    bursting = False

def numFrames(log):
    log.write(f"numFrames.\n")


def exit_standby(log):
    log.write(f"BOTH BUTTONS HELD.\n")
    
    log.close()

    cam0.stop()
    cam1.stop()
    
    right_button.close()
    left_button.close()

    sys.exit()

def standby(log_file):
    log = open(log_file, 'a')
    log.write(f"Entered standby mode.\n")

    while not right_button.is_held and not left_button.is_held:
        right_button.when_pressed = lambda: burst(log)
        left_button.when_pressed = lambda: numFrames(log)

    # right_button.when_held = lambda: exit_standby(log_file)
    # left_button.when_held = lambda: exit_standby(log_file)

    exit_standby(log)
        # global bursting

        # if right_button.is_pressed:
        #     bursting = True
        #     burst(log_file)
        
        # if left_button.is_pressed and not bursting:
        #     numFrames(log_file)

        # if right_button.is_held and left_button.is_held:
        #     exit_standby(log_file)
    # finally:
    #     log = open(log_file, 'a')
    #     log.write(f"I died.\n")
    #     log.close()
    #     right_button.close()
    #     left_button.close()
    #     sys.exit()

if __name__ == "__main__":
    standby(sys.argv[1])