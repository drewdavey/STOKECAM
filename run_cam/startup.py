# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import os
import time
import datetime
import subprocess
from vnpy import *

def setup_logging():
    fdir = f"../../DATA/{datetime.strftime('%Y%m%d')}/"
    if not os.path.exists(fdir):
        os.makedirs(fdir)
    pathLog = os.path.join(fdir, f"{datetime.strftime('%Y%m%d')}_LOG.txt")
    return fdir, pathLog

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
    # log = open(pathLog, 'a')
    # sync_clock(pathLog)  # Sync clock from GPS
    # dt = 0
    # num_frames = 10
    enter_standby(fdir, pathLog)  # Enter standby mode

if __name__ == "__main__":
    startup()