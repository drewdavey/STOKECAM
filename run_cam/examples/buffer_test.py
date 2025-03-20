import sys
import time
import io
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
buffer_size = 1000  # Store last 100 images in memory
image_buffer0 = deque(maxlen=buffer_size)
image_buffer1 = deque(maxlen=buffer_size)
write_queue = queue.Queue()

def capture_continuous(dt):
    """Capture images continuously into RAM buffer while the button is held."""
    i = 1
    while right_button.is_pressed:
        timestamp0 = time.monotonic_ns()
        buffer0 = io.BytesIO()
        cam0.capture_file(buffer0, format='jpeg')
        filename0 = f"{timestamp0}_{i:05}"

        timestamp1 = time.monotonic_ns()
        buffer1 = io.BytesIO()
        cam1.capture_file(buffer1, format='jpeg')
        filename1 = f"{timestamp1}_{i:05}"

        image_buffer0.append((buffer0, filename0))
        image_buffer1.append((buffer1, filename1))
        
        i += 1

def write_images_to_sd(fdir_cam0, fdir_cam1):
    """Background process to write images from buffer to SD card."""
    while not write_queue.empty():
        try:
            buffer0, filename0 = write_queue.get(timeout=2)
            buffer1, filename1 = write_queue.get(timeout=2)

            filename0 = f"{fdir_cam0}0_{filename0}.jpg"
            filename1 = f"{fdir_cam1}1_{filename1}.jpg"

            with open(filename0, "wb") as f:
                f.write(buffer0.getvalue())
            with open(filename1, "wb") as f:
                f.write(buffer1.getvalue())

            print(f"Saved {filename0} and {filename1}")
        except queue.Empty:
            break

def process_and_store(fdir_cam0, fdir_cam1):
    """Queue images for writing after button release."""
    for i in range(len(image_buffer0)):
        write_queue.put(image_buffer0[i])
        write_queue.put(image_buffer1[i])
    
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
    yellow.off(), red.off()
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
    while not (right_button.is_held and left_button.is_held):
        if right_button.is_pressed and not left_button.is_pressed:  
            red.on()
            capture_continuous(dt)
            process_and_store(fdir_cam0, fdir_cam1)
            red.off()
        time.sleep(0.2)
    exit_standby(fname_log)

############################ Initialization ############################
green = LED(12)
yellow = LED(16)
red = LED(24)
right_button = Button(18, hold_time=3)
left_button = Button(17, hold_time=3)

fdir = '/home/drew/testing_drew/'
fname_log = '/home/drew/testing_drew/log.txt'
inputs = read_inputs_yaml(fname_log)
dt = inputs['dt']

global cam0, cam1, config, mode, standby, shooting_modes
shooting_modes = [inputs['shooting_mode0'], inputs['shooting_mode1'], inputs['shooting_mode2']]
mode = shooting_modes[0]
config = get_config(mode)

cam0 = Picamera2(0)
cam1 = Picamera2(1)
configure_cameras(fname_log, mode)

standby = False
tlast = time.time()

try:
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
        log.write(traceback.format_exc() + "\n")
finally:
    cam0.stop()
    cam1.stop()
    cam0.close()
    cam1.close()
    green.close()
    yellow.close()
    red.close()
    right_button.close()
    left_button.close()
    sys.exit(0)


