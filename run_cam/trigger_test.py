import sys
import time
import cv2
import vectornav
import traceback
import threading
import queue
import multiprocessing
import RPi.GPIO as GPIO
from collections import deque
from datetime import datetime, timezone
import subprocess
import os
from utils import *
from settings import *
from vectornav import *
from picamera2 import Picamera2
from gpiozero import Button, LED
from vectornav.Plugins import ExporterCsv

###################### HARDWARE TRIGGER ADDITIONS ######################
# Example subdev device indices - adjust if necessary
TRIGGER_SUBDEV_0 = "/dev/v4l-subdev0"
TRIGGER_SUBDEV_1 = "/dev/v4l-subdev1"

# GPIO pin to pulse the hardware trigger line
triggerPin = 26

# Wrapper to run shell commands
def run_cmd(cmd):
    print(f"[Shell] {cmd}")
    try:
        subprocess.run(
            cmd,
            universal_newlines=True,
            check=False,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except RuntimeError as e:
        print(f"[Error] {e}")
    except:
        print("[Error] Unknown setup error running:", cmd)

# Enable or disable hardware trigger mode on both cameras
def set_trigger_mode(enable=True):
    """Sets hardware trigger mode on or off via v4l2-ctl."""
    mode_value = 1 if enable else 0
    run_cmd(f"v4l2-ctl -d {TRIGGER_SUBDEV_0} -c trigger_mode={mode_value}")
    run_cmd(f"v4l2-ctl -d {TRIGGER_SUBDEV_1} -c trigger_mode={mode_value}")

# Pulse the trigger pin briefly
def pulse_trigger():
    GPIO.output(triggerPin, GPIO.HIGH)
    time.sleep(0.001)  # ~1ms pulse
    GPIO.output(triggerPin, GPIO.LOW)

###################### END HARDWARE TRIGGER ADDITIONS ######################


######################### ORIGINAL UTILS & FUNCTIONS #######################
# (Include your existing utility funcs from your script, e.g.:
#  create_dirs, config_vecnav, vecnav_status, read_inputs_yaml, etc.
#  Here we show placeholders to illustrate structure.)

def configure_cameras(fname_log, mode):
    global cam0, cam1, config 
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        log.write(f"{tstr}:     Configuring cameras to {mode} mode...\n")

        for idx, cam in enumerate([cam0, cam1]):
            cam.configure(config)
            cam.start()  # We'll still start them initially
            log.write(f"{tstr}:     cam{idx} config: {cam.camera_configuration()}\n")
            log.write(f"{tstr}:     cam{idx} metadata: {cam.capture_metadata()}\n")
        log.write('\n')

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

def calib(fdir, fname_log, calib_dt, calib_frames, mode, portName):
    [led.on() for led in (red, green, yellow)]
    time.sleep(5)
    [led.off() for led in (red, green, yellow)]
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"calib_{mode}")
    log = open(fname_log, 'a')
    tnow = datetime.now(timezone.utc)
    tstr = tnow.strftime('%H%M%S%f')
    log.write(f"{tstr}:     calibration_{mode} session: {fdir_out}\n"), log.close()

    s = Sensor()  # Create sensor object and connect to the VN-200 
    csvExporter = ExporterCsv(fdir_out, True)
    s.autoConnect(portName)
    s.subscribeToMessage(csvExporter.getQueuePtr(), vectornav.Registers.BinaryOutputMeasurements(), vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch)
    csvExporter.start()

    for i in range(int(calib_frames)):
        green.on(), time.sleep(0.5)
        yellow.on(), time.sleep(0.5)
        red.on(), time.sleep(0.5)
        [led.on() for led in (red, green, yellow)]
        tnow = time.monotonic_ns()
        tnext = tnow + int(calib_dt * 1e9)  # Convert seconds to nanoseconds
        p0 = threading.Thread(target=cap0, args=(tnext, i))
        p1 = threading.Thread(target=cap1, args=(tnext, i))
        p0.start(), p1.start()
        p0.join(), p1.join()

        [led.off() for led in (red, green, yellow)]
        time.sleep(calib_dt)
    process_and_store(fdir_cam0, fdir_cam1)
    csvExporter.stop()
    s.disconnect()

def write_images_to_sd(fdir_cam0, fdir_cam1):
    """Background process to write images to SD card."""
    while not write_queue.empty():
        try:
            (img0, filename0, meta0), (img1, filename1, meta1) = write_queue.get(timeout=2), write_queue.get(timeout=2)
            # Save images
            filename0 = f"{fdir_cam0}0_{filename0}.jpg"
            filename1 = f"{fdir_cam1}1_{filename1}.jpg"

            # Convert RGB->BGR for OpenCV if needed
            img0 = cv2.cvtColor(img0, cv2.COLOR_RGB2BGR)
            img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2BGR)

            cv2.imwrite(filename0, img0)
            cv2.imwrite(filename1, img1)

            # Example: also log metadata if wanted
            meta_path_0 = f"{fdir_cam0}0_{filename0}_meta.txt"
            meta_path_1 = f"{fdir_cam1}1_{filename1}_meta.txt"
            with open(meta_path_0, 'w') as m0:
                m0.write(str(meta0))
            with open(meta_path_1, 'w') as m1:
                m1.write(str(meta1))

            print(f"Saved {filename0}, {filename1}")
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

