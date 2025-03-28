# Last updated: 2025-02-04
##################################
# This script allows the user to toggle through camera settings, launch standby mode, 
# and capture images synchronously by holding right button.
# The user can also calibrate the cameras by holding the left button for more than 5 seconds.
##################################
import os
os.environ["LIBCAMERA_RPI_CONFIG_FILE"] = "/usr/local/share/libcamera/pipeline/rpi/pisp/example.yaml"
# os.environ["LIBCAMERA_LOG_LEVEL"] = "ERROR"  # Set log level to ERROR to suppress warnings
import sys
import cv2
import time
import queue
import vectornav
import traceback
import threading
import subprocess
from utils import *
from settings import *
from vectornav import *
from collections import deque
from picamera2 import Picamera2
from datetime import datetime, timezone
from vectornav.Plugins import ExporterCsv
from gpiozero import Button, LED, DigitalOutputDevice

def set_trigger_mode(enable: bool = True):
    """
    Enables or disables external trigger mode by writing 1 or 0
    to /sys/module/imx296/parameters/trigger_mode.
    Requires 'sudo' privileges or that the Python script is run as root.
    """
    val = "1" if enable else "0"
    cmd = f"sudo sh -c 'echo {val} > /sys/module/imx296/parameters/trigger_mode'"
    print(f"[INFO] Setting IMX296 trigger_mode to: {val}")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("[INFO] Successfully set trigger mode.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to set trigger mode: {e}")

def configure_cameras(fname_log, mode):
    global cam0, cam1, config 
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Configuring cameras to {mode} mode...\n")
    for idx, cam in enumerate([cam0, cam1]):
        cam.configure(config)
        cam.start()
        log.write(f"{tstr}:     cam{idx} configuration: {cam.camera_configuration()}\n")
        # log.write(f"{tstr}:     cam{idx} metadata: {cam.capture_metadata()}\n")
    log.write('\n'), log.close()

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

def pulse_trigger(exposure):
    """Pulses the trigger pin to generate a frame."""
    trigger.off()
    time.sleep(exposure)      # Exposure time
    trigger.on()

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

def exit_standby(fname_log):
    global standby
    yellow.off(), red.off() # Close the lights
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Exiting standby.\n\n"), log.close()
    time.sleep(1)
    standby = False

def enter_standby(fdir, fname_log, mode, portName, exposure, dt):
    yellow.on()
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Entering standby... \n\n"), log.close()
    fdir_out, fdir_cam0, fdir_cam1 = create_dirs(fdir, f"session_{mode}")
    s = Sensor()  # Create sensor object and connect to the VN-200
    csvExporter = ExporterCsv(fdir_out, True)
    s.autoConnect(portName)
    s.subscribeToMessage(csvExporter.getQueuePtr(), vectornav.Registers.BinaryOutputMeasurements(), vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch)
    csvExporter.start()
    time.sleep(1)

    while not (right_button.is_held and left_button.is_held):  # Hold both buttons for 3 seconds to exit standby
        if right_button.is_pressed and not left_button.is_pressed:  
            i = 1
            red.on()
            while right_button.is_pressed:
                t1 = time.monotonic_ns()  # Before exposure
                pulse_trigger(exposure)
                t2 = time.monotonic_ns()  # After exposure
                timestamp = (t1 + t2) / 2 # Average timestamp  

                # Capture images and save them to the SD card
                cam0.capture_file(f"{fdir_cam0}0_{timestamp}_{i:05}.jpg")
                cam1.capture_file(f"{fdir_cam1}1_{timestamp}_{i:05}.jpg")

                # Capture images and store them in the circular buffer
                # filename = f"{timestamp}_{i:05}"
                # img0 = cam0.capture_array('main')  # Capture cam0
                # img1 = cam1.capture_array('main')  # Capture cam1
                # image_buffer0.append((img0, filename))
                # image_buffer1.append((img1, filename))
                
                i += 1
                while time.monotonic_ns() < (t2 + dt): # Wait for remainder of dt
                    pass
            # process_and_store(fdir_cam0, fdir_cam1)
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
trigger_pin = 26                        # Hardware trigger
trigger = DigitalOutputDevice(trigger_pin, active_high=True, initial_value=True)

