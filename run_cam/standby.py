# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import os
import sys
import time
import subprocess
import yaml
from picamera2 import Picamera2
from gpiozero import Button
from signal import pause
from vnpy import *

# Connect to the VN-200 
s = VnSensor()
s.connect('/dev/ttyUSB0', 115200)

# GPIO pin definitions
right_button = Button(18, hold_time=3)  # 
left_button = Button(17, hold_time=3)   # 

# Connect to the cameras
# cam0 = Picamera2(0)
# cam1 = Picamera2(1)
# cam0.start()
# cam1.start()

def configure_cameras(log):

    cam0 = Picamera2(0)
    cam1 = Picamera2(1)

    # Load the configuration
    config_file='../config.yaml'
    # Load the YAML configuration file
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)['camera_settings']

    # # Define the transform using the settings from the YAML file
    # transform = Transform(hflip=config['transform'].get('hflip', False),
    #                       vflip=config['transform'].get('vflip', False))

    # # Define the color space
    # color_space = ColorSpace.Srgb() if config.get('color_space', 'sRGB') == 'sRGB' else ColorSpace.Adobe()

    # Apply settings to both cameras
    for cam in [cam0, cam1]:
        camera_config = cam.create_still_configuration(
            main={"size": config['resolution'], "format": "RGB888"},
            # transform=transform,
            # colour_space=color_space
        )
        cam.configure(camera_config)
        cam.set_controls({
            'ExposureTime': int(config['exposure_time']),
            'AnalogueGain': float(config['iso']),
            'FrameRate': int(config['framerate']),
            'Brightness': float(config['brightness']),
            'Contrast': float(config['contrast']),
            'Saturation': float(config['saturation']),
            'AwbMode': config['awb_mode']
        })
        cam.start()
        log.write(f"Camera configuration: {cam.camera_configuration()}\n")
        #### pull each camera config and print to log ################'
        #After configuring the camera, it’s often helpful to inspect picam2.camera_configuration() to check 


busy = False

def burst(fdir, log, dt): 
    global busy
    i = 0
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'burst')
    imu = open(fname_imu, 'a')
    log.write(f"burst session: {fdir_out}\n")
    while right_button.is_pressed:
        tstr = time.strftime('%H%M%S%f')[:-3]
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        ypr = s.read_yaw_pitch_roll() # Read yaw, pitch, and roll values
        imu.write(f"{tstr}: Yaw: {ypr.x}, Pitch: {ypr.y}, Roll: {ypr.z}" + '\n') # Print the yaw, pitch, and roll values
        i += 1
        time.sleep(dt)
    imu.close()
    busy = False

def numFrames(fdir, log, dt, num_frames):
    global busy
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'numFrames')
    imu = open(fname_imu, 'a')
    log.write(f"numFrames session: {fdir_out}\n")
    for i in range(int(num_frames)):
        tstr = time.strftime('%H%M%S%f')[:-3] 
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        ypr = s.read_yaw_pitch_roll() # Read yaw, pitch, and roll values
        imu.write(f"{tstr}: Yaw: {ypr.x}, Pitch: {ypr.y}, Roll: {ypr.z}" + '\n') # Print the yaw, pitch, and roll values
        time.sleep(dt)
    imu.close()
    busy = False

def create_dirs(fdir, mode):
    session = time.strftime('%H%M%S_' + mode)
    fdir_out = os.path.join(fdir, session + '/')
    fdir_cam0 = os.path.join(fdir_out, 'cam0/')
    fdir_cam1 = os.path.join(fdir_out, 'cam1/')
    os.makedirs(fdir_cam0, exist_ok=True)
    os.makedirs(fdir_cam1, exist_ok=True)
    fname_imu = f'{fdir_out}IMU_{session}.txt'
    print(f'--Created output folders: {fdir_cam0} and {fdir_cam1}')
    return fdir_out, fdir_cam0, fdir_cam1, fname_imu

def exit_standby(log):
    log.write(f"EXITING STANDBY.\n")
    log.close()
    s.disconnect() # Disconnect from the VN-200
    cam0.stop() 
    cam1.stop() # Close the cameras
    right_button.close() 
    left_button.close() # Close the buttons
    sys.exit(0)

def standby(fdir, pathLog, dt, num_frames):
    global busy
    log = open(pathLog, 'a')
    log.write(f"Entered standby mode.\n")
    configure_cameras(log)

    while not (right_button.is_held and left_button.is_held):
        # left_button.when_pressed = lambda: numFrames(log)
        # right_button.when_pressed = lambda: burst(log)
        if right_button.is_pressed and not left_button.is_pressed and not busy:
            busy = True
            burst(fdir, log, dt)
        if left_button.is_pressed and not right_button.is_pressed and not busy:
            busy = True
            numFrames(fdir, log, dt, num_frames)

    exit_standby(log)

if __name__ == "__main__":
    standby(sys.argv[1], sys.argv[2], 0, 10)