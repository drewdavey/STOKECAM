# Last updated: 2024-06-03
##################################
# This script is passed 
# Args: (1) 
##################################

import sys
import time

# Import vnpy library
# from vnpy import *
import vectornav
from vectornav import *
from vectornav.Plugins import SimpleLogger
from vectornav import Sensor, ByteBuffer, Registers

# Create sensor object and connect to the VN-200 
# at the baud rate of 115200 (115,200 bytes/s)
s = Sensor()
s.connect('/dev/ttyUSB0', 115200)
if not s.verifySensorConnectivity():
    raise Exception("Wrong baud rate or incorrect port")
v
# # Create register object
# asyncDataOutputFreq = Registers.AsyncOutputFreq()
# gnss = Registers.GnssSolLla()
# # Set Output Frequency as 10Hz on Serial Port 1
# asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate40Hz
# asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1
# # Write the frequency
# s.writeRegister(asyncDataOutputFreq)


# Record the start time
start_time = time.time()
duration = 10  # seconds

filePath = "log.bin"
# Set up resources needed for data logging
bufferToLog = ByteBuffer(8192)
logger = SimpleLogger(bufferToLog, filePath)
# Register the logger's input buffer to receive all bytes from the sensor
s.registerReceivedByteBuffer(bufferToLog)
if (logger.start()):
    print("Error: Failed to write to file")
print(f"Logging to {filePath}")

# vs = Sensor()
# csvExporter = ExporterCsv('.', True) # exporting with system timestamps
# # subscribe to binary VectorNav ascii packets
# vs.subscribeToMessage(
#         csvExporter.getQueuePtr(),
#         "VN",
#         vectornav.AsciiPacketDispatcher.SubscriberFilterType.StartsWith
# )
# vs.autoConnect('/dev/ttyUSB0')
# csvExporter.start()


while time.time() - start_time < duration:
    # # Read yaw, pitch, and roll values
    # ypr = s.read_yaw_pitch_roll()
    # print(f"Yaw: {ypr.x}, Pitch: {ypr.y}, Roll: {ypr.z}"+ '\n')

    # gps = s.read_gps_solution_lla() # Read the GPS solution in LLA format

    # reg = s.read_yaw_pitch_roll_magnetic_acceleration_and_angular_rates()
    # print(f"Acc_X: {reg.accel.x}, Acc_Y: {reg.accel.y}, Acc_Z: {reg.accel.z}"+ '\n')

    # print(f" {gps.num_sats}, {gps.time}, ({gps.lla.x}, {gps.lla.y}, {gps.lla.z})" + '\n')
   
    # cd = CompositeData()
    # print(f"Time: {cd.time_utc}" + '\n')
    # print(f"position_gps_lla: {cd.position_gps_lla}" + '\n')

    # cd = ez.current_data
    # nd = ez.next_data()
    # print(cd.time_utc)
    # print(f"Next: {nd.time_utc}" + '\n')
    # print(nd.pressure)

    # gps = s.readRegister(gnss)
    # print(gps)

    cd = s.getMostRecentMeasurement()
    # if not cd: continue
    # # if cd.matchesMessage("VNINS"):
    print(f"Accel: {cd.imu.accel}"+ '\n')
    print(f"YPR: {cd.attitude.ypr}"+ '\n')
    print(f"Time: {cd.time.timeUtc}" + '\n')
    print(f"Unc: {cd.gnss.gnss1PosUncertainty}" + '\n')
    


    # Pause for a short time to avoid flooding the command window
    time.sleep(0.1)  

# csvExporter.stop()
logger.stop()

s.deregisterReceivedByteBuffer()

# Disconnect from the sensor
s.disconnect()


# s.write_async_data_output_frequency(10)
