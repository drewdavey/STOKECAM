# Last updated: 2024-11-26
##################################
# Housekeeping funcs for the stereo camera system
##################################

import os
import time

from vectornav import *
from datetime import datetime, timezone, timedelta
from vectornav.Registers import VpeBasicControl
from vectornav.Commands import Command, KnownMagneticDisturbance

s = Sensor()                      # Create sensor object and connect to the VN-200 
s.autoConnect('/dev/ttyUSB0')           # at the baud rate of 115200 (115,200 bytes/s) 

#### CONFIGURE THE SYNC OUTPUT
sync_control = Registers.SyncControl()
sync_control.syncOutMode = Registers.SyncControl.SyncOutMode.GpsPps
s.writeRegister(sync_control)

# #### CONFIGURE THE NMEA OUTPUT
# nmea_control = Registers.System.NmeaOutput1()
# nmea_control.port = Registers.System.NmeaOutput1.Port.Serial1
# s.writeRegister(nmea_control)

#### CONFIGURE ADOR AND AODF 
# asyncDataOutputType = Registers.AsyncOutputType()
# asyncDataOutputType.ador = Registers.AsyncOutputType.Ador.YPR
# asyncDataOutputType.serialPort = Registers.AsyncOutputType.SerialPort.Serial1
# s.writeRegister(asyncDataOutputType)
asyncDataOutputFreq= Registers.AsyncOutputFreq()
asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate40Hz
asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1
s.writeRegister(asyncDataOutputFreq)

#### CONFIGURE THE BINARY OUTPUT
binaryOutput1Register = Registers.BinaryOutput1()
binaryOutput1Register.rateDivisor = 20           ### 40 Hz (~800/rateDivisor) ###
binaryOutput1Register.asyncMode.serial1 = 1
binaryOutput1Register.asyncMode.serial2 = 0
binaryOutput1Register.time.timeUtc = 1
binaryOutput1Register.time.timeStartup = 1
binaryOutput1Register.time.timeGps = 1
binaryOutput1Register.time.timeSyncIn = 1
binaryOutput1Register.time.timeGpsPps = 1
binaryOutput1Register.imu.imuStatus = 1
binaryOutput1Register.imu.temperature = 1
binaryOutput1Register.imu.pressure = 1
binaryOutput1Register.imu.accel = 1
binaryOutput1Register.imu.mag = 1
binaryOutput1Register.attitude.ypr = 1
binaryOutput1Register.attitude.quaternion = 1
binaryOutput1Register.attitude.dcm = 1
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
