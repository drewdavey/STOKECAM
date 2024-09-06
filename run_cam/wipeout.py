# Last updated: 2024-09-03
##################################
# This script launches standby mode, which allows the user to choose between burst and numFrames shooting modes.
# The user can also calibrate the cameras by holding the left button for more than 5 seconds.
##################################
import sys
import time
import subprocess
from utils import *
from settings import *
from signal import pause
from picamera2 import Picamera2
from gpiozero import Button, LED
from datetime import datetime, timezone

def configure_cameras(fname_log, mode):
    global cam0, cam1, config 
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Configuring cameras to {mode} mode...\n")
    for idx, cam in enumerate([cam0, cam1]):
        cam.configure(config)
        cam.start()
        log.write(f"{tstr}:     cam{idx} configuration: {cam.camera_configuration()}\n")
        log.write(f"{tstr}:     cam{idx} metadata: {cam.capture_metadata()}\n")
    log.write('\n')
    log.close()

def burst(fdir, fname_log, dt, mode): 
    global busy
    i = 0
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"burst_{mode}")
    imu_process = subprocess.Popen(['python3', 'imu.py', fname_imu, fname_log])
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log.write(f"{tstr}:     burst_{mode} session: {fdir_out}\n")
    while right_button.is_pressed:
        red.on()
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        i += 1
        red.off()
        time.sleep(dt)
    imu_process.terminate()
    busy = False
    log.close()

def numFrames(fdir, fname_log, dt, num_frames, mode):
    global busy
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"numFrames_{mode}")
    imu_process = subprocess.Popen(['python3', 'imu.py', fname_imu, fname_log])
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log.write(f"{tstr}:     numFrames_{mode} session: {fdir_out}\n")
    for i in range(int(num_frames)):
        red.on()
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3] 
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        red.off()
        time.sleep(dt)
    imu_process.terminate()
    busy = False
    log.close()

def calib(fdir, fname_log, calib_dt, calib_frames, mode):
    global busy
    [led.on() for led in (red, green, yellow)]
    time.sleep(5)
    [led.off() for led in (red, green, yellow)]
    fdir_out, fdir_cam0, fdir_cam1, fname_imu = create_dirs(fdir, f"calib_{mode}")
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log.write(f"{tstr}:     calibration_{mode} session: {fdir_out}\n")
    log.close()
    imu_process = subprocess.Popen(['python3', 'imu.py', fname_imu, fname_log])
    for i in range(int(calib_frames)):
        green.on(), time.sleep(0.5)
        yellow.on(), time.sleep(0.5)
        red.on(), time.sleep(0.5)
        [led.blink(0.5,0.5) for led in (red, green, yellow)], time.sleep(3)
        [led.on() for led in (red, green, yellow)],time.sleep(1.5)
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3] 
        cam0.capture_file(f"{fdir_cam0}0_{tstr}_{i+1:05}.jpg")
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        [led.off() for led in (red, green, yellow)]
        time.sleep(calib_dt)
    imu_process.terminate()
    busy = False

def monitor_gps():
    global busy
    if not busy:
        ez = EzAsyncData.connect('/dev/ttyUSB0', 115200) 
        s = ez.sensor
        if ez.current_data.has_any_position:                              
            if ez.current_data.position_uncertainty_estimated > 10:
                green.blink(0.25, 0.25)
            elif ez.current_data.position_uncertainty_estimated <= 10:
                green.on()
        else:
            green.blink(0.5, 0.5) 
        s.disconnect()

def toggle_modes():
    global cam0, cam1, config, mode
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

def exit_standby(fname_log):
    global standby
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log = open(fname_log, 'a')
    log.write(f"{tstr}:     Exiting standby.\n\n")
    log.close()
    yellow.off() # Close the lights
    red.off()
    time.sleep(2)
    standby = False

def enter_standby(fdir, fname_log, dt, num_frames, mode):
    yellow.on()
    time.sleep(1)
    global busy
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log.write(f"{tstr}:     Entering standby...\n\n")
    log.close()
    while not (right_button.is_held and left_button.is_held): # Hold both buttons for 3 seconds to exit standby
        if right_button.is_pressed and not left_button.is_pressed and not busy:
            busy = True # Hold right button ONLY for burst   
            burst(fdir, fname_log, dt, mode)
        if left_button.is_pressed and not right_button.is_pressed and not busy:
            busy = True # Press left button ONLY for 3 numFrames
            numFrames(fdir, fname_log, dt, num_frames, mode)
        time.sleep(0.2)
    exit_standby(fname_log)

############################ Initialization ############################
green = LED(12)                         # Green LED
yellow = LED(16)                        # Yellow LED
red = LED(24)                           # Red LED
right_button = Button(18, hold_time=3)  # Right button
left_button = Button(17, hold_time=3)   # Left button

fdir, fname_log = setup_logging()               # Setup logging
inputs = read_inputs_yaml(fname_log)            # Read inputs from inputs.yaml
num_frames = inputs['num_frames']
dt = inputs['dt']
calib_frames = inputs['calib_frames']
calib_dt = inputs['calib_dt']
gps_wait_time = inputs['gps_wait_time']

sync_clock_and_imu(fname_log, gps_wait_time)    # Connect to VecNav and sync clock 

global cam0, cam1, config, mode, standby, shooting_modes
shooting_modes = [inputs['shooting_mode0'], inputs['shooting_mode1'], inputs['shooting_mode2']]
mode = shooting_modes[0]                        # Default to 'auto'
config = get_config(mode)                       # Get the configuration for the cameras
cam0 = Picamera2(0)                             # Initialize cam0       
cam1 = Picamera2(1)                             # Initialize cam1
configure_cameras(fname_log, mode)              # Configure the cameras

standby = False
busy = False
tnow = time.time()
monitor_gps()
#######################################################################


############################# Main loop ###############################
# Hold both buttons for 3 seconds to toggle modes, then:
#                         - release both to toggle modes
#                         - release left ONLY to exit script
# Hold right button ONLY for 3 seconds to enter standby mode    
# Hold left button ONLY for 3 seconds to calibrate the cameras
                                 
while True: 
    if time.time() - tnow > 10 and not standby:
        monitor_gps()
    if right_button.is_held and not standby and not left_button.is_pressed:
        standby = True
        enter_standby(fdir, fname_log, dt, num_frames, mode)    
    if left_button.is_held and not standby and not right_button.is_pressed:
        calib(fdir, fname_log, calib_dt, calib_frames, mode)
        monitor_gps()
    if (right_button.is_held and left_button.is_held) and not standby:
        [led.on() for led in (red, green, yellow)]
        left_button.wait_for_release()
        time.sleep(1)
        if right_button.is_held:
            break
        else:
            toggle_modes()
            monitor_gps()
    tnow = time.time()
    time.sleep(0.2)
#######################################################################

############################## Cleanup ###############################
cam0.stop() # Stop the cameras
cam1.stop()
cam0.close() # Close the cameras
cam1.close()
green.close()
yellow.close() # Close the LEDs
red.close() 
right_button.close() 
left_button.close() # Close the buttons
sys.exit(0)
#######################################################################