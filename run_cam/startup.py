

import os
import sys
import time
import subprocess
from picamera2 import Picamera2
from vnpy import *

# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s)
s = VnSensor()
s.connect('/dev/ttyUSB0', 115200)

# import serial

# # Setup serial for GPS (adjust as necessary)
# gps_serial = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

# Initialize the camera
camera = Picamera2()

def sync_clock_from_gps():
    while True:
        gps_data = gps_serial.readline().decode('ascii', errors='replace')
        if gps_data.startswith('$GPRMC'):
            parts = gps_data.split(',')
            if parts[2] == 'A':  # Check if data is valid
                utc_time = parts[1]
                utc_date = parts[9]
                formatted_time = f"{utc_date[4:6]}-{utc_date[2:4]}-{utc_date[0:2]} {utc_time[0:2]}:{utc_time[2:4]}:{utc_time[4:6]}"
                os.system(f'sudo date -u --set="{formatted_time}"')
                break

def config_cameras():
    log_dir = f"../DATA/{time.strftime('%Y%m%d')}/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, "log.txt")
    return log_file

def setup_logging():
    log_dir = f"../DATA/{time.strftime('%Y%m%d')}/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, "LOG.txt")
    return log_file

def enter_standby(log_file):
    subprocess.Popen(['python3', 'standby.py', log_file])

def main():
    log_file = setup_logging()  # Setup logging
    # config_cameras(log_file)  # Configure cameras
    # sync_clock_from_gps(log_file)  # Sync clock from GPS
    enter_standby(log_file)  # Enter standby mode

if __name__ == "__main__":
    main()