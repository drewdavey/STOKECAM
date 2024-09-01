
import time
from vnpy import *


# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s) 
# s = VnSensor()
# s.connect('/dev/ttyUSB0', 115200)
ez = EzAsyncData.connect('/dev/ttyUSB0', 115200)
s = ez.sensor

model_num = s.read_model_number()
serial_num = s.read_serial_number()

while not ez.current_data.has_fix:

    pos = ez.current_data.has_any_position
    print('Has position: ', str(pos), "\n")

    gpstime = ez.current_data.has_time_gps
    print('Has GPS time: ', str(gpstime), "\n")

    vn_pos = s.read_gps_solution_lla()
    print('GPS Pos: ', vn_pos.lla, '\n')

    vn_time = ez.current_data.time_utc
    print('GPS Time: ', vn_time, '\n')

    num_sats = ez.current_data.num_sats
    print("Number of satellites: ", str(num_sats), "\n")

    has_num_sats = ez.current_data.has_num_sats
    print("Has Number of satellites: ", str(has_num_sats), "\n")

    time.sleep(2)
    
s.disconnect()