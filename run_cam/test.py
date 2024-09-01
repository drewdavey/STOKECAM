
from picamera2 import Picamera2

cam = Picamera2(0)
cam.start()
cam.stop()
cam.close()
