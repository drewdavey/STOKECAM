# master_multiProc.py
# Last updated: 2025-02-04
##################################
# This script allows the user to toggle through camera settings, launch standby mode,
# and capture images synchronously by holding the right button.
# The user can also calibrate the cameras by holding the left button for >5 seconds.
##################################

import sys
import time
import cv2
import vectornav
import traceback
import threading
from utils import *
from settings import *
from vectornav import *
import queue
import multiprocessing  ### CHANGED ###
# from collections import deque   # <--- Removed since we won't use deque
from picamera2 import Picamera2
from gpiozero import Button, LED
from vectornav.Plugins import ExporterCsv
from datetime import datetime, timezone, timedelta

def monitor_gps(portName):
    s = Sensor()  # Create sensor object and connect to the VN-200
    s.autoConnect(portName)
    gnss = Registers.GnssSolLla()
    s.readRegister(gnss)
    gnssFix = gnss.gnss1Fix.name
    if gnssFix == 'NoFix':
        green.blink(0.25, 0.25)
    elif gnssFix == 'TimeFix':
        green.blink(1, 1)
    elif gnssFix == 'Fix2D':
        green.blink(2, 1)
    elif gnssFix == 'Fix3D':
        green.blink(3, 1)
    elif gnssFix == 'SBAS':
        green.on()
    elif gnssFix == 'RtkFloat':
        green.on()
    elif gnssFix == 'RtkFix':
        green.on()
    else:
        green.blink(1, 10)
    s.disconnect()

def exit_standby(fname_log):
    global standby
    yellow.off()
    red.off()
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        log.write(f"{tstr}:     Exiting standby.\n\n")
    time.sleep(1)
    standby = False

def enter_standby(fdir, fname_log, dt, mode, portName):
    yellow.on()
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        log.write(f"{tstr}:     Entering standby... \n\n")
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"session_{mode}")

    s = Sensor()  # Create sensor object and connect to the VN-200
    csvExporter = ExporterCsv(fdir_out, True)
    s.autoConnect(portName)
    s.subscribeToMessage(
        csvExporter.getQueuePtr(),
        vectornav.Registers.BinaryOutputMeasurements(),
        vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch
    )
    csvExporter.start()
    time.sleep(1)

    while not (right_button.is_held and left_button.is_held):
        # press right button only => do a burst
        if right_button.is_pressed and not left_button.is_pressed:
            red.on()

            if right_button.is_pressed:
                # We'll create an Event so both child processes can start in sync.
                start_event = multiprocessing.Event()

                # Launch child processes, passing them the manager-based global buffers
                p0 = multiprocessing.Process(target=cap0, args=(start_event, dt))
                p1 = multiprocessing.Process(target=cap1, args=(start_event, dt))
                p0.start()
                p1.start()

                # Simultaneous start
                start_event.set()

                p0.join()
                p1.join()

            process_and_store(fdir_cam0, fdir_cam1)
            red.off()

        time.sleep(0.2)

    csvExporter.stop()
    s.disconnect()
    exit_standby(fname_log)

def cap0(start_event, dt):
    """
    Child process that captures from camera0 until the button is released.
    The image_buffer0 list is a global manager list, so the child can append to it
    and the parent can see the results.
    """
    cam0 = Picamera2(0)
    cam0.configure(config)
    cam0.start()

    # Wait for "go" signal from parent
    start_event.wait()

    # i = 0
    # while Button(18).is_pressed:
    for i in range(25):
        img0 = cam0.capture_array('main')
        tnow = time.monotonic_ns()
        filename0 = f"{tnow}_{i:05}"
        image_buffer0.append((img0, filename0))  ### manager list append
        # i += 1
        # Wait dt
        next_t = tnow + int(dt * 1e9)
        while time.monotonic_ns() < next_t:
            pass

    cam0.stop()
    cam0.close()

