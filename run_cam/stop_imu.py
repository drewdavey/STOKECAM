# Last updated: 2024-06-03
##################################
# This script is passed 
# Args: (1) 
##################################

import sys
import time

# Import vnpy library
from vectornav import *

# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s)
s = VnSensor()
s.connect('/dev/ttyUSB0', 115200)

# Disconnect from the sensor
s.disconnect()
