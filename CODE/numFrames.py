# Last updated: 2024-04-08
##################################
# This script is passed 5 arguments from run_numFrames.sh
# Args: (1) Cam0 path (2) Cam1 path (3) Log path (4) Number of frames (5) dt
##################################

import sys
import time
from picamera2 import Picamera2
from datetime import datetime
# from signal import pause
from libcamera import Transform
# import xarray as xr

def run(path0,path1,pathLog,num_frames,dt):
	cam0 = Picamera2(0)
	cam1 = Picamera2(1)

	# Define camera configurations
	config0 = cam0.create_still_configuration()
	config1 = cam1.create_still_configuration()
	
	# Configuration settings
	config0['main']['size'] = (1920, 1080)  # Resolution for cam0
	config1['main']['size'] = (1920, 1080)  # Resolution for cam1
	config0['controls']['FrameDurationLimits'] = (33333, 33333)  # Frame rate (in microseconds) for cam0
	config1['controls']['FrameDurationLimits'] = (33333, 33333)  # Frame rate for cam1
	
	# Try this .. maybe import xarray
	# config0.main.size = (1920, 1080)  # Resolution for cam0
	# config1.main.size = (1920, 1080)  # Resolution for cam1
	# config0.controls.FrameDurationLimits = (33333, 33333)  # Frame rate (in microseconds) for cam0
	# config1.controls.FrameDurationLimits = (33333, 33333)  # Frame rate for cam1

	# More config settings, why?
	# cam0.rotation = 180
	# cam1.rotation = 180
	config0['transform'] = Transform(vflip=1)
	config1['transform'] = Transform(vflip=1)

	cam0.start()
	cam1.start()
	# Apply configurations
	cam0.configure(config0)
	cam1.configure(config1)



	meta0 = cam0.capture_metadata()
	meta1 = cam1.capture_metadata()

	# Write to log file
	outfile = open(pathLog, 'a')
	outfile.write('\n' + 'Start Time: ' + datetime.utcnow().strftime('%H%M%S%f')[:-3] + '\n')
	outfile.write('\n' + 'Cam0 Metadata:' + '\n')
	outfile.write(str(meta0) + '\n')
	outfile.write('\n' + 'Cam0 Config:' + '\n')
	outfile.write(str(config0) + '\n')
	outfile.write('' + '\n')
	outfile.write('Cam1 Metadata:' + '\n')
	outfile.write(str(meta1) + '\n')
	outfile.write('\n' + 'Cam1 Config:' + '\n')
	outfile.write(str(config1) + '\n')
	
	for i in range(int(num_frames)):
		timestamp = datetime.utcnow()
		tstr = timestamp.strftime('%H%M%S%f')[:-3] 
		cam0.capture_file(f"{path0}0_{tstr}_{i+1:05}.jpg")
		cam1.capture_file(f"{path1}1_{tstr}_{i+1:05}.jpg")
		time.sleep(dt)
	
	cam0.stop()
	cam1.stop()

	outfile.write('\n' + 'Stop Time: ' + datetime.utcnow().strftime('%H%M%S%f')[:-3] + '\n')
	outfile.write('Done collecting images.' + '\n')
	outfile.close()
	
	
	cam0.close()
	cam1.close()
	exit() 
		

if __name__ == '__main__':
    run(sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5]))
