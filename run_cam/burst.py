# Last updated: 2024-02-23
import os
import time
import pprint
import subprocess
from gpiozero import Button
from signal import pause
from threading import Timer
from settings import *
from picamera2 import Picamera2
from datetime import datetime, timezone
from startup import setup_logging, read_inputs_yaml

i = 0  # Global index variable

config = get_still_configuration()

cam0 = Picamera2(0)
cam1 = Picamera2(1)

def run(fdir_cam0, fdir_cam1, fname_log, fname_imu, duration, dt):
	button = Button(18)
	log = open(fname_log, 'a')
	log.write(f"Running burst mode manually.\n")
	imu_process = subprocess.Popen(['python3', 'imu.py', fname_imu, fname_log])

	for idx, cam in enumerate([cam0, cam1]):
		cam.configure(config)
		cam.start()
		format_config = pprint.pformat(cam.camera_configuration(), width=100, indent=2)
		format_meta = pprint.pformat(cam.capture_metadata(), width=100, indent=2)  
		log.write(f"cam{idx} configuration: {format_config}\n\n\n\n\n")
		log.write(f"cam{idx} metadata: {format_meta}\n\n\n\n\n")

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
duration = inputs['burst_duration']
dt = inputs['dt']
fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, 'burst')
run(fdir_cam0, fdir_cam1, fname_log, fname_imu, duration, dt)