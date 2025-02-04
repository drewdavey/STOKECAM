# Last updated: 2024-11-26
##################################
# Housekeeping funcs for the stereo camera system
##################################

import os
import time
from utils import *
import vectornav
from vectornav import *
from datetime import datetime, timezone, timedelta
from vectornav.Registers import *
from vectornav.Plugins import ExporterCsv
from vectornav.Commands import Command, KnownMagneticDisturbance

portName = '/dev/ttyUSB0'
fdir_out = '/home/drew/Downloads/session.csv'
fname_log = '/home/drew/Downloads/latency_test2.txt'

dt = 0.025

s = Sensor()                      # Create sensor object and connect to the VN-200 
s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 

# ### LOAD CONFIG IF EXIST
# configurator = Plugins.SensorConfigurator(vs, port)
# configurator.SaveConfiguration(pathToSaveFile)
# configurator.LoadConfiguration(pathToLoadFile)

# #### CONFIGURE THE SYNC OUTPUT
# sync_control = Registers.SyncControl()
# sync_control.syncOutMode = Registers.SyncControl.SyncOutMode.GpsPps
# s.writeRegister(sync_control)

# #### CONFIGURE THE NMEA OUTPUT
# nmea_control = Registers.NmeaOutput1()
# nmea_control.port = Registers.NmeaOutput1.Port.Serial1
# s.writeRegister(nmea_control)

### CONFIGURE ADOR AND AODF 
asyncDataOutputType = Registers.AsyncOutputType()
asyncDataOutputType.ador = Registers.AsyncOutputType.Ador.GPS
asyncDataOutputType.serialPort = Registers.AsyncOutputType.SerialPort.Serial1
s.writeRegister(asyncDataOutputType)

asyncDataOutputFreq= Registers.AsyncOutputFreq()
asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate50Hz
asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1
s.writeRegister(asyncDataOutputFreq)

#### CONFIGURE THE BINARY OUTPUT
binaryOutput1Register = Registers.BinaryOutput1()
binaryOutput1Register.rateDivisor = 16           ### 40 Hz (~800/rateDivisor) ###
binaryOutput1Register.asyncMode.serial1 = 1
# binaryOutput1Register.asyncMode.serial2 = 0
binaryOutput1Register.time.timeUtc = 1
binaryOutput1Register.time.timeStartup = 1
binaryOutput1Register.time.timeGps = 1
binaryOutput1Register.time.timeSyncIn = 1
binaryOutput1Register.time.timeGpsPps = 1
binaryOutput1Register.imu.imuStatus = 1
# binaryOutput1Register.imu.temperature = 1
# binaryOutput1Register.imu.pressure = 1
# binaryOutput1Register.imu.accel = 1
# binaryOutput1Register.imu.mag = 1
binaryOutput1Register.attitude.ypr = 1
binaryOutput1Register.attitude.quaternion = 1
binaryOutput1Register.attitude.dcm = 0
binaryOutput1Register.ins.posLla = 1
binaryOutput1Register.ins.posEcef = 1
binaryOutput1Register.ins.posU = 1
binaryOutput1Register.ins.insStatus = 1
binaryOutput1Register.gnss.gnss1PosLla = 1
binaryOutput1Register.gnss.gnss1PosEcef = 1
binaryOutput1Register.gnss.gnss1PosUncertainty = 1
binaryOutput1Register.gnss.gnss1Fix = 1
binaryOutput1Register.gnss.gnss1NumSats = 1
binaryOutput1Register.gnss.gnss1TimeUtc = 1
s.writeRegister(binaryOutput1Register)

s.disconnect()

####### Simulate STOKECAM #######

log = open(fname_log, 'w')

# Enter standby mode
s = Sensor() # Create sensor object and connect to the VN-200
csvExporter = ExporterCsv(fdir_out, True)
s.autoConnect(portName)
s.subscribeToMessage(csvExporter.getQueuePtr(), vectornav.Registers.BinaryOutputMeasurements(), vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch)

# cd = s.getNextMeasurement()
# rp_time = time.monotonic_ns()
# while not cd:
#     cd = s.getNextMeasurement()
#     rp_time = time.monotonic_ns()
# vn_time = cd.time.timeStartup.microseconds() * 1e3
# delta_time = vn_time - rp_time
# log.write(f"{rp_time}, {vn_time}, {delta_time}\n")

tstart1 = time.monotonic_ns()
csvExporter.start()
tstart2 = time.monotonic_ns()
tstart = (tstart1 + tstart2) / 2
log.write(f"{tstart}\n")

# While in burst
# reg = Registers.GnssSolLla()
# reg = Registers.BinaryOutputMeasurements()
t0 = time.time()
while (time.time() - t0 < 1):
    # s.readRegister(reg)
    # t = reg.time.timeGps
    # print(t)

    # cd = s.getNextMeasurement()
    # rp_time = time.monotonic_ns()
    # while not cd:
    #     cd = s.getNextMeasurement()
    #     rp_time = time.monotonic_ns()
    # vn_time = cd.time.timeStartup.microseconds() * 1e3
    # delta_time = vn_time - rp_time
    # log.write(f"{rp_time}, {vn_time}, {delta_time}\n")

    rp_time = time.monotonic_ns()
    log.write(f"{rp_time}\n")

    time.sleep(dt)

# # Exit standby
# tstop1 = time.monotonic_ns()
csvExporter.stop()
# tstop2 = time.monotonic_ns()
# tstop = (tstop1 + tstop2) / 2
# log.write(f"{tstop}\n")

s.disconnect()
log.close()