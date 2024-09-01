# Last updated: 2024-07-08
##################################
# This script is passed IMU filename and IMU dt
# Args: (1)  (2)
##################################

import sys
import time
import psutil

# Import vnpy library
from vnpy import *

# Connect to the VN-200 
ez = EzAsyncData.connect('/dev/ttyUSB0', 115200)
s = ez.sensor                                       # create sensor object for VN-200

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

    imu = open(imu_path, 'a')
    log_out = open(log_path, 'a')
        
    imu.write(imu_headerLine = "Timestamp (UTC: HHMMSSsss), VN-200 Timestamp (UTC), Temperature (deg C), Pressure (Pa), Yaw (deg), Pitch (deg), Roll (deg), Accel_x, Accel_y, Accel_z, Gyro_x, Gyro_y, Gyro_z, Mag_x, Mag_y, Mag_z, GPS_LLA, INS_LLA\n")

    while is_pid_active(cam_pid):

        ####################### IMU #######################
        ypr = s.read_yaw_pitch_roll() # Read yaw, pitch, and roll values
        gps = s.read_gps_solution_lla() # Read the GPS solution in LLA format
        ins = s.read_ins_solution_lla() # Read the INS solution
        imu_out = s.read_imu_measurements() # Read the IMU measurements
        cd = ez.current_data # Read current data as CompositeData class from the EzAsyncData
        imu.write(f"{tstr}, {cd.time_utc}, {cd.temperature} or {imu_out.temp}, {cd.pressure} or {imu_out.pressure}, {ypr.x}, {ypr.y}, {ypr.z}, {imu_out.accel.x}, {imu_out.accel.y}, {imu_out.accel.z}, {imu_out.gyro.x}, {imu_out.gyro.y}, {imu_out.gyro.z}, {imu_out.mag.x}, {imu_out.mag.y}, {imu_out.mag.z}, ({gps.lla.x}, {gps.lla.y}, {gps.lla.z}), ({ins.position.x}, {ins.position.y}, {ins.position.z})" + '\n')
        ###################################################

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