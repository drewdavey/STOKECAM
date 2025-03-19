#!/usr/bin/python3
import sys
import time
import os
import cv2
import threading
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder
from gpiozero import Button, LED
from datetime import datetime, timezone
from utils import create_dirs, read_inputs_yaml, get_config

# Load configuration from YAML
BASE_DIR = "/home/drew/testing_drew/"
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
inputs = read_inputs_yaml(LOG_FILE)
dt = inputs["dt"]
shooting_modes = [inputs["shooting_mode0"], inputs["shooting_mode1"], inputs["shooting_mode2"]]
mode = shooting_modes[0]

# Setup GPIO buttons and LED
right_button = Button(18)  # Hold to record
left_button = Button(17)   # Hold both buttons to exit standby
red_led = LED(24)

# Initialize cameras
cam0 = Picamera2(0)
cam1 = Picamera2(1)
config = get_config(mode)

cam0.configure(config)
cam1.configure(config)

# Use H.264 encoder (videos stored in RAM)
encoder0 = H264Encoder(10000000)
encoder1 = H264Encoder(10000000)

# Video timestamp overlay settings
colour = (0, 255, 0)
origin = (0, 30)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2

def apply_timestamp(request):
    """Overlay a timestamp on each frame before encoding."""
    timestamp = str(time.monotonic_ns())
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, origin, font, scale, colour, thickness)

def record_and_process(fdir_cam0, fdir_cam1):
    """Records video streams and extracts frames using existing timestamps."""
    red_led.on()
    cam0.start()
    cam1.start()

    # Set callback to embed timestamp onto frames
    cam0.pre_callback = apply_timestamp
    cam1.pre_callback = apply_timestamp

    # Record video to RAM
    cam0.start_recording(encoder0, "/dev/null")
    cam1.start_recording(encoder1, "/dev/null")

    cap0 = cv2.VideoCapture(cam0)
    cap1 = cv2.VideoCapture(cam1)

    try:
        while right_button.is_pressed:
            ret0, frame0 = cap0.read()
            ret1, frame1 = cap1.read()

            if not ret0 or not ret1:
                break  # Stop if video feed fails

            # Read timestamp from the image
            timestamp_text = extract_timestamp(frame0)

            # Save frames using the extracted timestamp
            filename0 = os.path.join(fdir_cam0, f"{timestamp_text}.jpg")
            filename1 = os.path.join(fdir_cam1, f"{timestamp_text}.jpg")

            cv2.imwrite(filename0, frame0)
            cv2.imwrite(filename1, frame1)

            print(f"Saved: {filename0} and {filename1}")

            time.sleep(0.03)  # Approx 30 FPS
    finally:
        cam0.stop_recording()
        cam1.stop_recording()
        cam0.stop()
        cam1.stop()
        red_led.off()
        cap0.release()
        cap1.release()

def extract_timestamp(frame):
    """Extract timestamp from the frame by OCR or direct parsing (if applicable)."""
    return str(time.monotonic_ns())  # Replace with OCR if needed

def enter_standby():
    """Handles standby mode and session directory creation."""
    global mode
    tstr = datetime.now(timezone.utc).strftime("%H%M%S%f")

    # Create session directories following existing structure
    fdir_out, fdir_cam0, fdir_cam1, fdir_vid = create_dirs(BASE_DIR, f"session_{mode}")

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

