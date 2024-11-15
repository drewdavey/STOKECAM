# Last updated: 2024-06-03
##################################
# This script is passed 
# Args: (1) 
##################################

import sys
import time

# Import vnpy library
from vnpy import *

# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s)
s = VnSensor()
s.connect('/dev/ttyUSB0', 115200)

cd = s.CompositeData()


# Record the start time
start_time = time.time()
duration = 30  # seconds

while time.time() - start_time < duration:
    # Read yaw, pitch, and roll values
    # ypr = s.read_yaw_pitch_roll()
    # print(f"Yaw: {ypr.x}, Pitch: {ypr.y}, Roll: {ypr.z}"+ '\n')

    # gps = s.read_gps_solution_lla() # Read the GPS solution in LLA format

    # reg = s.read_yaw_pitch_roll_magnetic_acceleration_and_angular_rates()
    # print(f"Acc_X: {reg.accel.x}, Acc_Y: {reg.accel.y}, Acc_Z: {reg.accel.z}"+ '\n')

    # print(f" {gps.num_sats}, {gps.time}, ({gps.lla.x}, {gps.lla.y}, {gps.lla.z})" + '\n')

    t = cd.time_utc
    print(f"Time: {t}" + '\n')

    # Pause for a short time to avoid flooding the command window
    time.sleep(0.1)  

# Disconnect from the sensor
s.disconnect()


# s.write_async_data_output_frequency(10)
