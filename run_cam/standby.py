

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
        # time.sleep(dt) - do watchdog loop
    
    log.write("Stopping burst.\n")
 
    bursting = False

def numFrames(log):
    if not bursting:
        log.write(f"numFrames.\n")


def exit_standby(log):
    log.write(f"BOTH BUTTONS HELD.\n")
    
    log.close()

    cam0.stop()
    cam1.stop()
    
    right_button.close()
    left_button.close()

    sys.exit(0)

def standby(pathLog):
    log = open(pathLog, 'a')
    log.write(f"Entered standby mode.\n")

    while not right_button.is_held and not left_button.is_held:
        # sleep 0.5.... check if both are pressed
        if right_button.is_pressed and not left_button.is_pressed:
            # right_button.when_pressed = lambda: burst(log)
            burst(log)
        if left_button.is_pressed and not right_button.is_pressed:
            # left_button.when_pressed = lambda: numFrames(log)
            numFrames(log)


    exit_standby(log)
        # global bursting

        # if right_button.is_pressed:
        #     bursting = True
        #     burst(pathLog)
        
        # if left_button.is_pressed and not bursting:
        #     numFrames(pathLog)

        # if right_button.is_held and left_button.is_held:
        #     exit_standby(pathLog)
    # finally:
    #     log = open(pathLog, 'a')
    #     log.write(f"I died.\n")
    #     log.close()
    #     right_button.close()
    #     left_button.close()
    #     sys.exit()

if __name__ == "__main__":
    standby(sys.argv[1])