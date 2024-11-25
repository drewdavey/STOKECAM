# The MIT License (MIT)
# 
#  VectorNav Software Development Kit (v0.15.1)
# Copyright (c) 2024 VectorNav Technologies, LLC
# 
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import time, sys

from vectornav import Sensor, Registers


def main(argv):
    """
    This getting started example will walk you through the Python usage of the SDK to connect to
    and interact with a VectorNav sensor.

    This example will achieve the following in the specified order:
    1. Connect to the sensor
    2. Poll and print the model number using a read register command
    3. Poll and print the yaw, pitch, and roll using a read register command
    4. Configure the ADOR and ADOF to YPR at 2Hz
    5. Configure the first binary output to output timeStartup, accel, angularRate, all from the common group
        with a 200 rate divisor
    6. Enter a loop for 5 seconds where it:
        Determines which measurement it has (VNYPR or the necessary binary header)
        Prints out the relevant measurement from the CompositeData struct
    7. Disconnect from the sensor
    """

    
    #### 1. AUTOCONNECT TO THE SENSOR

    # Defining the port connection parameters    sensorPortName = argv[0] if argv else "COM30" # Change the sensor port name to the com port of your local machine
    sensorPortName = argv[0] if argv else "COM30" # Change the sensor port name to the com port of your local machine
    

    # Instantiate a Sensor object to interact with the sensor
    vs = Sensor()

    vs.autoConnect(sensorPortName)
    print(f"Connected to {sensorPortName} at {vs.connectedBaudRate()}")

    #### 2. PRINTING THE SENSOR MODEL NUMBER
    modelRegister = Registers.Model()

    vs.readRegister(modelRegister)
    print(f"Sensor Model Number: {modelRegister.model}")

    #### 3. PRINTING THE YPR    
    yprRegister = Registers.YawPitchRoll()
    
    vs.readRegister(yprRegister)
    print(f"Current Reading: Yaw - {yprRegister.yaw}, Pitch - {yprRegister.pitch}, Roll - {yprRegister.roll} ")

    #### 4. CONFIGURING ADOR AND AODF TO YPR @ 2Hz
    asyncDataOutputType = Registers.AsyncOutputType()

    asyncDataOutputType.ador = Registers.AsyncOutputType.Ador.YPR
    asyncDataOutputType.serialPort = Registers.AsyncOutputType.SerialPort.Serial1

    vs.writeRegister(asyncDataOutputType)
    print(f"ADOR Configured")
    
    asyncDataOutputFreq= Registers.AsyncOutputFreq()
    asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate20Hz
    asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1

    vs.writeRegister(asyncDataOutputFreq)
    print("ADOF Configured")

    #### 5. CONFIGURING THE FIRST BINARY OUTPUT
    binaryOutput1Register = Registers.BinaryOutput1()
    binaryOutput1Register.rateDivisor = 100
    binaryOutput1Register.asyncMode.serial1 = 1
    binaryOutput1Register.asyncMode.serial2 = 0
    
    binaryOutput1Register.common.timeStartup = 1
    binaryOutput1Register.common.accel = 1
    binaryOutput1Register.common.angularRate = 1

    vs.writeRegister(binaryOutput1Register)
    print("Binary output message configured")

    #### 6. ENTER A LOOP FOR 5 SECONDS TO DETERMINE THE MEASUREMENT TYPE
    t0 = time.time()
    while (time.time() - t0 < 5):
        cd = vs.getNextMeasurement()
        if not cd: continue

        if timeStartup := cd.time.timeStartup:
            print(f"Binary Packet")
            print(f"Time: {timeStartup.nanoseconds()}")
            print(f"Accel: {cd.imu.accel}")
        elif cd.matchesMessage("VNYPR"):
            print("Ascii Packet")
            print(f"YPR: {cd.attitude.ypr}")
        else:
            print("Unrecognized asynchronous message received")

    #### 7. DISCONNECTING THE SENSOR
    vs.disconnect()
    print("Sensor Disconnected")
    print("gettingStarted example complete.")

if __name__ == '__main__':
    main(sys.argv[1:])
