# Last updated: 2025-02-04
##################################
# This script allows the user to toggle through camera settings, launch standby mode, and capture images syncronously by holding right button.
# The user can also calibrate the cameras by holding the left button for more than 5 seconds.
##################################
import sys
import time
import cv2
import queue
from collections import deque
import threading
import traceback
from utils import *
from settings import *
from picamera2 import Picamera2
from gpiozero import Button, LED
from datetime import datetime, timezone, timedelta

# Circular buffer and queue setup
buffer_size = 100  # Store last 50 images in memory
image_buffer0 = deque(maxlen=buffer_size)
image_buffer1 = deque(maxlen=buffer_size)
timestamp_buffer = deque(maxlen=buffer_size)
write_queue = queue.Queue()

def capture_continuous(dt):
    """Capture images continuously into RAM while the button is held."""
    i = 1
    while right_button.is_pressed:
        timestamp = time.monotonic_ns() 
        img0 = cam0.capture_array()  # Capture to NumPy array
        img1 = cam1.capture_array()
        filename = f"{timestamp}_{{i+1:05}}"
        image_buffer0.append((img0, filename))
        image_buffer1.append((img1, filename))
        timestamp_buffer.append(timestamp)
        i = i + 1
        time.sleep(dt)  # Maintain 25Hz capture rate

def write_images_to_sd(fdir_cam0, fdir_cam1):
    """Background process to write images to SD card."""
    while True:
        try:
            img0, img1, timestamp = write_queue.get(timeout=2)
            filename0 = f"{fdir_cam0}0_{timestamp}.jpg"
            filename1 = f"{fdir_cam1}1_{timestamp}.jpg"
            cv2.imwrite(filename0, img0)  # Save as full-resolution images
            cv2.imwrite(filename1, img1)
            print(f"Saved {filename0} and {filename1}")
        except queue.Empty:
            break

def process_and_store(fdir_cam0, fdir_cam1):
    """Queue images for writing after button release."""
    for i in range(len(image_buffer0)):
        write_queue.put((image_buffer0[i][0], image_buffer1[i][0], image_buffer0[i][1]))
    thread = threading.Thread(target=write_images_to_sd, args=[fdir_cam0, fdir_cam1])
    thread.start()

def configure_cameras(fname_log, mode):
    global cam0, cam1, config 
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Configuring cameras to {mode} mode...\n")
    for idx, cam in enumerate([cam0, cam1]):
        cam.configure(config)
        cam.start()
        log.write(f"{tstr}:     cam{idx} configuration: {cam.camera_configuration()}\n")
        log.write(f"{tstr}:     cam{idx} metadata: {cam.capture_metadata()}\n")
    log.write('\n'), log.close()

def exit_standby(fname_log):
    global standby
    yellow.off(), red.off() # Close the lights
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Exiting standby.\n\n"), log.close()
    time.sleep(1)
    standby = False

def enter_standby(fdir, fname_log, dt, mode):
    yellow.on()
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Entering standby... \n\n"), log.close()
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"session_{mode}")
    time.sleep(1)
    while not (right_button.is_held and left_button.is_held): # Hold both buttons for 3 seconds to exit standby
        if right_button.is_pressed and not left_button.is_pressed:  
            red.on()
            capture_continuous(dt)
            process_and_store(fdir_cam0, fdir_cam1)
            red.off()
        time.sleep(0.2)
    exit_standby(fname_log)

############################ Initialization ############################
green = LED(12)                         # Green LED
yellow = LED(16)                        # Yellow LED
red = LED(24)                           # Red LED
right_button = Button(18, hold_time=3)  # Right button
left_button = Button(17, hold_time=3)   # Left button     

fdir = '/home/drew/testing_drew/'
fname_log = '/home/drew/testing_drew/log.txt'
inputs = read_inputs_yaml(fname_log)            # Read inputs from inputs.yaml
dt = inputs['dt']
calib_dt = inputs['calib_dt']
calib_frames = inputs['calib_frames']

global cam0, cam1, config, mode, standby, shooting_modes
shooting_modes = [inputs['shooting_mode0'], inputs['shooting_mode1'], inputs['shooting_mode2']]
mode = shooting_modes[0]                        # Default to 'auto'
config = get_config(mode)                       # Get the configuration for the cameras
cam0 = Picamera2(0)                             # Initialize cam0       
cam1 = Picamera2(1)                             # Initialize cam1
configure_cameras(fname_log, mode)              # Configure the cameras

standby = False
tnow = time.time()
tlast = time.time()
#######################################################################

try: 
    ############################# Main loop ###############################
    # Hold right button ONLY for 3 seconds to enter standby mode    
    # Hold left button ONLY for 3 seconds to calibrate the cameras
    # Hold both buttons for 3 seconds to toggle modes, then:
    #                         - release both to toggle modes
    #                         - release left ONLY to exit script                   
    while True: 
        if (time.time() - tlast > 10) and not standby:
            tlast = time.time()
        if right_button.is_held and not standby and not left_button.is_pressed:
            standby = True
            enter_standby(fdir, fname_log, dt, mode)    
        time.sleep(0.2)
except Exception as e:
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        log.write(f"{tstr}: ERROR: {str(e)}\n")
        log.write("Traceback:\n")
        log.write(traceback.format_exc() + "\n")  # Log the traceback
    #######################################################################
finally:
    ############################## Cleanup ###############################
    cam0.stop(), cam1.stop()                   # Stop the cameras
    cam0.close(), cam1.close()                 # Close the cameras
    green.close(), yellow.close(), red.close() # Close the LEDs
    right_button.close(), left_button.close()  # Close the buttons
    sys.exit(0)
    #######################################################################