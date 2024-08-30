# Last updated: 2024-02-23
##################################
# This script is passed 5 arguments from run_burst.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) dt (5) duration
##################################

import sys
from picamera2 import Picamera2
import time
from datetime import datetime
from gpiozero import Button
from signal import pause
from threading import Timer
from functools import partial
from settings import *

i = 0  # Global index variable

config = get_still_configuration()

cam0 = Picamera2(0)
cam1 = Picamera2(1)

def run(path0,path1,pathLog,dt,duration):
	button = Button(18)
	log = open(pathLog, 'a')
	log.write(f"Entered burst mode.\n")

	for idx, cam in enumerate([cam0, cam1]):
		cam.configure(config)
		cam.start()
		log.write(f"cam{idx} configuration: {cam.camera_configuration()}\n")
		log.write(f"cam{idx} metadata: {cam.capture_metadata()}\n")

	def capture(i):
		while button.is_pressed:
			timestamp = datetime.utcnow()
			tstr = timestamp.strftime('%H%M%S%f')[:-3]
			cam0.capture_file(f"{path0}0_{tstr}_{i+1:05}.jpg")
			cam1.capture_file(f"{path1}1_{tstr}_{i+1:05}.jpg")
			i += 1
			time.sleep(dt)

	def end_program():
		cam0.stop()
		cam1.stop()
		cam0.close()
		cam1.close()
		exit()

	# Set a timer to end the program after the specified duration
	Timer(duration, end_program).start()

	button.when_pressed = lambda: capture(i)
	
if __name__ == '__main__':
    run(sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4]),int(sys.argv[5]))
