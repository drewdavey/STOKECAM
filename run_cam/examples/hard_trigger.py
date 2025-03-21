import pigpio
import time
import threading
import queue
import cv2
import subprocess
from picamera2 import Picamera2
from datetime import datetime

# ------------------------------
# CONFIG & CONSTANTS
# ------------------------------
TRIGGER_PIN      = 26  # Physical pin to the GS camera XTR lines
RIGHT_BUTTON_PIN = 18  # Press to start captures
LEFT_BUTTON_PIN  = 17  # Press to exit or other functionality
LED_PIN          = 24  # Optional LED to indicate capturing

# If you want to set the driver to external trigger mode from Python:
IMX296_TRIGGER_PARAM = "/sys/module/imx296/parameters/trigger_mode"

# Filenames / directories to store images
CAM0_DIR = "./cam0"
CAM1_DIR = "./cam1"

# ------------------------------
# SET TRIGGER MODE (OPTIONAL)
# ------------------------------
def set_trigger_mode(enable=True):
    """
    Enables (echo 1) or disables (echo 0) external trigger mode 
    for IMX296-based GS cameras. Requires root (sudo).
    """
    val = "1" if enable else "0"
    cmd = f"sudo sh -c 'echo {val} > {IMX296_TRIGGER_PARAM}'"
    print(f"[set_trigger_mode] Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("[set_trigger_mode] Successfully set trigger mode.")
    except subprocess.CalledProcessError as e:
        print(f"[set_trigger_mode] Failed: {e}")

# ------------------------------
# INITIALIZE pigpio
# ------------------------------
pi = pigpio.pi()
if not pi.connected:
    print("pigpio daemon not running or no connection. Exiting.")
    exit(1)

# Optionally set external trigger mode ON
set_trigger_mode(True)

# ------------------------------
# CONFIGURE PINS
# ------------------------------
# Trigger pin as OUTPUT (active-high pulse)
pi.set_mode(TRIGGER_PIN, pigpio.OUTPUT)
pi.write(TRIGGER_PIN, 0)  # Ensure LOW at start

# Buttons as INPUT. Assume they're wired to pull up or pull down as needed.
# If you have e.g. a button from pin -> GND, you can do:
pi.set_mode(RIGHT_BUTTON_PIN, pigpio.INPUT)
pi.set_pull_up_down(RIGHT_BUTTON_PIN, pigpio.PUD_UP)

pi.set_mode(LEFT_BUTTON_PIN, pigpio.INPUT)
pi.set_pull_up_down(LEFT_BUTTON_PIN, pigpio.PUD_UP)

# LED as OUTPUT
pi.set_mode(LED_PIN, pigpio.OUTPUT)
pi.write(LED_PIN, 0)

# Helper functions to check if a button is pressed
# (assuming active-low, i.e. pressed means read=0)
def is_pressed(pin):
    return pi.read(pin) == 0

def led_on():
    pi.write(LED_PIN, 1)

def led_off():
    pi.write(LED_PIN, 0)

# ------------------------------
# CAMERA INITIALIZATION
# ------------------------------
cam0 = Picamera2(0)
cam1 = Picamera2(1)

# If you need custom config:
# config0 = cam0.create_still_configuration()
# cam0.configure(config0)
# config1 = cam1.create_still_configuration()
# cam1.configure(config1)

cam0.start()
cam1.start()

# ------------------------------
# IMAGE BUFFERS & QUEUE
# ------------------------------
image_buffer0 = []
image_buffer1 = []
write_queue   = queue.Queue()

# ------------------------------
# HARDWARE TRIGGER & CAPTURE
# ------------------------------
def hardware_trigger_pulse():
    """
    Send a ~1ms HIGH pulse on TRIGGER_PIN to cause both GS cameras to capture
    a frame in external-trigger mode.
    """
    pi.write(TRIGGER_PIN, 1)
    time.sleep(0.001)  # 1ms
    pi.write(TRIGGER_PIN, 0)

def capture_both_cameras(index):
    """
    After pulsing, wait ~10ms for sensor readout, then capture frames from both cameras
    into memory buffers.
    """
    time.sleep(0.01)  # small wait for exposure + readout

    frame0 = cam0.capture_array()
    tstamp0 = time.monotonic_ns()
    filename0 = f"{tstamp0}_{index:05}"
    image_buffer0.append((frame0, filename0))

    frame1 = cam1.capture_array()
    tstamp1 = time.monotonic_ns()
    filename1 = f"{tstamp1}_{index:05}"
    image_buffer1.append((frame1, filename1))

# ------------------------------
# WRITING IMAGES TO DISK
# ------------------------------
def write_images_to_disk():
    """
    Pull frames (cam0 + cam1) from write_queue in pairs and save them to .jpg files.
    """
    while not write_queue.empty():
        try:
            frame0, filename0 = write_queue.get(timeout=1)
            frame1, filename1 = write_queue.get(timeout=1)

            # Convert RGB -> BGR for OpenCV
            frame0_bgr = cv2.cvtColor(frame0, cv2.COLOR_RGB2BGR)
            frame1_bgr = cv2.cvtColor(frame1, cv2.COLOR_RGB2BGR)

            path0 = f"{CAM0_DIR}/0_{filename0}.jpg"
            path1 = f"{CAM1_DIR}/1_{filename1}.jpg"

            cv2.imwrite(path0, frame0_bgr)
            cv2.imwrite(path1, frame1_bgr)
            print(f"Saved {path0} and {path1}")
        except queue.Empty:
            break

def flush_and_write():
    """
    Move frames from memory buffers into write_queue, then spawn a thread to write them.
    """
    for i in range(len(image_buffer0)):
        write_queue.put(image_buffer0[i])
        write_queue.put(image_buffer1[i])

    image_buffer0.clear()
    image_buffer1.clear()

    th = threading.Thread(target=write_images_to_disk)
    th.start()

# ------------------------------
# MAIN LOOP
# ------------------------------
try:
    print("Press & hold Right Button to trigger captures. Release -> saves to disk. Left Button -> exit.")
    i = 0

    while True:
        if is_pressed(RIGHT_BUTTON_PIN) and not is_pressed(LEFT_BUTTON_PIN):
            led_on()
            while is_pressed(RIGHT_BUTTON_PIN):
                hardware_trigger_pulse()
                capture_both_cameras(i)
                i += 1
                # Basic limit for framerate or sensor readout
                time.sleep(0.03)
            # On release
            flush_and_write()
            led_off()

        if is_pressed(LEFT_BUTTON_PIN):
            print("Left button pressed - exiting.")
            break

        time.sleep(0.1)

except KeyboardInterrupt:
    print("KeyboardInterrupt - Exiting.")

finally:
    print("Cleaning up...")
    # Optionally disable external trigger mode
    set_trigger_mode(False)

    cam0.stop()
    cam1.stop()
    cam0.close()
    cam1.close()

    pi.write(LED_PIN, 0)
    pi.stop()  # terminate pigpio connection

    print("Done.")


