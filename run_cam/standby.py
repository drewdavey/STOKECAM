# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import sys
import time
import subprocess
from utils import *
from settings import *
from signal import pause
from picamera2 import Picamera2
from gpiozero import Button, LED
from datetime import datetime, timezone

# GPIO pin definitions
green = LED(12)
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

def monitor_gps():
    global busy
    if not busy:
        ez = EzAsyncData.connect('/dev/ttyUSB0', 115200) 
        s = ez.sensor
        # green.blink(0.5, 0.5)
        if ez.current_data.has_any_position:                              
            if ez.current_data.position_uncertainty_estimated > 10:
                green.blink(0.5, 0.5)
            elif ez.current_data.position_uncertainty_estimated <= 10:
                green.on()
        else:
            green.off() 
        s.disconnect()

def exit_standby(fname_log):
    global standby
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Exiting standby.\n\n")
    log.close()
    yellow.off() # Close the lights
    red.off()
    time.sleep(0.5)
    standby = False

def enter_standby(fdir, fname_log, dt, num_frames):
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

fdir, fname_log = setup_logging()               # Setup logging

inputs = read_inputs_yaml(fname_log)            # Read inputs from inputs.yaml
num_frames = inputs['num_frames']
dt = inputs['dt']

gps_wait_time = inputs['gps_wait_time']
sync_clock_and_imu(fname_log, gps_wait_time)        # Connect to VecNav and sync clock

global standby
standby = False

while not (right_button.is_held and left_button.is_held):
    monitor_gps()
    if right_button.is_held and not standby and not left_button.is_pressed:
        standby = True
        enter_standby(fdir, fname_log, dt, num_frames)    # Enter standby mode
    if left_button.is_held and not standby and left_button.held_time > 5 and not right_button.is_pressed:
        cam0.close()
        cam1.close()
        process = subprocess.Popen(['python3', 'calib.py'])
        process.wait()
        cam0 = Picamera2(0)
        cam1 = Picamera2(1)
    time.sleep(0.2)

cam0.stop() 
cam1.stop() # Close the cameras
cam0.close()
cam1.close()
green.close()
yellow.close()
red.close() 
right_button.close() 
left_button.close() # Close the buttons
sys.exit(0)