#!/usr/bin/python3
#!/usr/bin/python3
import sys
import time
import os
import cv2
import threading
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from gpiozero import Button, LED
from datetime import datetime, timezone
from collections import deque
from utils import *
from settings import *

# Base directory setup
BASE_DIR = "/home/drew/testing_drew/"
LOG_FILE = os.path.join(BASE_DIR, "log.txt")

# Setup GPIO buttons and LED
right_button = Button(18)  # Hold to record
left_button = Button(17)  # Other button for standby exit
red_led = LED(24)

# Load config from YAML
inputs = read_inputs_yaml(LOG_FILE)
dt = inputs["dt"]
shooting_modes = [inputs["shooting_mode0"], inputs["shooting_mode1"], inputs["shooting_mode2"]]
mode = shooting_modes[0]

# Initialize cameras
cam0 = Picamera2(0)
cam1 = Picamera2(1)
config = get_config(mode)

cam0.configure(config)
cam1.configure(config)

# Use MJPEGEncoder for RAM buffering (no file saving)
encoder0 = MJPEGEncoder()
encoder1 = MJPEGEncoder()

# Circular buffer to store recent frames
buffer_size = 1000  # Store up to 1000 frames
image_buffer0 = deque(maxlen=buffer_size)
image_buffer1 = deque(maxlen=buffer_size)

def apply_timestamp(image):
    """Overlay a timestamp on the image."""
    timestamp = str(time.monotonic_ns())
    cv2.putText(image, timestamp, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return image

def record_and_process(fdir_cam0, fdir_cam1):
    """Capture video frames in RAM and save extracted frames to directories."""
    red_led.on()
    cam0.start()
    cam1.start()

    try:
        while right_button.is_pressed:
            timestamp0 = time.monotonic_ns()
            img0 = cam0.capture_array("main")

            timestamp1 = time.monotonic_ns()
            img1 = cam1.capture_array("main")

            img0 = apply_timestamp(img0)
            img1 = apply_timestamp(img1)

            image_buffer0.append((img0, timestamp0))
            image_buffer1.append((img1, timestamp1))

            time.sleep(0.03)  # ~30 FPS

    finally:
        cam0.stop()
        cam1.stop()
        red_led.off()
        save_frames(fdir_cam0, fdir_cam1)

def save_frames(fdir_cam0, fdir_cam1):
    """Save buffered frames as JPEGs."""
    while image_buffer0:
        img0, timestamp0 = image_buffer0.popleft()
        img1, timestamp1 = image_buffer1.popleft()

        filename0 = os.path.join(fdir_cam0, f"{timestamp0}.jpg")
        filename1 = os.path.join(fdir_cam1, f"{timestamp1}.jpg")

        # Convert RGB to BGR for OpenCV
        img0 = cv2.cvtColor(img0, cv2.COLOR_RGB2BGR)
        img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2BGR)

        cv2.imwrite(filename0, img0)
        cv2.imwrite(filename1, img1)
        print(f"Saved: {filename0} and {filename1}")

def enter_standby():
    """Handles session directory creation and standby logic."""
    global mode
    tstr = datetime.now(timezone.utc).strftime("%H%M%S%f")
    
    # Create session directories
    fdir_out, fdir_cam0, fdir_cam1, _ = create_dirs(BASE_DIR, f"session_{mode}")

    while not (right_button.is_held and left_button.is_held):
        if right_button.is_pressed and not left_button.is_pressed:
            record_and_process(fdir_cam0, fdir_cam1)
        time.sleep(0.2)

# Main loop
try:
    while True:
        if right_button.is_held:
            enter_standby()
        time.sleep(0.2)
except KeyboardInterrupt:
    print("Exiting.")
    cam0.stop()
    cam1.stop()
    sys.exit(0)
