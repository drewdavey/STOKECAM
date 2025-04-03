# Last updated: 2025-04-01
##################################
# This script allows the user to toggle through camera settings, launch standby mode, 
# and capture images synchronously by holding right button.
# The user can also calibrate the cameras by holding the left button for more than 5 seconds.
##################################
import os
os.environ["LIBCAMERA_RPI_CONFIG_FILE"] = "../STOKECAM.yaml"
import sys
import cv2
import time
import queue
import vectornav
import traceback
import threading
import subprocess
from utils import *
from vectornav import *
from collections import deque
from picamera2 import Picamera2
from datetime import datetime, timezone
from vectornav.Plugins import ExporterCsv
from gpiozero import Button, LED, DigitalOutputDevice

def set_trigger_mode(enable, fname_log):
    """
    Enables or disables external trigger mode by writing 1 or 0
    to /sys/module/imx296/parameters/trigger_mode.
    Requires 'sudo' privileges or that master.py is run as root.
    """
    log = open(fname_log, 'a')
    val = "1" if enable else "0"
    cmd = f"sudo sh -c 'echo {val} > /sys/module/imx296/parameters/trigger_mode'"
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log.write(f"{tstr}:     [INFO] Setting IMX296 trigger_mode to: {val}\n")
    try:
        subprocess.run(cmd, shell=True, check=True)
        log.write(f"{tstr}:     [INFO] Successfully set trigger mode.\n\n")
    except subprocess.CalledProcessError as e:
        log.write(f"{tstr}:     [ERROR] Failed to set trigger mode: {e}\n\n")
    log.close()

def configure_cameras(fname_log, mode, exposure_us):
    """
    Configures the cameras with the specified mode and exposure time.
    The cameras are initialized and started, and their configurations are logged.
    """
    global cam0, cam1
    # Create the camera config for that default mode
    config = get_config(mode, exposure_us) 
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Configuring cameras to {mode} mode...\n")
    cam0 = Picamera2(0)                             # Initialize cam0
    cam1 = Picamera2(1)                             # Initialize cam1
    for idx, cam in enumerate([cam0, cam1]):
        cam.configure(config)
        cam.start()
        log.write(f"{tstr}:     cam{idx} configuration: {cam.camera_configuration()}\n")
        # log.write(f"{tstr}:     cam{idx} metadata: {cam.capture_metadata()}\n")
    log.write('\n'), log.close()

def calib(fdir, fname_log, calib_dt, calib_frames, mode, portName, exposure):
    """Collect set of calibration images with indicator lights."""
    [led.on() for led in (red, green, yellow)]
    time.sleep(5)
    [led.off() for led in (red, green, yellow)]
    fdir_out, fdir_cam0, fdir_cam1 = create_dirs(fdir, f"calib_{mode}")
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     calibration_{mode} session: {fdir_out}\n"), log.close()
    s = Sensor() # Create sensor object and connect to the VN-200 
    csvExporter = ExporterCsv(fdir_out, True)
    s.autoConnect(portName)
    s.subscribeToMessage(csvExporter.getQueuePtr(), vectornav.Registers.BinaryOutputMeasurements(), vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch)
    csvExporter.start()
    for i in range(int(calib_frames)):
        green.on(), time.sleep(0.5)
        yellow.on(), time.sleep(0.5)
        red.on(), time.sleep(0.5)
        [led.blink(0.5,0.5) for led in (red, green, yellow)], time.sleep(3)
        [led.on() for led in (red, green, yellow)], time.sleep(1)
        t1 = time.monotonic_ns()  # Before exposure
        pulse_trigger(exposure)
        t2 = time.monotonic_ns()  # After exposure
        timestamp = round((t1 + t2) / 2) # Average timestamp  
        # Capture images and store them in the circular buffer
        filename = f"{timestamp}_{i+1:05}"
        img0 = cam0.capture_array('main')  # Capture cam0
        img1 = cam1.capture_array('main')  # Capture cam1
        image_buffer0.append((img0, filename))
        image_buffer1.append((img1, filename))
        [led.off() for led in (red, green, yellow)]
        while time.monotonic_ns() < (t2 + calib_dt): # Wait for remainder of dt
            pass
    process_and_store(fdir_cam0, fdir_cam1)
    csvExporter.stop()
    s.disconnect()

def monitor_gps(portName):
    """Monitor GPS status and blink the green LED based on the fix type."""
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
    """Toggle between shooting modes and configure the cameras accordingly."""
    global cam0, cam1, mode, exposure, dt
    [led.blink(0.1, 0.1) for led in (red, green, yellow)]
    time.sleep(3)
    [led.off() for led in (red, green, yellow)]
    cam0.close(), cam1.close()                      # Close the cameras
    idx = shooting_modes.index(mode)                # Get the index of the current mode
    while not (right_button.is_held and left_button.is_held):
        if right_button.is_pressed and not left_button.is_pressed:
            idx = (idx + 1) % len(shooting_modes)
            mode = shooting_modes[idx]
            exposure_us = exposure_times[idx]
        if mode == shooting_modes[0]:
            green.on(), yellow.off(), red.off()
        elif mode == shooting_modes[1]:
            yellow.on(), green.off(), red.off()
        elif mode == shooting_modes[2]:
            red.on(), green.off(), yellow.off()
        time.sleep(0.2)
    [led.off() for led in (red, green, yellow)]
    exposure, dt = calc_dt(frame_rate, exposure_us)   # Calculate dt
    configure_cameras(fname_log, mode, exposure_us)   # Configure the cameras
    [led.blink(0.1, 0.1) for led in (red, green, yellow)]
    time.sleep(3)
    [led.off() for led in (red, green, yellow)]

