#!/usr/bin/python3
import sys
import time
import threading
import queue
import traceback
from collections import deque
from datetime import datetime, timezone
from utils import *
from settings import *
from picamera2 import Picamera2
from gpiozero import Button, LED

# Circular buffer and queue setup (store in memory first)
buffer_size = 1000  # Store last 1000 images in RAM before writing
image_buffer0 = deque(maxlen=buffer_size)
image_buffer1 = deque(maxlen=buffer_size)
write_queue = queue.Queue()

# Setup GPIO buttons and LED
right_button = Button(18, hold_time=3)  # Right button to capture
left_button = Button(17, hold_time=3)   # Left button for standby exit
green = LED(12)
yellow = LED(16)
red = LED(24)

# Load config
BASE_DIR = "/home/drew/testing_drew/"
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
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

def capture_image(cam, buffer, tnext):
    """Capture an image from a camera and store it in RAM."""
    while time.monotonic_ns() < tnext:
        pass  # Wait until exact time for sync
    timestamp = time.monotonic_ns()
    img = cam.capture_array("main")  # Capture image into RAM
    buffer.append((img, timestamp))  # Store image and timestamp

def capture_thread(fdir_cam0, fdir_cam1):
    """Threaded capture loop with watchdog-style timing."""
    i = 0
    red.on()
    
    while right_button.is_pressed:
        tnow = time.monotonic_ns()
        tnext = tnow + int(dt * 1e9)  # Next capture time (nanoseconds)

        p0 = threading.Thread(target=capture_image, args=(cam0, image_buffer0, tnext))
        p1 = threading.Thread(target=capture_image, args=(cam1, image_buffer1, tnext))

        p0.start()
        p1.start()
        p0.join()
        p1.join()

        i += 1

    red.off()
    process_and_store(fdir_cam0, fdir_cam1)

def process_and_store(fdir_cam0, fdir_cam1):
    """Queue images for writing after button release."""
    for i in range(len(image_buffer0)):
        write_queue.put(image_buffer0[i])
        write_queue.put(image_buffer1[i])
    thread = threading.Thread(target=write_images_to_sd, args=(fdir_cam0, fdir_cam1))
    thread.start()

def write_images_to_sd(fdir_cam0, fdir_cam1):
    """Background process to write images from RAM to SD card."""
    while not write_queue.empty():
        try:
            img0, timestamp0 = write_queue.get(timeout=2)
            img1, timestamp1 = write_queue.get(timeout=2)

            filename0 = os.path.join(fdir_cam0, f"{timestamp0}.jpg")
            filename1 = os.path.join(fdir_cam1, f"{timestamp1}.jpg")

            # Convert RGB to BGR for OpenCV
            img0 = cv2.cvtColor(img0, cv2.COLOR_RGB2BGR)
            img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2BGR)

            cv2.imwrite(filename0, img0)
            cv2.imwrite(filename1, img1)
            print(f"Saved {filename0} and {filename1}")
        except queue.Empty:
            break

def enter_standby():
    """Handles session directory creation and standby mode."""
    global mode
    tstr = datetime.now(timezone.utc).strftime("%H%M%S%f")

    # Create session directories following existing structure
    fdir_out, fdir_cam0, fdir_cam1, _ = create_dirs(BASE_DIR, f"session_{mode}")

    while not (right_button.is_held and left_button.is_held):
        if right_button.is_pressed and not left_button.is_pressed:
            capture_thread(fdir_cam0, fdir_cam1)
        time.sleep(0.2)

def configure_cameras():
    """Configures both cameras based on mode."""
    global cam0, cam1, config
    tstr = datetime.now(timezone.utc).strftime("%H%M%S%f")
    
    with open(LOG_FILE, 'a') as log:
        log.write(f"{tstr}: Configuring cameras to {mode} mode...\n")
    
    for idx, cam in enumerate([cam0, cam1]):
        cam.configure(config)
        cam.start()
    
        with open(LOG_FILE, 'a') as log:
            log.write(f"{tstr}: cam{idx} configuration: {cam.camera_configuration()}\n")
            log.write(f"{tstr}: cam{idx} metadata: {cam.capture_metadata()}\n")

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
