
import sys
import time
import signal
from vnpy import *
from datetime import datetime, timezone

imu_dt = 0 # get from yaml
imu_headerLine = "Timestamp (UTC: HHMMSSsss), VN-200 Timestamp (UTC), Temperature (deg C), Pressure (Pa), Yaw (deg), Pitch (deg), Roll (deg), Accel_x, Accel_y, Accel_z, Gyro_x, Gyro_y, Gyro_z, Mag_x, Mag_y, Mag_z, GPS_LLA, INS_LLA\n"

# Connect to the VN-200 
ez = EzAsyncData.connect('/dev/ttyUSB0', 115200)
s = ez.sensor

running = True

def imu_run(fname_imu,fname_log):
    global running
    imu = open(fname_imu, 'a')
    log = open(fname_log, 'a')
    log.write(f"STARTING IMU.\n")
    imu.write(imu_headerLine)
    while running:
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
        ypr = s.read_yaw_pitch_roll() # Read yaw, pitch, and roll values
        gps = s.read_gps_solution_lla() # Read the GPS solution in LLA format
        ins = s.read_ins_solution_lla() # Read the INS solution
        imu_out = s.read_imu_measurements() # Read the IMU measurements
        cd = ez.current_data # Read current data as CompositeData class from the EzAsyncData
        imu.write(f"{tstr}, {cd.time_utc}, {cd.temperature} or {imu_out.temp}, {cd.pressure} or {imu_out.pressure}, {ypr.x}, {ypr.y}, {ypr.z}, {imu_out.accel.x}, {imu_out.accel.y}, {imu_out.accel.z}, {imu_out.gyro.x}, {imu_out.gyro.y}, {imu_out.gyro.z}, {imu_out.mag.x}, {imu_out.mag.y}, {imu_out.mag.z}, ({gps.lla.x}, {gps.lla.y}, {gps.lla.z}), ({ins.position.x}, {ins.position.y}, {ins.position.z})" + '\n')
        time.sleep(imu_dt)
    imu.write('STOPPING IMU' + '\n')
    imu.close()
    s.disconnect()
    sys.exit(0)

# Signal handler function
def imu_disconnect():
    global running
    running = False  # Set the flag to False to stop the loop

# Set up signal handling
signal.signal(signal.SIGTERM, imu_disconnect)
signal.signal(signal.SIGINT, imu_disconnect)

if __name__ == '__main__':
    imu_run(sys.argv[1],sys.argv[2])
