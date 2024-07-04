# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import sys
import time

# Import vnpy library
from vnpy import *

# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s)
s = VnSensor()
s.connect('/dev/ttyUSB0', 115200)


# Record the start time
start_time = time.time()
duration = 30  # seconds

while time.time() - start_time < duration:
    # Read yaw, pitch, and roll values
    ypr = s.read_yaw_pitch_roll()
    
    # Print the yaw, pitch, and roll values
    print(f"Yaw: {ypr.x}, Pitch: {ypr.y}, Roll: {ypr.z}")
    
    reg = s.read_yaw_pitch_roll_magnetic_acceleration_and_angular_rates()
    print(reg)
    
    # Pause for a short time to avoid flooding the command window
    time.sleep(0.01)  # Adjust as needed based on the desired update rate

# Disconnect from the sensor
s.disconnect()


# s.write_async_data_output_frequency(10)
