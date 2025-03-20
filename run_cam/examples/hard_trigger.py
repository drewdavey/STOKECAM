import RPi.GPIO as GPIO
import time
from picamera2 import Picamera2

# Define GPIO pin for hardware trigger
TRIGGER_PIN = 23  # GPIO23 (physical pin 16)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIGGER_PIN, GPIO.OUT, initial=GPIO.LOW)

# Initialize cameras
cam0 = Picamera2(0)
cam1 = Picamera2(1)
cam0.start()
cam1.start()

def trigger_cameras():
    """Send a hardware trigger pulse to both cameras."""
    GPIO.output(TRIGGER_PIN, GPIO.HIGH)
    time.sleep(0.001)  # 1ms pulse ##### EXPOSURE TIME #####
    GPIO.output(TRIGGER_PIN, GPIO.LOW)

def save_images(fdir_cam0, fdir_cam1, i):
    """Capture images from both cameras and save them."""
    tstr = str(time.monotonic_ns())
    cam0.capture_file(f"{fdir_cam0}/0_{tstr}_{i+1:05}.jpg")
    cam1.capture_file(f"{fdir_cam1}/1_{tstr}_{i+1:05}.jpg")

def capture_images(fdir_cam0, fdir_cam1, i):
    """Trigger cameras and save images."""
    trigger_cameras()
    time.sleep(0.1)  # Allow time for exposure 
    save_images(fdir_cam0, fdir_cam1, i)

# Example usage:
capture_images("/path/to/cam0", "/path/to/cam1", 0)
