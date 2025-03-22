#!/usr/bin/env python3

import time
import subprocess
from picamera2 import Picamera2
from gpiozero import DigitalOutputDevice

# GPIO pin that drives the cameras' XTR line.
TRIGGER_PIN = 26

# Create a DigitalOutputDevice for the trigger line.
trigger_output = DigitalOutputDevice(TRIGGER_PIN, active_high=True, initial_value=False)

def set_trigger_mode(enable: bool = True):
    """
    Write 1 or 0 to /sys/module/imx296/parameters/trigger_mode
    to enable or disable external trigger for IMX296 sensors.
    Requires root or passwordless sudo.
    """
    val = "1" if enable else "0"
    cmd = f"sudo sh -c 'echo {val} > /sys/module/imx296/parameters/trigger_mode'"
    print(f"[INFO] Setting IMX296 trigger_mode to: {val}")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("[INFO] Successfully set trigger mode.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to set trigger mode: {e}")

def hardware_trigger_pulse(pulse_length=0.001):
    """
    Send a short pulse on TRIGGER_PIN (3.3V) to trigger the GS cameras.
    Default is 1 ms.
    """
    trigger_output.on()
    time.sleep(pulse_length)
    trigger_output.off()

def main():
    # 1) Enable external trigger mode
    set_trigger_mode(True)

    # 2) Initialize both cameras
    cam0 = Picamera2(0)
    cam1 = Picamera2(1)

    # Optionally configure them if you want full control
    config0 = cam0.create_still_configuration()
    config1 = cam1.create_still_configuration()
    cam0.configure(config0)
    cam1.configure(config1)

    # 3) Start cameras
    cam0.start()
    cam1.start()

    # We wait a moment so the cameras can finish their initial setup
    time.sleep(0.5)

    # 4) Send an immediate “dummy” pulse to avoid initial timeouts
    hardware_trigger_pulse(pulse_length=0.005)
    time.sleep(0.01)
    frame_test_0 = cam0.capture_array()
    frame_test_1 = cam1.capture_array()
    print("[INFO] Captured initial frames successfully (no timeout).")

    # 5) Loop a few times to see if pulses produce new frames
    print("[INFO] Sending pulses and capturing frames...")
    for i in range(5):
        hardware_trigger_pulse(pulse_length=0.001)
        time.sleep(0.01)  # small delay for exposure/readout

        frame0 = cam0.capture_array()
        frame1 = cam1.capture_array()

        print(f"[INFO] Captured triggered frame pair #{i+1}")

        # If desired, do something with frame0, frame1 (e.g. check shape, print timestamps, etc.)

        time.sleep(0.2)  # slow down loop a bit

    # 6) Clean up
    cam0.stop()
    cam1.stop()
    set_trigger_mode(False)   # or leave it on if you prefer

    trigger_output.off()
    trigger_output.close()
    print("[INFO] Done. If you saw 'Captured triggered frame pair' lines, the cameras got pulses.")

if __name__ == "__main__":
    main()




