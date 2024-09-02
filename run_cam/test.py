
import time
from vnpy import *
from datetime import datetime, timezone

# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s) 
# s = VnSensor()
# s.connect('/dev/ttyUSB0', 115200)
ez = EzAsyncData.connect('/dev/ttyUSB0', 115200)
s = ez.sensor

model_num = s.read_model_number()
serial_num = s.read_serial_number()

fname_log = 'test_LOG.txt'
log = open(fname_log, 'a')

while not ez.current_data.has_fix:

    log.write('#####################################################')

    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
    log.write(f"{tstr}\n")
    
    pos = ez.current_data.has_any_position
    log.write('Has position: ', str(pos), "\n")

    hasposun = ez.current_data.has_any_position_uncertainty
    log.write('Has position uncertainty: ', str(hasposun), "\n")

    posun = ez.current_data.any_position_uncertainty
    log.write('Position uncertainty: ', str(posun), "\n")

    posunes = ez.current_data.position_uncertainty_estimated
    log.write('Position uncertainty estimate: ', str(posunes), "\n")

    gpstime = ez.current_data.has_time_gps
    log.write('Has GPS time: ', str(gpstime), "\n")

    vn_pos = s.read_gps_solution_lla()
    log.write('GPS Pos: ', vn_pos.lla, '\n')

    vn_time = ez.current_data.time_utc
    log.write('GPS Time: ', vn_time, '\n')

    num_sats = ez.current_data.num_sats
    log.write("Number of satellites: ", str(num_sats), "\n")

    has_num_sats = ez.current_data.has_num_sats
    log.write("Has Number of satellites: ", str(has_num_sats), "\n")

    log.write('#####################################################')
    time.sleep(2)

log.close()
s.disconnect()