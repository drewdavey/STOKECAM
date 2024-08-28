# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import os
import time
import yaml
import subprocess
from picamera2 import Picamera2
from vnpy import *

def setup_logging():
    fdir = f"../../DATA/{time.strftime('%Y%m%d')}/"
    if not os.path.exists(fdir):
        os.makedirs(fdir)
    pathLog = os.path.join(fdir, f"{time.strftime('%Y%m%d')}_LOG.txt")
    return fdir, pathLog

def configure_cameras(log):
    cam0 = Picamera2(0)
    cam1 = Picamera2(1)

    # Load the configuration
    config_file='../config.yaml'
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)['camera_settings']

    # Apply minimal settings to both cameras
    for cam in [cam0, cam1]:
        print(config)
        camera_config = cam.create_still_configuration(still=config)
        cam.configure(camera_config)

        cam.start()
        log.write(f"Minimal Camera configuration: {cam.camera_configuration()}\n")


#         #### pull each camera config and print to log ################'
#         #After configuring the camera, it’s often helpful to inspect picam2.camera_configuration() to check 

# from picamera2 import Picamera2
# picam2 = Picamera2()
# picam2.configure(picam2.create_preview_configuration())
# picam2.set_controls({"ExposureTime": 10000, "AnalogueGain": 1.0})
# picam2.start()

# from picamera2 import Picamera2
# picam2 = Picamera2()
# config = picam2.create_preview_configuration()
# picam2.configure(config)
# picam2.start()

######################################################################################
    # def configure_cameras(log):
    # cam0 = Picamera2(0)
    # cam1 = Picamera2(1)

    # # Load the configuration
    # config_file='../config.yaml'
    # with open(config_file, 'r') as file:
    #     config = yaml.safe_load(file)['camera_settings']

    # # Apply settings to both cameras
    # for cam in [cam0, cam1]:
    #     camera_config = cam.create_still_configuration(
    #         main={"size": config['resolution'], "format": "RGB888"},
    #     )
    #     cam.configure(camera_config)

    #     controls = {
    #         'ExposureTime': int(config['exposure_time']),
    #         'AnalogueGain': float(config['iso']),
    #         'FrameRate': int(config['framerate']),
    #         'Brightness': float(config['brightness']),
    #         'Contrast': float(config['contrast']),
    #         'Saturation': float(config['saturation']),
    #         'AwbMode': config['awb_mode']
    #     }

    #     # Debugging output
    #     print("Controls being set:")
    #     for key, value in controls.items():
    #         print(f"{key}: {value} (type: {type(value)})")

    #     cam.set_controls(controls)
    #     cam.start()
    #     log.write(f"Camera configuration: {cam.camera_configuration()}\n")

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
    log = open(pathLog, 'a')
    configure_cameras(log)
    # sync_clock(pathLog)  # Sync clock from GPS
    # dt = 0
    # num_frames = 10
    enter_standby(fdir, pathLog)  # Enter standby mode

if __name__ == "__main__":
    startup()