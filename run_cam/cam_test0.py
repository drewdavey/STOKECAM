## Camera Test
## Last updated: 2024-02-12

from picamera2 import Picamera2, Preview
import time
from datetime import datetime
from gpiozero import Button
from signal import pause

cam0 = Picamera2(0)
cam1 = Picamera2(1)

button = Button(18)

#camera_config = cam0.create_still_configuration(main={"size":(1920,1080)}, lores={"size":(640,480)}, display="lores")
# camera_config = cam0.create_still_configuration(main={"size":(1920,1080)}, lores={"size":(640,480)}, display="lores")
#cam0.configure(camera_config)
	
def capture():
#	cam0.start_preview(Preview.QTGL)
	timestamp = datetime.now().isoformat()
	cam0.start()
	cam1.start()
	time.sleep(1)
	cam0.capture_file('/home/drew/Pictures/cam0/%s.jpg' % timestamp)
	cam1.capture_file('/home/drew/Pictures/cam1/%s.jpg' % timestamp)
#s	cam0.stop_preview
	cam0.stop()
	cam1.stop()
	
	
# #arg = input('Take a picture? (y/n)')
# while arg == 'y':
	
	# capture
	# pause()
	# arg = input('Take a picture? (y/n)')
	
button.when_pressed = capture
pause()


