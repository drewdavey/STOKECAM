# Last updated: 2025-02-04
##################################
# This script allows the user to toggle through camera settings, launch standby mode, and capture images syncronously by holding right button.
# The user can also calibrate the cameras by holding the left button for more than 5 seconds.
##################################
import sys
import time
import vectornav
import threading
import traceback
from utils import *
from settings import *
from vectornav import *
from picamera2 import Picamera2
from gpiozero import Button, LED
from vectornav.Plugins import ExporterCsv
from datetime import datetime, timezone, timedelta

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


def toggle_modes():
    global cam0, cam1, config, mode, shooting_modes
    [led.blink(0.1, 0.1) for led in (red, green, yellow)]
    time.sleep(3)
    [led.off() for led in (red, green, yellow)]
    cam0.close(), cam1.close()                      # Close the cameras
    idx = shooting_modes.index(mode)                # Get the index of the current mode
    while not (right_button.is_held and left_button.is_held):
        if right_button.is_pressed and not left_button.is_pressed:
            idx = (idx + 1) % len(shooting_modes)
            mode = shooting_modes[idx]
        if mode == shooting_modes[0]:
            green.on(), yellow.off(), red.off()
        elif mode == shooting_modes[1]:
            yellow.on(), green.off(), red.off()
        elif mode == shooting_modes[2]:
            red.on(), green.off(), yellow.off()
        time.sleep(0.2)
    [led.off() for led in (red, green, yellow)]
    config = get_config(mode)                       # Get the configuration for the cameras
    cam0 = Picamera2(0)                             # Initialize cam0       
    cam1 = Picamera2(1)                             # Initialize cam1
    configure_cameras(fname_log, mode)              # Configure the cameras
    [led.blink(0.1, 0.1) for led in (red, green, yellow)]
    time.sleep(3)
    [led.off() for led in (red, green, yellow)]

def cap0(fdir_cam0, tnext, i):
    while time.monotonic_ns() < tnext:
        pass
    cam0.capture_file(f"{fdir_cam0}0_{str(time.monotonic_ns())}_{i+1:05}.jpg")

def cap1(fdir_cam1, tnext, i):
    while time.monotonic_ns() < tnext:
        pass
    cam1.capture_file(f"{fdir_cam1}1_{str(time.monotonic_ns())}_{i+1:05}.jpg")

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
    time.sleep(1)
    while not (right_button.is_held and left_button.is_held): # Hold both buttons for 3 seconds to exit standby
        if right_button.is_pressed and not left_button.is_pressed:  
            i = 0
            red.on()
            while right_button.is_pressed:
                tnow = time.monotonic_ns()
                tnext = tnow + int(dt * 1e9)  # Convert seconds to nanoseconds
                p0 = threading.Thread(target=cap0, args=[fdir_cam0, tnext, i])
                p1 = threading.Thread(target=cap1, args=[fdir_cam1, tnext, i])
                p0.start(), p1.start()
                p0.join(), p1.join()
                i += 1
            red.off()
        time.sleep(0.2)
    exit_standby(fname_log)

############################ Initialization ############################
green = LED(12)                         # Green LED
yellow = LED(16)                        # Yellow LED
red = LED(24)                           # Red LED
right_button = Button(18, hold_time=3)  # Right button
left_button = Button(17, hold_time=3)   # Left button

portName = '/dev/ttyUSB0'                 # Default port for VN-200
config_vecnav(portName)                   # Config VN-200 output           

fdir = '/home/drew/testing_drew/'
fname_log = 'log.txt'
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
            monitor_gps(portName)
            tlast = time.time()
        if right_button.is_held and not standby and not left_button.is_pressed:
            standby = True
            enter_standby(fdir, fname_log, dt, mode, portName)    
        if (right_button.is_held and left_button.is_held) and not standby:
            [led.on() for led in (red, green, yellow)]
            left_button.wait_for_release()
            time.sleep(1)
            if right_button.is_held:
                break
            else:
                toggle_modes()
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