import time
import threading
import queue
import cv2
import subprocess
from picamera2 import Picamera2
from gpiozero import Button, LED, DigitalOutputDevice
from datetime import datetime

# ------------------------------
# HARDWARE PIN SETUP
# ------------------------------
TRIGGER_PIN      = 26   # Goes to GS camera XTR line (both cams)
RIGHT_BUTTON_PIN = 18   # Press/hold to start capturing
LEFT_BUTTON_PIN  = 17   # (Optional) for exit or other logic
LED_PIN          = 24   # (Optional) LED to show capturing

# Using gpiozero's DigitalOutputDevice for the trigger line
trigger_output = DigitalOutputDevice(TRIGGER_PIN, active_high=True, initial_value=False)
# Buttons and LED
right_button = Button(RIGHT_BUTTON_PIN, hold_time=2)
left_button  = Button(LEFT_BUTTON_PIN,  hold_time=2)
capture_led  = LED(LED_PIN)

# ------------------------------
# ENABLE EXTERNAL TRIGGER MODE VIA PYTHON
# ------------------------------
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

# Call once at the start to enable external trigger
set_trigger_mode(True)

# ------------------------------
# CAMERA INITIALIZATION
# ------------------------------
cam0 = Picamera2(0)
cam1 = Picamera2(1)

# If needed, configure them:
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
# HELPER FUNCTIONS
# ------------------------------
def hardware_trigger_pulse():
    """
    Send a ~1ms HIGH pulse on TRIGGER_PIN. Both cameras (cam0 & cam1) 
    use this line in external trigger mode to expose/capture a frame.
    """
    trigger_output.on()
    time.sleep(0.001)  # 1ms
    trigger_output.off()

def capture_both_cameras(i):
    """
    After pulsing the hardware trigger, wait briefly,
    then capture from each camera, storing frames in memory buffers.
    """
    time.sleep(0.01)  # small delay for exposure & readout

    # Capture from cam0
    frame0 = cam0.capture_array()
    tnow0  = time.monotonic_ns()
    filename0 = f"{tnow0}_{i:05}"
    image_buffer0.append((frame0, filename0))

    # Capture from cam1
    frame1 = cam1.capture_array()
    tnow1  = time.monotonic_ns()
    filename1 = f"{tnow1}_{i:05}"
    image_buffer1.append((frame1, filename1))

def write_images_to_disk(cam0_dir="./cam0", cam1_dir="./cam1"):
    """
    Pull frames off the write_queue in pairs (cam0, cam1) and write them to disk.
    """
    while not write_queue.empty():
        try:
            (frame0, filename0) = write_queue.get(timeout=1)
            (frame1, filename1) = write_queue.get(timeout=1)

            # Convert from RGB to BGR for OpenCV
            frame0_bgr = cv2.cvtColor(frame0, cv2.COLOR_RGB2BGR)
            frame1_bgr = cv2.cvtColor(frame1, cv2.COLOR_RGB2BGR)

            path0 = f"{cam0_dir}/0_{filename0}.jpg"
            path1 = f"{cam1_dir}/1_{filename1}.jpg"

            cv2.imwrite(path0, frame0_bgr)
            cv2.imwrite(path1, frame1_bgr)
            print(f"[INFO] Saved {path0} and {path1}")
        except queue.Empty:
            break

def flush_and_write():
    """
    Move all frames from memory buffers to the write_queue,
    then start a background thread to write them asynchronously.
    """
    for i in range(len(image_buffer0)):
        write_queue.put(image_buffer0[i])
        write_queue.put(image_buffer1[i])

    image_buffer0.clear()
    image_buffer1.clear()

    writer_thread = threading.Thread(target=write_images_to_disk, args=("./cam0", "./cam1"))
    writer_thread.start()

# ------------------------------
# MAIN LOOP / LOGIC
# ------------------------------
try:
    print("[INFO] Ready. Press & hold Right Button to capture. Release -> write images. Ctrl+C to exit.")
    i = 0

    while True:
        # If right button is pressed (and not left), start capturing loop
        if right_button.is_pressed and not left_button.is_pressed:
            capture_led.on()
            while right_button.is_pressed:
                hardware_trigger_pulse()
                capture_both_cameras(i)
                i += 1
                time.sleep(0.03)  # basic framerate delay
            # On release
            flush_and_write()
            capture_led.off()

        # If left button is pressed, exit
        if left_button.is_pressed:
            print("[INFO] Left button pressed - exiting.")
            break

        time.sleep(0.1)

except KeyboardInterrupt:
    print("[INFO] Interrupted by user.")

finally:
    print("[INFO] Cleaning up...")
    # Optionally disable trigger mode
    set_trigger_mode(False)

    cam0.stop()
    cam1.stop()
    cam0.close()
    cam1.close()

    capture_led.off()
    capture_led.close()

    trigger_output.off()
    trigger_output.close()

    right_button.close()
    left_button.close()

    print("[INFO] Done.")



