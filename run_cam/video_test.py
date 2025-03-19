#!/usr/bin/python3
import sys
import time
import os
import cv2
import threading
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2 import MappedArray, Picamera2
from gpiozero import Button, LED
from datetime import datetime

# Directories
BASE_DIR = "/home/drew/testing_drew/"
VIDEO_DIR = os.path.join(BASE_DIR, "videos/")
CAM0_DIR = os.path.join(BASE_DIR, "cam0/")
CAM1_DIR = os.path.join(BASE_DIR, "cam1/")

# Ensure directories exist
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(CAM0_DIR, exist_ok=True)
os.makedirs(CAM1_DIR, exist_ok=True)

# Setup GPIO buttons and LED
right_button = Button(18)  # Hold to record
red_led = LED(24)

# Initialize cameras
cam0 = Picamera2(0)
cam1 = Picamera2(1)

# Create video configuration
config = cam0.create_video_configuration()
cam0.configure(config)
cam1.configure(config)

# Encoder settings
encoder0 = H264Encoder(10000000)
encoder1 = H264Encoder(10000000)

colour = (0, 255, 0)
origin = (0, 30)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2


def apply_timestamp(request):
    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, origin, font, scale, colour, thickness)

cam0.pre_callback = apply_timestamp
cam1.pre_callback = apply_timestamp

def record_video():
    """Starts recording video on both cameras while the button is held."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    video_path0 = os.path.join(VIDEO_DIR, f"cam0_{timestamp}.h264")
    video_path1 = os.path.join(VIDEO_DIR, f"cam1_{timestamp}.h264")

    red_led.on()
    cam0.start()
    cam1.start()

    cam0.start_recording(encoder0, video_path0)
    cam1.start_recording(encoder1, video_path1)
    
    print(f"Recording started: {video_path0} and {video_path1}")

    try:
        while right_button.is_pressed:
            time.sleep(0.1)
    finally:
        cam0.stop_recording()
        cam1.stop_recording()
        cam0.stop()
        cam1.stop()
        red_led.off()

        print(f"Recording stopped. Extracting frames...")
        extract_frames(video_path0, CAM0_DIR)
        extract_frames(video_path1, CAM1_DIR)

def extract_frames(video_path, output_dir):
    """Extracts frames from a video file and saves them as JPEGs."""
    cap = cv2.VideoCapture(video_path)
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # Stop when video ends

        timestamp = time.monotonic_ns()
        frame_filename = os.path.join(output_dir, f"{timestamp}_{frame_count:05}.jpg")

        cv2.imwrite(frame_filename, frame)
        frame_count += 1

    cap.release()
    print(f"Frames saved in {output_dir}")

# Main loop
try:
    while True:
        if right_button.is_pressed:
            record_video()
        time.sleep(0.2)
except KeyboardInterrupt:
    print("Exiting.")
    cam0.stop()
    cam1.stop()
    sys.exit(0)