# Enable external trigger mode
set_trigger_mode(True)

# Circular buffer and queue setup
buffer_size = 1000  # Store last 100 images in memory
image_buffer0 = deque(maxlen=buffer_size)
image_buffer1 = deque(maxlen=buffer_size)
write_queue = queue.Queue()

try: # Get gps_timeout for syncing the clock
    gps_timeout = yaml.safe_load(open('../inputs.yaml', 'r'))['gps_timeout']
except (FileNotFoundError, yaml.YAMLError, KeyError) as exc:
    gps_timeout = 60
portName = '/dev/ttyUSB0'                 # Default port for VN-200
config_vecnav(portName)                   # Config VN-200 output           
# # Sync the clock. If sync fails, turn on all LEDs. Hold both buttons to retry.
# while not sync_clock(portName, gps_timeout):  
#     [led.on() for led in (red, green, yellow)]  
#     while not (right_button.is_held and left_button.is_held):
#         time.sleep(0.1)
#     [led.off() for led in (red, green, yellow)]
fdir, fname_log = setup_logging()       # Setup logging

# Read camera parameters inputs.yaml 
inputs = read_inputs_yaml(fname_log)    
# calib_dt = inputs['calib_dt']
# calib_frames = inputs['calib_frames']

frame_rate = inputs['fps']              # Frame rate in Hz
frame_period = 1 / frame_rate           # e.g. 0.04 sec
exposure_ms = 1                         # Exposure time in milliseconds
exposure_sec = exposure_ms / 1e3        # Exposure time in seconds
latency = 14.26 / 1e6                   # Latency in seconds
exposure = exposure_sec - latency       # True exposure time in seconds
dt = (frame_period - exposure) * 1e9    # Time to wait before triggering the next frame

# # Get IMU/GPS status. Print initial values to log.
# vecnav_status(portName, fname_log, gps_timeout)

global cam0, cam1, config, mode, standby, shooting_modes
shooting_modes = [inputs['shooting_mode0'], inputs['shooting_mode1'], inputs['shooting_mode2']]
mode = shooting_modes[0]                        # Default to 'auto'
config = get_config(mode)                       # Get the configuration for the cameras
cam0 = Picamera2(0)                             # Initialize cam0       
cam1 = Picamera2(1)                             # Initialize cam1
configure_cameras(fname_log, mode)              # Configure the cameras

# Pulse trigger to generate initial frames
for _ in range(10):
    pulse_trigger(0.01)
    time.sleep(0.01)

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
    #     - release both to toggle modes
    #     - release left ONLY to exit script
    while True:
        if (time.time() - tlast > 10) and not standby:
            monitor_gps(portName)
            tlast = time.time()
        if right_button.is_held and not standby and not left_button.is_pressed:
            standby = True
            enter_standby(fdir, fname_log, mode, portName, exposure, dt)    
        if (right_button.is_held and left_button.is_held) and not standby:
            [led.on() for led in (red, green, yellow)]
            left_button.wait_for_release()
            time.sleep(1)
            if right_button.is_held:
                break
            else:
                toggle_modes()
                monitor_gps(portName)
        time.sleep(0.2)

except Exception as e:
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        log.write(f"{tstr}: ERROR: {str(e)}\n")
        log.write("Traceback:\n")
        log.write(traceback.format_exc() + "\n")  # Log the traceback

finally:
    ############################## Cleanup ###############################
    cam0.stop(), cam1.stop()                   # Stop the cameras
    cam0.close(), cam1.close()                 # Close the cameras
    green.close(), yellow.close(), red.close() # Close the LEDs
    right_button.close(), left_button.close()  # Close the buttons
    trigger.close()                            # Close the trigger pin
    set_trigger_mode(False)                    # Disable external trigger mode 
    sys.exit(0)
    #####################################################################

