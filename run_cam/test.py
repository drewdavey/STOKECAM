
import time
import subprocess
from settings import *
from picamera2 import Picamera2
from datetime import datetime, timezone
from startup import setup_logging, read_inputs_yaml
from standby import create_dirs

config = get_still_configuration() # get still config from settings.py. add statement here to choose mode

cam = Picamera2(0)
# cam1 = Picamera2(1)

# cam0.stop()
# cam1.stop()
# cam0.close()
# cam1.close()
