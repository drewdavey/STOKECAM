# Last updated: 2024-04-10
import os
import time
import pprint
import subprocess
from settings import *
from picamera2 import Picamera2
from datetime import datetime, timezone
from startup import setup_logging, read_inputs_yaml

config = get_still_configuration() # get still config from settings.py. add statement here to choose mode

cam0 = Picamera2(0)
cam1 = Picamera2(1)

def run(fdir_out, fdir_cam0,fdir_cam1,fname_log,fname_imu,calib_frames,dt):
	log = open(fname_log, 'a')
	tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3] 
	log.write(f"{tstr}:     calibration session (from calib.py): {fdir_out}\n")
	imu_process = subprocess.Popen(['python3', 'imu.py', fname_imu, fname_log])

	for idx, cam in enumerate([cam0, cam1]):
		cam.configure(config)
		cam.start()
		# format_config = pprint.pformat(cam.camera_configuration(), width=100, indent=2)
		# format_meta = pprint.pformat(cam.capture_metadata(), width=100, indent=2)  
		# log.write(f"cam{idx} configuration: {format_config}\n\n\n")
		# log.write(f"cam{idx} metadata: {format_meta}\n\n\n")
	
	for i in range(int(calib_frames)):
		tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3] 
		cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
		cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
		time.sleep(dt)
	imu_process.terminate()
	
	cam0.stop()
	cam1.stop()
	cam0.close()
	cam1.close()
	log.close()	
	exit() 

def create_dirs(fdir, mode):
    session = datetime.now(timezone.utc).strftime('%H%M%S_' + mode)
    fdir_out = os.path.join(fdir, session + '/')
    fdir_cam0 = os.path.join(fdir_out, 'cam0/')
    fdir_cam1 = os.path.join(fdir_out, 'cam1/')
    os.makedirs(fdir_cam0, exist_ok=True)
    os.makedirs(fdir_cam1, exist_ok=True)
    fname_imu = f'{fdir_out}IMU_{session}.txt'
    return fdir_out, fdir_cam0, fdir_cam1, fname_imu

fdir, fname_log = setup_logging()               # Setup logging
inputs = read_inputs_yaml(fname_log)            # Read inputs from inputs.yaml
calib_frames = inputs['calib_frames']
dt = inputs['calib_dt']
fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'calib')
run(fdir_out, fdir_cam0, fdir_cam1, fname_log, fname_imu, calib_frames, dt)