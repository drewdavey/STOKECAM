
from picamera2 import Picamera2
from settings import *

config = get_still_configuration() 

cam = Picamera2(0)
cam.start()
cam.stop()
cam.close()
