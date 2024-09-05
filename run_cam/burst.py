# Last updated: 2024-04-10
##################################
# This script captures images continuosly at [dt] while right button is held. 
# It reads inputs from inputs.yaml and creates directories for the session.
##################################
import os
import time
import subprocess
from utils import *
from settings import *
from threading import Timer
from picamera2 import Picamera2
from gpiozero import Button, LED
from datetime import datetime, timezone

config = get_config('auto')

cam0 = Picamera2(0)
cam1 = Picamera2(1)

i = 0  # Global index variable

def run(fdir_out, fdir_cam0, fdir_cam1, fname_log, fname_imu, duration, dt):
	button = Button(18)
	log = open(fname_log, 'a')
	tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3] 
	log.write(f"{tstr}:     burst session (from burst.py): {fdir_out}\n")
	log.close()	
	imu_process = subprocess.Popen(['python3', 'imu.py', fname_imu, fname_log])
	log = open(fname_log, 'a')
	for idx, cam in enumerate([cam0, cam1]):
		cam.configure(config)
		cam.start()
		log.write(f"{tstr}:     cam{idx} configuration: {cam.camera_configuration()}\n")
		log.write(f"{tstr}:     cam{idx} metadata: {cam.capture_metadata()}\n")
	log.close()
	def capture(i):
		while button.is_pressed:
			tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
			cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
			cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
			i += 1
			time.sleep(dt)

	def end_program():
		imu_process.terminate()
		cam0.stop()
		cam1.stop()
		cam0.close()
		cam1.close()
		exit()

	# Set a timer to end the program after the specified duration
	Timer(duration, end_program).start()

	button.when_pressed = lambda: capture(i)

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
duration = 10
dt = inputs['dt']
fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'burst')
run(fdir_out, fdir_cam0, fdir_cam1, fname_log, fname_imu, duration, dt)