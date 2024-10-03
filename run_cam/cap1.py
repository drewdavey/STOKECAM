# Last updated: 2024-04-10
##################################
# This script is launched in the background during capture and passed 3 arguments from a parent script.
# Args: (1) fname_imu (2) fname_log (3) imu_dt 
##################################
import sys
import time
import signal
from utils import *
from settings import *
from picamera2 import Picamera2
from datetime import datetime, timezone, timedelta

running = True

def capture(fdir_cam1, mode, dt):
    global running

    # config = get_config(mode)                       # Get the configuration for the cameras
    # time.sleep(5)
    # cam1 = Picamera2(1)                             # Initialize cam0     
    # cam1.configure(config)                            # Configure cam0    
    # cam1.start()

    i = 0
    # time.sleep(twait - datetime.now(timezone.utc))
    while running:
        tnow = datetime.now(timezone.utc)
        tnext = tnow + timedelta(seconds=dt)
        tstr = tnow.strftime('%H%M%S%f')
        cam1.capture_file(f"{fdir_cam1}1_{tstr}_{i+1:05}.jpg")
        i += 1
        # time.sleep(tnext - datetime.now(timezone.utc))

    # cam1.stop() # Stop the camera
    # cam1.close() # Close the camera
    sys.exit(0)

def disconnect(signum, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, disconnect) # signal handling
signal.signal(signal.SIGINT, disconnect)

if __name__ == '__main__':
    fdir, fname_log = setup_logging()             
    inputs = read_inputs_yaml(fname_log)
    dt = inputs['dt']           
    capture(sys.argv[1],sys.argv[2], dt)
