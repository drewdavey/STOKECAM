# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import os
import sys
import time
import yaml
import subprocess
from picamera2 import Picamera2
from vnpy import *

# # Setup serial for GPS (adjust as necessary)
# gps_serial = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

# Initialize the camera
# camera = Picamera2()

def setup_logging():
    fdir = f"../../DATA/{time.strftime('%Y%m%d')}/"
    if not os.path.exists(fdir):
        os.makedirs(fdir)
    pathLog = os.path.join(fdir, f"{time.strftime('%Y%m%d')}_LOG.txt")
    return fdir, pathLog

def apply_camera_settings(camera, settings):
    # Apply the settings to the camera
    camera.configure({
        'mode': settings.get('mode', 'manual'),
        'size': settings.get('resolution', [1920, 1080]),
        'controls': {
            'ExposureTime': settings.get('exposure_time', 10000),
            'AnalogueGain': settings.get('iso', 100),
            'FrameRate': settings.get('framerate', 30),
            'Brightness': settings.get('brightness', 50),
            'Contrast': settings.get('contrast', 0),
            'Saturation': settings.get('saturation', 0),
            'AwbMode': settings.get('awb_mode', 'auto'),
        }
    })
    camera.start()

def configure_cameras():
    # Load the configuration
    config_file='../config.yaml'
    # Load the YAML configuration file
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)

    # Initialize both cameras
    cam0 = Picamera2(camera_num=0)
    cam1 = Picamera2(camera_num=1)

    # Apply settings to both cameras
    apply_camera_settings(cam0, config['camera_0'])
    apply_camera_settings(cam1, config['camera_1'])

    # Save the configuration to both cameras (if needed)
    cam0.capture_file('camera0_settings.json')
    cam1.capture_file('camera1_settings.json') # what? <---

    # close cams? do they even need to open?

    return cam0, cam1 #?

def sync_clock():
    # Create sensor object and connect to the VN-200 
    # at the baud rate of 115200 (115,200 bytes/s)
    s = VnSensor()
    s.connect('/dev/ttyUSB0', 115200)
    # while True:
    #     gps_data = gps_serial.readline().decode('ascii', errors='replace')
    #     if gps_data.startswith('$GPRMC'):
    #         parts = gps_data.split(',')
    #         if parts[2] == 'A':  # Check if data is valid
    #             utc_time = parts[1]
    #             utc_date = parts[9]
    #             formatted_time = f"{utc_date[4:6]}-{utc_date[2:4]}-{utc_date[0:2]} {utc_time[0:2]}:{utc_time[2:4]}:{utc_time[4:6]}"
    #             os.system(f'sudo date -u --set="{formatted_time}"')
    #             break

def enter_standby(fdir, pathLog):
    with open(pathLog, 'a') as log:
        log.write(f"Startup complete - created log for today blah blah.\n")
    subprocess.Popen(['python3', 'standby.py', fdir, pathLog])

def startup():
    fdir, pathLog = setup_logging()  # Setup logging
    cam0, cam1 = configure_cameras()
    # sync_clock(pathLog)  # Sync clock from GPS
    # dt = 0
    # num_frames = 10
    enter_standby(fdir, pathLog)  # Enter standby mode

if __name__ == "__main__":
    startup()