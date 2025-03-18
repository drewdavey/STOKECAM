import time
import threading
import queue
from collections import deque
from datetime import datetime, timezone
from picamera2 import Picamera2
from gpiozero import Button
import numpy as np
import cv2

# Initialize Picamera2 for both cameras
cam0 = Picamera2(0)
cam1 = Picamera2(1)
config0 = cam0.create_still_configuration(buffer_count=8)
config1 = cam1.create_still_configuration(buffer_count=8)
cam0.configure(config0)
cam1.configure(config1)
cam0.start()
cam1.start()

# Circular buffer and queue setup
buffer_size = 50  # Store last 50 images in memory
image_buffer0 = deque(maxlen=buffer_size)
image_buffer1 = deque(maxlen=buffer_size)
timestamp_buffer = deque(maxlen=buffer_size)
write_queue = queue.Queue()

dt = 1 / 25  # Capture at 25Hz (40ms interval)
right_button = Button(18, hold_time=3)  # Right button

def capture_continuous():
    """Capture images continuously into RAM while the button is held."""
    while right_button.is_pressed:
        timestamp = time.monotonic_ns() 
        img0 = cam0.capture_array("main")  # Capture to NumPy array
        img1 = cam1.capture_array("main")
        image_buffer0.append((img0, timestamp))
        image_buffer1.append((img1, timestamp))
        timestamp_buffer.append(timestamp)
        time.sleep(dt)  # Maintain 25Hz capture rate

def write_images_to_sd():
    """Background process to write images to SD card."""
    while True:
        try:
            img0, img1, timestamp = write_queue.get(timeout=2)
            filename0 = f"/home/pi/cam0_{timestamp}.jpg"
            filename1 = f"/home/pi/cam1_{timestamp}.jpg"
            cv2.imwrite(filename0, img0)  # Save as full-resolution images
            cv2.imwrite(filename1, img1)
            print(f"Saved {filename0} and {filename1}")
        except queue.Empty:
            break

def process_and_store():
    """Queue images for writing after button release."""
    for i in range(len(image_buffer0)):
        write_queue.put((image_buffer0[i][0], image_buffer1[i][0], image_buffer0[i][1]))
    thread = threading.Thread(target=write_images_to_sd)
    thread.start()

# Main loop
while True:
    if right_button.is_pressed:
        capture_continuous()
        process_and_store()