def cap1(start_event, dt):
    """
    Child process that captures from camera1 until the button is released.
    The image_buffer1 list is a global manager list, so the child can append to it
    and the parent can see the results.
    """
    
    cam1 = Picamera2(1)
    # cam1.configure(config)
    cam1.start()

    start_event.wait()

    # i = 0
    # while Button(18).is_pressed:
    for i in range(25):
        img1 = cam1.capture_array('main')
        tnow = time.monotonic_ns()
        filename1 = f"{tnow}_{i:05}"
        image_buffer1.append((img1, filename1))  ### manager list append
        # i += 1
        # Wait dt
        next_t = tnow + int(dt * 1e9)
        while time.monotonic_ns() < next_t:
            pass

    cam1.stop()
    cam1.close()

def write_images_to_sd(fdir_cam0, fdir_cam1):
    """Background function to write images to SD card."""
    while not write_queue.empty():
        try:
            img0, filename0 = write_queue.get(timeout=2)
            img1, filename1 = write_queue.get(timeout=2)

            filename0 = f"{fdir_cam0}0_{filename0}.jpg"
            filename1 = f"{fdir_cam1}1_{filename1}.jpg"

            # Convert to BGR for OpenCV
            img0 = cv2.cvtColor(img0, cv2.COLOR_RGB2BGR)
            img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2BGR)

            cv2.imwrite(filename0, img0)
            cv2.imwrite(filename1, img1)
            print(f"Saved {filename0} and {filename1}")
        except queue.Empty:
            break

def process_and_store(fdir_cam0, fdir_cam1):
    """
    Called in the parent process after the child burst completes.
    We move everything from the manager-based image_buffer0 and image_buffer1
    into the write_queue, then launch a background thread to write them to disk.
    """
    for i in range(len(image_buffer0)):
        write_queue.put(image_buffer0[i])
        write_queue.put(image_buffer1[i])

    # Start a writer thread
    thread = threading.Thread(target=write_images_to_sd, args=(fdir_cam0, fdir_cam1))
    thread.start()

    # Clear the manager lists for the next burst
    image_buffer0.clear()
    image_buffer1.clear()

############################ Initialization ############################
green = LED(12)
yellow = LED(16)
red = LED(24)
right_button = Button(18, hold_time=3)
left_button = Button(17, hold_time=3)

### CHANGED: we remove the local deque usage, and switch to Manager ###
manager = multiprocessing.Manager()
image_buffer0 = manager.list()  # shareable list
image_buffer1 = manager.list()
write_queue = queue.Queue()

try:
    gps_timeout = yaml.safe_load(open('../inputs.yaml', 'r'))['gps_timeout']
except (FileNotFoundError, yaml.YAMLError, KeyError) as exc:
    gps_timeout = 60

portName = '/dev/ttyUSB0'
config_vecnav(portName)

# Sync the clock. If sync fails, turn on all LEDs. Hold both buttons to retry.
while not sync_clock(portName, gps_timeout):
    [led.on() for led in (red, green, yellow)]
    while not (right_button.is_held and left_button.is_held):
        time.sleep(0.1)
    [led.off() for led in (red, green, yellow)]

fdir, fname_log = setup_logging()
inputs = read_inputs_yaml(fname_log)
dt = inputs['dt']

# Print initial IMU/GPS status
vecnav_status(portName, fname_log, gps_timeout)

global config, mode, standby, shooting_modes
shooting_modes = [inputs['shooting_mode0'],
                  inputs['shooting_mode1'],
                  inputs['shooting_mode2']]
mode = shooting_modes[0]  # 'auto'
# config = get_config(mode)

standby = False
tnow = time.time()
monitor_gps(portName)
tlast = time.time()
#######################################################################

try:
    while True:
        # Periodically blink GPS if needed
        if (time.time() - tlast > 10) and not standby:
            monitor_gps(portName)
            tlast = time.time()

        # Enter standby if right button is held
        if right_button.is_held and not standby and not left_button.is_pressed:
            standby = True
            enter_standby(fdir, fname_log, dt, mode, portName)

        time.sleep(0.2)

except Exception as e:
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        log.write(f"{tstr}: ERROR: {str(e)}\n")
        log.write("Traceback:\n")
        log.write(traceback.format_exc() + "\n")

finally:
    # Cleanup
    green.close()
    yellow.close()
    red.close()
    right_button.close()
    left_button.close()
    sys.exit(0)
