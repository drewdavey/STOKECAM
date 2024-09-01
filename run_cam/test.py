
import os
from settings import *
from picamera2 import Picamera2
config = get_still_configuration() # get still config from settings.py. add statement here to choose mode
import time
import subprocess

from datetime import datetime, timezone
from startup import setup_logging, read_inputs_yaml
# from standby import create_dirs
fdir, fname_log = setup_logging()               # Setup logging
session = datetime.now(timezone.utc).strftime('%H%M%S_' + 'burst')
fdir_out = os.path.join(fdir, session + '/')
fdir_cam0 = os.path.join(fdir_out, 'cam0/')
fdir_cam1 = os.path.join(fdir_out, 'cam1/')
os.makedirs(fdir_cam0, exist_ok=True)
os.makedirs(fdir_cam1, exist_ok=True)
fname_imu = f'{fdir_out}IMU_{session}.txt'

cam0 = Picamera2(0)
cam1 = Picamera2(1)

cam0.configure(config)
cam1.configure(config)
# cam0.stop()
# cam1.stop()
# cam0.close()
# cam1.close()
