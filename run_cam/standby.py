# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import os
import sys
import time
from picamera2 import Picamera2
from gpiozero import Button
from signal import pause
from vnpy import *
from settings import *
from datetime import datetime, timezone

# Connect to the VN-200 
s = VnSensor()
s.connect('/dev/ttyUSB0', 115200)
ez = EzAsyncData()

# GPIO pin definitions
right_button = Button(18, hold_time=3)  # 
left_button = Button(17, hold_time=3)   # 

config = get_still_configuration() # get still config from settings.py. add statement here to choose mode

# Connect to the cameras
cam0 = Picamera2(0)
cam1 = Picamera2(1)

busy = False

def configure_cameras(log):
    for idx, cam in enumerate([cam0, cam1]):
        cam.configure(config)
        cam.start()
        log.write(f"cam{idx} configuration: {cam.camera_configuration()}\n")
        log.write(f"cam{idx} metadata: {cam.capture_metadata()}\n")

def burst(fdir, log, dt): 
    global busy
    i = 0
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'burst')
    imu = open(fname_imu, 'a')
    log.write(f"burst session: {fdir_out}\n")
    while right_button.is_pressed:
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        ypr = s.read_yaw_pitch_roll() # Read yaw, pitch, and roll values
        imu.write(f"{tstr}: Yaw: {ypr.x}, Pitch: {ypr.y}, Roll: {ypr.z}" + '\n') # Print the yaw, pitch, and roll values
        i += 1
        time.sleep(dt)
    imu.close()
    busy = False

def numFrames(fdir, log, dt, num_frames):
    global busy
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'numFrames')
    imu = open(fname_imu, 'a')
    log.write(f"numFrames session: {fdir_out}\n")
    imu.write("Timestamp, EzAsyncData, Yaw, Pitch, Roll, Aceel, Gyro, Mag, GPS_LLA, INS_LLA\n")  # Header line
    for i in range(int(num_frames)):
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3] 
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")

        ####################### IMU #######################
        ypr = s.read_yaw_pitch_roll() # Read yaw, pitch, and roll values
        gps_solution = s.read_gps_solution_lla() # Read the GPS solution in LLA format
        ins_solution = s.read_ins_solution_lla() # Read the INS solution
        imu_out = s.read_imu_measurements() # Read the IMU measurements
        cd = ez.current_data # Read the current data from the EzAsyncData class
        
        imu.write(f"{tstr}, {dir(cd)}, {ypr.x}, {ypr.y}, {ypr.z}, {imu_out.accel}, {imu_out.gyro}, {imu_out.mag}, {gps_solution.lla}, {ins_solution.position}" + '\n')
        ###################################################

        time.sleep(dt)
    imu.close()
    busy = False

def create_dirs(fdir, mode):
    session = datetime.now(timezone.utc).strftime('%H%M%S_' + mode)
    fdir_out = os.path.join(fdir, session + '/')
    fdir_cam0 = os.path.join(fdir_out, 'cam0/')
    fdir_cam1 = os.path.join(fdir_out, 'cam1/')
    os.makedirs(fdir_cam0, exist_ok=True)
    os.makedirs(fdir_cam1, exist_ok=True)
    fname_imu = f'{fdir_out}IMU_{session}.txt'
    print(f'--Created output folders: {fdir_cam0} and {fdir_cam1}')
    return fdir_out, fdir_cam0, fdir_cam1, fname_imu

def exit_standby(log):
    log.write(f"EXITING STANDBY.\n")
    log.close()
    s.disconnect() # Disconnect from the VN-200
    cam0.stop() 
    cam1.stop() # Close the cameras
    right_button.close() 
    left_button.close() # Close the buttons
    sys.exit(0)

def standby(fdir, pathLog, dt, num_frames):
    global busy
    log = open(pathLog, 'a')
    log.write(f"Entered standby mode.\n")
    configure_cameras(log)

    while not (right_button.is_held and left_button.is_held):

        if right_button.is_pressed and not left_button.is_pressed and not busy:
            busy = True
            burst(fdir, log, dt)
        if left_button.is_pressed and not right_button.is_pressed and not busy:
            busy = True
            numFrames(fdir, log, dt, num_frames)
        time.sleep(0.2)

    exit_standby(log)

if __name__ == "__main__":
    standby(sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]))