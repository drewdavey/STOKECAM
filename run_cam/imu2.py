

import time
import psutil
from vnpy import *
from datetime import datetime, timezone

# Connect to the VN-200 
ez = EzAsyncData.connect('/dev/ttyUSB0', 115200)
s = ez.sensor                                       # create sensor object for VN-200

imu_headerLine = "Timestamp (UTC: HHMMSSsss), VN-200 Timestamp (UTC), Temperature (deg C), Pressure (Pa), Yaw (deg), Pitch (deg), Roll (deg), Accel_x, Accel_y, Accel_z, Gyro_x, Gyro_y, Gyro_z, Mag_x, Mag_y, Mag_z, GPS_LLA, INS_LLA\n"

def write_imu(log_path,imu_path,imu_dt,cam_pid):

    imu = open(imu_path, 'a')
    log_out = open(log_path, 'a')
    imu.write(imu_headerLine)

    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    ####################### IMU #######################
    ypr = s.read_yaw_pitch_roll() # Read yaw, pitch, and roll values
    gps = s.read_gps_solution_lla() # Read the GPS solution in LLA format
    ins = s.read_ins_solution_lla() # Read the INS solution
    imu_out = s.read_imu_measurements() # Read the IMU measurements
    cd = ez.current_data # Read current data as CompositeData class from the EzAsyncData
    imu.write(f"{tstr}, {cd.time_utc}, {cd.temperature} or {imu_out.temp}, {cd.pressure} or {imu_out.pressure}, {ypr.x}, {ypr.y}, {ypr.z}, {imu_out.accel.x}, {imu_out.accel.y}, {imu_out.accel.z}, {imu_out.gyro.x}, {imu_out.gyro.y}, {imu_out.gyro.z}, {imu_out.mag.x}, {imu_out.mag.y}, {imu_out.mag.z}, ({gps.lla.x}, {gps.lla.y}, {gps.lla.z}), ({ins.position.x}, {ins.position.y}, {ins.position.z})" + '\n')
    ###################################################

    # Disconnect from the sensor
    s.disconnect()

    log_out.write('Stopping IMU cleanly' + '\n')
    log_out.close()
    imu.close()
