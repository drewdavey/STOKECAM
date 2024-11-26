# Last updated: 2024-10-03
##################################
# This script is launched in the background during standby and passed 3 arguments from a parent script.
# Args: (1) fname_imu (2) fname_log (3) imu_dt 
##################################
import sys
import time
import signal
import vectornav
from utils import *
from vectornav import *
from datetime import datetime, timezone
from vectornav.Plugins import ExporterCsv

running = True

def imu_run(fname_imu,fname_log,portName):
    global running
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 
    csvExporter = ExporterCsv(fname_imu, True)
    s.subscribeToMessage(
            csvExporter.getQueuePtr(),
            vectornav.Registers.BinaryOutputMeasurements(),
            vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch)
    csvExporter.start()
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log.write(f"{tstr}:     IMU started.\n")
    while running:
        time.sleep(0.001)
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log.write(f"{tstr}:     IMU stopped.\n\n")
    log.close()
    csvExporter.stop()
    s.disconnect()
    sys.exit(0)

def imu_disconnect(signum, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, imu_disconnect) # signal handling
signal.signal(signal.SIGINT, imu_disconnect)

if __name__ == '__main__':
    fdir, fname_log = setup_logging()             
    imu_run(sys.argv[1],sys.argv[2],sys.argv[3])