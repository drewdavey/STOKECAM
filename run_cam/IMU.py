# Last updated: 2024-06-06
##################################
# This script is passed IMU filename and IMU dt
# Args: (1)  (2)
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
# start_time = time.time()
# duration = 30  # seconds

def run_imu(path,imu_dt):

    outfile = open(path, 'a')
        
    outfile.write(str('Time(UTC),Heading(deg, magN),Yaw(deg),Roll(deg),Pitch(deg)') + '\n')

    while time.time() - start_time < duration:

        # Read yaw, pitch, and roll values
        ypr = s.read_yaw_pitch_roll()
        
        # Print the yaw, pitch, and roll values
        outfile.write(f"Yaw: {ypr.x}, Pitch: {ypr.y}, Roll: {ypr.z}" + '\n')
        
        reg = s.read_yaw_pitch_roll_magnetic_acceleration_and_angular_rates()
        outfile.write(f"Acc_X: {reg.accel.x}, Acc_Y: {reg.accel.y}, Acc_Z: {reg.accel.z}" + '\n')

        # Pause for imu_dt seconds
        time.sleep(imu_dt)  

    # Disconnect from the sensor
    s.disconnect()

    outfile.close()

    # s.write_async_data_output_frequency(10)

if __name__ == '__main__':
    run_imu(sys.argv[1],int(sys.argv[2]))