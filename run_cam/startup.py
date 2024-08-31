# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import os
import time
import yaml
import subprocess
from vnpy import *
from datetime import datetime, timezone

def setup_logging():
    fdir = f"../../DATA/{datetime.now(timezone.utc).strftime('%Y%m%d')}/"
    if not os.path.exists(fdir):
        os.makedirs(fdir)
    pathLog = os.path.join(fdir, f"{datetime.now(timezone.utc).strftime('%Y%m%d')}_LOG.txt")
    #if empty, write header
    return fdir, pathLog

def read_inputs_yaml(pathLog):
    inputs_path = '../inputs.yaml'
    with open(pathLog, 'a') as log:
        try:
            with open(inputs_path, 'r') as file:
                inputs = yaml.safe_load(file)
                log.write(f"Reading inputs...\n")
            return inputs
        except FileNotFoundError:
            log.write(f"Error: The file {inputs_path} was not found.")
            return None
        except yaml.YAMLError as exc:
            log.write(f"Error parsing YAML file: {exc}")
            return None
    
def sync_clock_and_imu(pathLog):
    # Create sensor object and connect to the VN-200 
    # at the baud rate of 115200 (115,200 bytes/s) 
    s = VnSensor()
    s.connect('/dev/ttyUSB0', 115200)

    with open(pathLog, 'a') as log:
        model_num = s.read_model_number()
        serial_num = s.read_serial_number()
        log.write(f"Connected to VN-200: Model {model_num}, Serial: {serial_num}\n")

        time_utc = CompositeData.time_utc
        log.write(f"Time from VN-200: {time_utc.fget}\n")

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

def enter_standby(fdir, pathLog, dt, num_frames):
    with open(pathLog, 'a') as log:
        log.write(f"Startup complete - created log for today blah blah.\n")
    subprocess.Popen(['python3', 'standby.py', fdir, pathLog, str(dt), str(num_frames)])

def startup():
    fdir, pathLog = setup_logging()               # Setup logging
    inputs = read_inputs_yaml(pathLog)            # Read inputs from inputs.yaml
    num_frames = inputs['num_frames']
    dt = inputs['dt']
    calib_on_boot = inputs['calib_on_boot']
    launch_standby = inputs['launch_standby']
    mode = inputs['shooting_mode'] # pass to settings.py

    sync_clock_and_imu(pathLog)                    # Connect to VecNav and sync clock

    if calib_on_boot:
        subprocess.Popen(['python3', 'calib.py', fdir, pathLog, num_frames, dt]) # path0,path1,pathLog,calib_frames,dt

    if launch_standby:
        enter_standby(fdir, pathLog, dt, num_frames)    # Enter standby mode

if __name__ == "__main__":
    startup()