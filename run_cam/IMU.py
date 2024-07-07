# Last updated: 2024-06-06
##################################
# This script is passed IMU filename and IMU dt
# Args: (1)  (2)
##################################

import sys
import time
import psutil

# Import vnpy library
from vnpy import *

# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s)
s = VnSensor()
s.connect('/dev/ttyUSB0', 115200)


# Record the start time
# start_time = time.time()
# duration = 30  # seconds

def is_pid_active(pid):
    """Check if a process with the given PID is still running."""
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False
    
def run_imu(log_path,imu_path,imu_dt,cam_pid):

    imu_out = open(imu_path, 'a')
    log_out = open(log_path, 'a')
        
    imu_out.write(str('Time(UTC),Heading(deg, magN),Yaw(deg),Roll(deg),Pitch(deg)') + '\n')

    while is_pid_active(cam_pid):

        # Read yaw, pitch, and roll values
        ypr = s.read_yaw_pitch_roll()
        
        # Print the yaw, pitch, and roll values
        imu_out.write(f"Yaw: {ypr.x}, Pitch: {ypr.y}, Roll: {ypr.z}" + '\n')
        
        reg = s.read_yaw_pitch_roll_magnetic_acceleration_and_angular_rates()
        imu_out.write(f"Acc_X: {reg.accel.x}, Acc_Y: {reg.accel.y}, Acc_Z: {reg.accel.z}" + '\n')

        # Pause for imu_dt seconds
        time.sleep(imu_dt)  

    # Disconnect from the sensor
    s.disconnect()

    log_out.write('Stopping IMU cleanly' + '\n')
    log_out.close()

    imu_out.close()

    # s.write_async_data_output_frequency(10)

if __name__ == '__main__':
    run_imu(sys.argv[1],sys.argv[2],float(sys.argv[3]),int(sys.argv[4]))