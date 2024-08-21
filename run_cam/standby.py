# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import os
import sys
import time
import subprocess
from picamera2 import Picamera2
from gpiozero import Button
from signal import pause
from time import strftime, datetime

# GPIO pin definitions
right_button = Button(18, hold_time=3)  # 
left_button = Button(17, hold_time=3)   # 

cam0 = Picamera2(0)
cam1 = Picamera2(1)

cam0.start()
cam1.start()

busy = False

def burst(fdir, log, dt):
    global busy
    fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'burst')
    log.write(f"Created directories and log files.\n")
    log.write(f"Starting burst.\n")
    
    # start_time = time.time()
    
    while right_button.is_pressed:
        cam0.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
        cam1.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
        timestamp = datetime.utcnow()
        tstr = timestamp.strftime('%H%M%S%f')[:-3]
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        i += 1
        time.sleep(dt)
    
    log.write("Stopping burst.\n")
 
    busy = False

def numFrames(fdir, log, dt, num_frames):
    global busy
    fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'numFrames')
    log.write(f"numFrames.\n")
    for i in range(int(num_frames)):
        timestamp = datetime.utcnow()
        tstr = timestamp.strftime('%H%M%S%f')[:-3] 
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        time.sleep(dt)
    busy = False

def create_dirs(fdir, mode):
    session = strftime('%H%M%S_' + mode)
    fdir_out = os.path.join(fdir, session + '/')
    fdir_cam0 = os.path.join(fdir_out, 'cam0/')
    fdir_cam1 = os.path.join(fdir_out, 'cam1/')

    os.makedirs(fdir_cam0, exist_ok=True)
    os.makedirs(fdir_cam1, exist_ok=True)

    fname_log = f'{fdir_out}LOG_{session}.txt'
    fname_imu = f'{fdir_out}IMU_{session}.txt'

    print(f'--Created output folders: {fdir_cam0} and {fdir_cam1}')
    return fdir_cam0, fdir_cam1, fname_log, fname_imu

def exit_standby(log):
    log.write(f"EXITING STANDBY.\n")
    
    log.close()

    cam0.stop()
    cam1.stop()
    
    right_button.close()
    left_button.close()

    sys.exit(0)

def standby(fdir, pathLog, dt, num_frames):
    global busy
    log = open(pathLog, 'a')
    log.write(f"Entered standby mode.\n")

    while not right_button.is_held and not left_button.is_held:
        # sleep 0.5.... check if both are pressed
        if right_button.is_pressed and not left_button.is_pressed and not busy:
            # right_button.when_pressed = lambda: burst(log)
            busy = True
            burst(fdir, log, dt)

        if left_button.is_pressed and not right_button.is_pressed and not busy:
            # left_button.when_pressed = lambda: numFrames(log)
            busy = True
            numFrames(fdir, log, dt, num_frames)


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
    standby(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))