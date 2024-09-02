# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import os
import sys
import time
from picamera2 import Picamera2
from gpiozero import Button, LED
from signal import pause
import subprocess
from settings import *
from datetime import datetime, timezone

# GPIO pin definitions
yellow = LED(16)
red = LED(26)
right_button = Button(18, hold_time=3)  # 
left_button = Button(17, hold_time=3)   # 

config = get_config()

# Connect to the cameras
cam0 = Picamera2(0)
cam1 = Picamera2(1)

busy = False

def configure_cameras(fname_log, config):
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log = open(fname_log, 'a')
    for idx, cam in enumerate([cam0, cam1]):
        cam.configure(config)
        cam.start()
        log.write(f"{tstr}:     cam{idx} configuration: {cam.camera_configuration()}\n")
        log.write(f"{tstr}:     cam{idx} metadata: {cam.capture_metadata()}\n")
    log.close()

def burst(fdir, fname_log, dt): 
    global busy
    i = 0
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'burst')
    imu_process = subprocess.Popen(['python3', 'imu.py', fname_imu, fname_log])
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log.write(f"{tstr}:     burst session: {fdir_out}\n")
    while right_button.is_pressed:
        red.on()
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        i += 1
        red.off()
        time.sleep(dt)
    imu_process.terminate()
    busy = False
    log.close()

def numFrames(fdir, fname_log, dt, num_frames):
    global busy
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'numFrames')
    imu_process = subprocess.Popen(['python3', 'imu.py', fname_imu, fname_log])
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log.write(f"{tstr}:     numFrames session: {fdir_out}\n")
    for i in range(int(num_frames)):
        red.on()
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3] 
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        red.off()
        time.sleep(dt)
    imu_process.terminate()
    busy = False
    log.close()

def create_dirs(fdir, mode):
    session = datetime.now(timezone.utc).strftime('%H%M%S_' + mode)
    fdir_out = os.path.join(fdir, session + '/')
    fdir_cam0 = os.path.join(fdir_out, 'cam0/')
    fdir_cam1 = os.path.join(fdir_out, 'cam1/')
    os.makedirs(fdir_cam0, exist_ok=True)
    os.makedirs(fdir_cam1, exist_ok=True)
    fname_imu = f'{fdir_out}IMU_{session}.txt'
    return fdir_out, fdir_cam0, fdir_cam1, fname_imu

def exit_standby(fname_log):
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Exiting standby.\n\n")
    log.close()
    cam0.stop() 
    cam1.stop() # Close the cameras
    red.close()
    yellow.close() # Close the lights
    right_button.close() 
    left_button.close() # Close the buttons
    sys.exit(0)

def standby(fdir, fname_log, dt, num_frames):
    yellow.on()
    global busy
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log.write(f"{tstr}:     Entering standby...\n\n")
    log.close()
    configure_cameras(fname_log, config)

    while not (right_button.is_held and left_button.is_held):

        if right_button.is_pressed and not left_button.is_pressed and not busy:
            busy = True
            burst(fdir, fname_log, dt)
        if left_button.is_pressed and not right_button.is_pressed and not busy:
            busy = True
            numFrames(fdir, fname_log, dt, num_frames)
        time.sleep(0.2)

    exit_standby(fname_log)

if __name__ == "__main__":
    standby(sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]))