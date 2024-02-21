## Camera Test
## Last updated: 2024-02-14

import sys
from picamera2 import Picamera2
import time
from datetime import datetime
from gpiozero import Button
from signal import pause

def run(path):

	def capture():
		cam0 = Picamera2(0)
		cam1 = Picamera2(1)
		#	cam0.start_preview(Preview.QTGL)
		timestamp = datetime.utcnow()
		tstr = timestamp.strftime('%H%M%S%f')[:-3]
		cam0.start()
		cam1.start()
		time.sleep(1)
		cam0.capture_file(path+'cam0/'+tstr+'.jpg')
		cam1.capture_file(path+'cam1/'+tstr+'.jpg')
		#cam0.stop_preview
		time.sleep(1)
		cam0.stop()
		cam1.stop()
		exit(0);
		
	
	button = Button(17)
	button.when_pressed = capture
	pause()
	#button.close()
	#cam0.stop()
	#cam1.stop()


#exit(0);
#cam0.stop()
#cam1.stop()


if __name__ == '__main__':
    run(sys.argv[1])
