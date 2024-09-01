

from vnpy import *


# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s) 
# s = VnSensor()
# s.connect('/dev/ttyUSB0', 115200)
ez = EzAsyncData.connect('/dev/ttyUSB0', 115200)
s = ez.sensor

model_num = s.read_model_number()
serial_num = s.read_serial_number()

pos = ez.current_data.has_any_position
print('Has position: ', str(pos), "\n")

num_sats = ez.current_data.num_sats
print("Number of satellites: ", str(num_sats), "\n")

vn_pos = s.read_gps_solution_lla()
print('Pos: ', vn_pos.lla, '\n')

vn_time = ez.current_data.time_utc
print('Time: ', vn_time, '\n')

s.disconnect()