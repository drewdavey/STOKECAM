## Camera Test
## Last updated: 2024-02-14

import sys
from picamera2 import Picamera2
import time
from datetime import datetime
from gpiozero import Button
from signal import pause

def run(path,num_frames):
	
	cam0 = Picamera2(0)
	cam1 = Picamera2(1)
	cam0.start()
	cam1.start()

	for i in num_frames:
		print('----------'+str(i)+'------------')
		timestamp = datetime.utcnow()
		tstr = timestamp.strftime('%H%M%S%f')[:-3]
		cam0.capture_file(path+'cam0/'+tstr+'.jpg')
		cam1.capture_file(path+'cam1/'+tstr+'.jpg')
		time.sleep(1)
	
	cam0.stop()
	cam1.stop()
		

if __name__ == '__main__':
    run(sys.argv[1],sys.argv[2])