def enter_standby(fdir, fname_log, mode, portName, exposure, dt):
    """Enter standby mode to capture images with external trigger."""
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
                timestamp = round((t1 + t2) / 2) # Average timestamp  
                # Capture images and store them in the circular buffer
                filename = f"{timestamp}_{i:05}"
                img0 = cam0.capture_array('main')  # Capture cam0
                img1 = cam1.capture_array('main')  # Capture cam1
                image_buffer0.append((img0, filename))
                image_buffer1.append((img1, filename))
                i += 1
                while time.monotonic_ns() < (t2 + dt): # Wait for remainder of dt
                    pass
            process_and_store(fdir_cam0, fdir_cam1)
            red.off()
        time.sleep(0.2)
    csvExporter.stop()
    s.disconnect()
    exit_standby(fname_log)

def pulse_trigger(exposure):
    """Pulses the trigger pin to generate a frame."""
    trigger.off()
    time.sleep(exposure)      # Exposure time
    trigger.on()

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

def write_images_to_sd(fdir_cam0, fdir_cam1):
    """Background process to write images to SD card."""
    while not write_queue.empty():
        try:
            img0, filename0 = write_queue.get(timeout=2)
            img1, filename1 = write_queue.get(timeout=2)
            filename0 = f"{fdir_cam0}0_{filename0}.jpg"
            filename1 = f"{fdir_cam1}1_{filename1}.jpg"
            cv2.imwrite(filename0, img0)  # Save images
            cv2.imwrite(filename1, img1)
        except queue.Empty:
            break

def exit_standby(fname_log):
    """Exit standby mode and turn off the LEDs."""
    global standby
    yellow.off(), red.off() # Close the lights
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Exiting standby.\n\n"), log.close()
    time.sleep(1)
    standby = False

############################ Initialization ############################
green = LED(12)                         # Green LED
yellow = LED(16)                        # Yellow LED
red = LED(24)                           # Red LED
right_button = Button(18, hold_time=3)  # Right button
left_button = Button(17, hold_time=3)   # Left button
trigger_pin = 26                        # Hardware trigger
trigger = DigitalOutputDevice(trigger_pin, active_high=True, initial_value=True)

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

##### Sync the clock. If sync fails, turn on all LEDs. #####
# Hold right button only to try/retry syncing the clock.
# Hold left button only to continue (if clock is synced but no GPS signal).
[led.on() for led in (red, green, yellow)]
while True:
    if right_button.is_held and not left_button.is_pressed:
        [led.blink(0.5,0.5) for led in (red, green, yellow)]
        if sync_clock(portName, gps_timeout):
            [led.off() for led in (red, green, yellow)]
            break   # Successful sync
        else:
            [led.on() for led in (red, green, yellow)]
            pass # Sync failed, remain in this loop to try again or skip
    if left_button.is_held and not right_button.is_pressed:
        [led.off() for led in (red, green, yellow)]
        gps_timeout = 3 # Don't wait for GPS fix in status check
        break
    time.sleep(0.1)

# Setup log file and directories now that clock is synced
fdir, fname_log = setup_logging()       

# Get IMU/GPS status. Print initial values to log.
vecnav_status(portName, fname_log, gps_timeout)

# Disable IMX 296 external trigger mode for auto exposure
set_trigger_mode(False, fname_log)

# Write exposure times to inputs.yaml
write_inputs_yaml(fname_log)

# Enable IMX 296 external trigger mode
set_trigger_mode(True, fname_log)

# Initialize and configure cameras 
global cam0, cam1, mode, standby, exposure, dt
frame_rate, calib_dt, calib_frames, shooting_modes, exposure_times = parse_inputs(fname_log)
mode = shooting_modes[0]                        # Default mode
exposure_us = exposure_times[0]                 # Default exposure time
configure_cameras(fname_log, mode, exposure_us) # Configure the cameras
exposure, dt = calc_dt(frame_rate, exposure_us) # Calculate dt

standby = False         # Flag to indicate standby mode 
monitor_gps(portName)   # Monitor GPS status
tlast = time.time()     # Last time GPS was checked
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
        if left_button.is_held and not standby and not right_button.is_pressed:
            calib(fdir, fname_log, calib_dt, calib_frames, mode, portName, exposure)
            monitor_gps(portName) 
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
    set_trigger_mode(False, fname_log)         # Disable external trigger mode 
    
    time.sleep(3)
    subprocess.run(["python", "OLDmaster.py"])
    
    sys.exit(0)
    #######################################################################

