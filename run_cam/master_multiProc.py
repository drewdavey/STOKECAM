# Last updated: 2025-02-04
##################################
# This script allows the user to toggle through camera settings, launch standby mode, and capture images syncronously by holding right button.
# The user can also calibrate the cameras by holding the left button for more than 5 seconds.
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
import multiprocessing
from collections import deque
from picamera2 import Picamera2
from gpiozero import Button, LED
from vectornav.Plugins import ExporterCsv
from datetime import datetime, timezone, timedelta

def monitor_gps(portName):
    s = Sensor() # Create sensor object and connect to the VN-200 
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
    yellow.off(), red.off() # Close the lights
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Exiting standby.\n\n"), log.close()
    time.sleep(1)
    standby = False

def enter_standby(fdir, fname_log, dt, mode, portName):
    yellow.on()
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Entering standby... \n\n"), log.close()
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"session_{mode}")
    s = Sensor() # Create sensor object and connect to the VN-200
    csvExporter = ExporterCsv(fdir_out, True)
    s.autoConnect(portName)
    s.subscribeToMessage(csvExporter.getQueuePtr(), vectornav.Registers.BinaryOutputMeasurements(), vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch)
    csvExporter.start()
    time.sleep(1)
    while not (right_button.is_held and left_button.is_held): # Hold both buttons for 3 seconds to exit standby
        if right_button.is_pressed and not left_button.is_pressed:  
            red.on()
            if right_button.is_pressed:
                tstart = time.monotonic_ns() + 1e9 
                p0 = multiprocessing.Process(target=cap0, args=[tstart, dt])
                p1 = multiprocessing.Process(target=cap1, args=[tstart, dt])
                p0.start(), p1.start()
                p0.join(), p1.join()
            process_and_store(fdir_cam0, fdir_cam1)
            red.off()
        time.sleep(0.2)
    csvExporter.stop()
    s.disconnect()
    exit_standby(fname_log)

def cap0(tstart, dt):
    cam0 = Picamera2(0)                             # Initialize cam0       
    cam0.configure(config)
    cam0.start()
    while time.monotonic_ns() < tstart:
        pass
    for i in range(25):
        img0 = cam0.capture_array('main')  # Capture cam0
        tnow = time.monotonic_ns()
        filename0 = f"{tnow}_{i:05}"
        image_buffer0.append((img0, filename0))
        while time.monotonic_ns() < tnow + int(dt * 1e9):
            pass

def cap1(tstart, dt):
    cam1 = Picamera2(1)                             # Initialize cam1
    cam1.configure(config)
    cam1.start()
    while time.monotonic_ns() < tstart:
        pass
    for i in range(25):
        img1 = cam1.capture_array('main')  # Capture cam1
        tnow = time.monotonic_ns()
        filename1 = f"{tnow}_{i:05}"
        image_buffer1.append((img1, filename1))
        while time.monotonic_ns() < tnow + int(dt * 1e9):
            pass

def write_images_to_sd(fdir_cam0, fdir_cam1):
    """Background process to write images to SD card."""
    while not write_queue.empty():
        try:
            img0, filename0 = write_queue.get(timeout=2)
            img1, filename1 = write_queue.get(timeout=2)
            filename0 = f"{fdir_cam0}0_{filename0}.jpg"
            filename1 = f"{fdir_cam1}1_{filename1}.jpg"
            # Convert RGB to BGR for OpenCV
            img0 = cv2.cvtColor(img0, cv2.COLOR_RGB2BGR)
            img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename0, img0)  # Save images
            cv2.imwrite(filename1, img1)
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
    # Clear out the buffers so the next burst starts fresh
    image_buffer0.clear()
    image_buffer1.clear()

############################ Initialization ############################
green = LED(12)                         # Green LED
yellow = LED(16)                        # Yellow LED
red = LED(24)                           # Red LED
right_button = Button(18, hold_time=3)  # Right button
left_button = Button(17, hold_time=3)   # Left button

# Circular buffer and queue setup
buffer_size = 1000  # Store last 100 images in memory
image_buffer0 = deque(maxlen=buffer_size)
image_buffer1 = deque(maxlen=buffer_size)
write_queue = queue.Queue()

try:
    gps_timeout = yaml.safe_load(open('../inputs.yaml', 'r'))['gps_timeout']
except (FileNotFoundError, yaml.YAMLError, KeyError) as exc:
    gps_timeout = 60

portName = '/dev/ttyUSB0'                 # Default port for VN-200
config_vecnav(portName)                   # Config VN-200 output           

# Sync the clock. If sync fails, turn on all LEDs. Hold both buttons to retry.
while not sync_clock(portName, gps_timeout):  
    [led.on() for led in (red, green, yellow)]  
    while not (right_button.is_held and left_button.is_held):
        time.sleep(0.1)
    [led.off() for led in (red, green, yellow)]

fdir, fname_log = setup_logging()               # Setup logging
inputs = read_inputs_yaml(fname_log)            # Read inputs from inputs.yaml
dt = inputs['dt']

# Get IMU/GPS status. Print initial values to log.
vecnav_status(portName, fname_log, gps_timeout)  

global cam0, cam1, config, mode, standby, shooting_modes
shooting_modes = [inputs['shooting_mode0'], inputs['shooting_mode1'], inputs['shooting_mode2']]
mode = shooting_modes[0]                        # Default to 'auto'
config = get_config(mode)                       # Get the configuration for the cameras

standby = False
tnow = time.time()
monitor_gps(portName)
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
            monitor_gps(portName)
            tlast = time.time()
        if right_button.is_held and not standby and not left_button.is_pressed:
            standby = True
            enter_standby(fdir, fname_log, dt, mode, portName)    
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