def cap0(i):
    # Wait for a frame from cam0
    # Then capture array
    img0 = cam0.capture_array('main', wait=False)
    filename0 = f"{time.monotonic_ns()}_{i:05}"
    meta0 = cam0.capture_metadata()  # Or you can do it before capture_array
    image_buffer0.append((img0, filename0, meta0))

def cap1(i):
    img1 = cam1.capture_array('main', wait=False)
    filename1 = f"{time.monotonic_ns()}_{i:05}"
    meta1 = cam1.capture_metadata()
    image_buffer1.append((img1, filename1, meta1))

def exit_standby(fname_log):
    global standby
    yellow.off(), red.off()  # Turn off lights
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        log.write(f"{tstr}:     Exiting standby.\n\n")
    time.sleep(1)
    standby = False

def enter_standby(fdir, fname_log, dt, mode, portName):
    """
    Called when right button is held to go into standby:
      - Start camera previews
      - Enable hardware trigger
      - While right button is pressed, pulse trigger + capture frames
      - On release, disable trigger + save images
    """
    global standby
    yellow.on()
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        log.write(f"{tstr}:     Entering standby... \n\n")

    # Create session directories, start logging IMU, etc.
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"session_{mode}")
    s = Sensor()
    csvExporter = ExporterCsv(fdir_out, True)
    s.autoConnect(portName)
    s.subscribeToMessage(csvExporter.getQueuePtr(), vectornav.Registers.BinaryOutputMeasurements(),
                         vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch)
    csvExporter.start()

    # Start both camera previews (if not already started):
    #  Some cameras can remain started from configure_cameras()
    #  But ensure they're definitely running:
    cam0.start()
    cam1.start()

    # Enable hardware trigger mode
    set_trigger_mode(True)
    time.sleep(1)  # short delay to ensure cameras are in trigger mode

    # MAIN capture loop in standby
    while not (right_button.is_held and left_button.is_held):
        # If only right is pressed, we do continuous triggered captures
        if right_button.is_pressed and not left_button.is_pressed:
            red.on()
            i = 1
            while right_button.is_pressed:
                # Pulse the external trigger
                pulse_trigger()

                # Give cameras a short moment to expose & produce frames
                # The exact wait depends on your sensor's exposure or framerate
                time.sleep(0.03)  

                # Capture from both cameras
                p0 = threading.Thread(target=cap0, args=(i,))
                p1 = threading.Thread(target=cap1, args=(i,))
                p0.start(), p1.start()
                p0.join(), p1.join()

                i += 1

            # Once right button is released, flush images to disk
            process_and_store(fdir_cam0, fdir_cam1)
            red.off()

        time.sleep(0.2)

    # Disable hardware trigger before exiting standby
    set_trigger_mode(False)

    csvExporter.stop()
    s.disconnect()
    exit_standby(fname_log)

########################### MAIN SCRIPT FLOW ############################

# Setup your LEDs and Buttons
green = LED(12)
yellow = LED(16)
red = LED(24)
right_button = Button(18, hold_time=3)
left_button = Button(17, hold_time=3)

# Setup the GPIO for the hardware trigger pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(triggerPin, GPIO.OUT, initial=GPIO.LOW)

# Buffers for images
buffer_size = 1000
image_buffer0 = deque(maxlen=buffer_size)
image_buffer1 = deque(maxlen=buffer_size)
write_queue = queue.Queue()

# ... your existing code to read inputs.yaml, config VN-200, etc. ...
# Example placeholders:
gps_timeout = 60
portName = '/dev/ttyUSB0'
config_vecnav(portName)
sync_clock(portName, gps_timeout)
fdir, fname_log = setup_logging()
inputs = read_inputs_yaml(fname_log)

dt = inputs['dt']
calib_dt = inputs['calib_dt']
calib_frames = inputs['calib_frames']

# Set up & print initial VecNav status
vecnav_status(portName, fname_log, gps_timeout)

global cam0, cam1, config, mode, standby, shooting_modes
shooting_modes = [inputs['shooting_mode0'], inputs['shooting_mode1'], inputs['shooting_mode2']]
mode = shooting_modes[0]
config = get_config(mode)
cam0 = Picamera2(0)
cam1 = Picamera2(1)

# Configure cameras once at start
configure_cameras(fname_log, mode)

standby = False
tnow = time.time()
monitor_gps(portName)  # your function for blinking LED by GPS fix
tlast = time.time()

try:
    while True:
        if (time.time() - tlast > 10) and not standby:
            monitor_gps(portName)
            tlast = time.time()

        # If only right is held for 3 sec -> enter standby with hardware trigger
        if right_button.is_held and not standby and not left_button.is_pressed:
            standby = True
            enter_standby(fdir, fname_log, dt, mode, portName)

        # If only left is held for 3 sec -> calibrate
        if left_button.is_held and not standby and not right_button.is_pressed:
            calib(fdir, fname_log, calib_dt, calib_frames, mode, portName)
            monitor_gps(portName)

        # Both held for 3 sec -> either break or toggle modes
        if (right_button.is_held and left_button.is_held) and not standby:
            [led.on() for led in (red, green, yellow)]
            left_button.wait_for_release()
            time.sleep(1)
            if right_button.is_held:
                # Exits the script
                break
            else:
                # Toggle modes
                toggle_modes()
                monitor_gps(portName)

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
    GPIO.cleanup()  # clean up GPIO pins
    sys.exit(0)
