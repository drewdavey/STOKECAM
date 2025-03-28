import RPi.GPIO as GPIO
from picamera2 import Picamera2, Preview
import time
import numpy as np

"""    camera configuration   """
picam2 = Picamera2()
camera_config = picam2.create_still_configuration({"format": "YUV420"})
camera_config['buffer_count'] = 3
camera_config['queue'] = False
picam2.controls.ExposureTime = 2000		# set a random number, exposure time set by the external pulse width

picam2.align_configuration(camera_config)		# resizing to whichever closest size that python is more comfortable with for improved efficiency
picam2.configure(camera_config)			


""" external trigger COMS pulse (PWM) configuration and initiation  """
pin_number = 26				# GPIO pin number = 17, board pin number = 11
frqHz = 10				# pulse frequency in Hz
pulse_width = 0.002			# ON/HIGH TIME in seconds
duty = 100 * pulse_width * frqHz	# duty cycle in %
#GPIO.setmode(GPIO.BOARD)		# to use the board pin numbering instead of the GPIO numbers
GPIO.setmode(GPIO.BCM)			# to use the GPIO pin numbering instead of the board numbers
GPIO.setup(pin_number,GPIO.OUT)		# set the pin to OUT
GPIO.output(pin_number, False)		# to output HIGH (True) or LOW (False)
signal = GPIO.PWM(pin_number,frqHz) 	# create the PWM object
signal.start(duty)			# starting te signal with the set duty cycle

"""  starting the camera and grabing images for 20 seconds
     in the future this part will be in a seperate thread with some processing on each array/image   """
counter1 = 0	
picam2.start()
ts = time.perf_counter()
while time.perf_counter() - ts <= 20:
    counter1 += 1
    array = picam2.capture_array("main")

signal.stop()						# stop the PWM object, i stop the signal before the camera to check if it is running only while the signal is runing.
time.sleep(1)
picam2.stop()
time.sleep(1)
GPIO.cleanup()
print(counter1)
