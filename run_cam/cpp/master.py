# Last updated: 2025-02-04
##################################
# This script allows the user to toggle through camera settings, launch standby mode, and capture images syncronously by holding right button.
# The user can also calibrate the cameras by holding the left button for more than 5 seconds.
##################################
import sys
import time
import vectornav
import subprocess
import traceback
from utils import *
from vectornav import *
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

def capture_in_parallel(num_frames, fdir_cam0, fdir_cam1):
    subprocess.run([
        "./dual_capture",
        str(num_frames),
        fdir_cam0,
        fdir_cam1
    ])

def exit_standby(fname_log):
    global standby
    yellow.off(), red.off() # Close the lights
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Exiting standby.\n\n"), log.close()
    time.sleep(1)
    standby = False

def enter_standby(fdir, fname_log, dt, portName):
    yellow.on()
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Entering standby... \n\n"), log.close()
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"session_C_sub")
    s = Sensor() # Create sensor object and connect to the VN-200
    csvExporter = ExporterCsv(fdir_out, True)
    s.autoConnect(portName)
    s.subscribeToMessage(csvExporter.getQueuePtr(), vectornav.Registers.BinaryOutputMeasurements(), vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch)
    csvExporter.start()
    time.sleep(1)
    while not (right_button.is_held and left_button.is_held): # Hold both buttons for 3 seconds to exit standby
        if right_button.is_pressed and not left_button.is_pressed:  
            red.on()
            capture_in_parallel(100, fdir_cam0, fdir_cam1)
            red.off()
        time.sleep(0.2)
    csvExporter.stop()
    s.disconnect()
    exit_standby(fname_log)

############################ Initialization ############################
green = LED(12)                         # Green LED
yellow = LED(16)                        # Yellow LED
red = LED(24)                           # Red LED
right_button = Button(18, hold_time=3)  # Right button
left_button = Button(17, hold_time=3)   # Left button

try:
    gps_timeout = yaml.safe_load(open('inputs.yaml', 'r'))['gps_timeout']
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
            enter_standby(fdir, fname_log, dt, portName)    
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