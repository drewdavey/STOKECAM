# Last updated: 2024-04-10
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import sys
import time
from picamera2 import Picamera2
from settings import *

config = get_still_configuration()

cam0 = Picamera2(0)
cam1 = Picamera2(1)

def run(path0,path1,pathLog,num_frames,dt):
	log = open(pathLog, 'a')
	log.write(f"Entered numFrames mode.\n")

	for idx, cam in enumerate([cam0, cam1]):
		cam.configure(config)
		cam.start()
		log.write(f"cam{idx} configuration: {cam.camera_configuration()}\n")
		log.write(f"cam{idx} metadata: {cam.capture_metadata()}\n")

	for i in range(int(num_frames)):
		tstr = time.strftime('%H%M%S%f')[:-3] 
		cam0.capture_file(f"{path0}0_{tstr}_{i+1:05}.jpg")
		cam1.capture_file(f"{path1}1_{tstr}_{i+1:05}.jpg")
		time.sleep(dt)
	
	cam0.stop()
	cam1.stop()
	
	cam0.close()
	cam1.close()
	exit() 

if __name__ == '__main__':
    run(sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5]))
