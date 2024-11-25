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

from vectornav import Sensor, Registers
from vectornav.Registers import VpeBasicControl
from vectornav.Commands import Command, KnownMagneticDisturbance
import time,sys

def main(argv):
    print("Starting main")
    sensorPortName = argv[0] if argv else "COM10"

    # Instantiate a Sensor object to interact with the sensor
    vs = Sensor()
    vs.autoConnect(sensorPortName)
    vs.verifySensorConnectivity()
    print(f"Connected to {sensorPortName} at {vs.connectedBaudRate()}")

    # Read and pring model number
    modelReg = Registers.Model()
    vs.readRegister(modelReg)
    print("Model number: ", modelReg.model)

    # Create and configure both a generic command and a Write Register command
    kmd = KnownMagneticDisturbance(KnownMagneticDisturbance.State.Present)    

    vpeBasicControl = VpeBasicControl()
    vpeBasicControl.headingMode = VpeBasicControl.HeadingMode.Absolute
    vpeBasicControl.filteringMode =  VpeBasicControl.FilteringMode.AdaptivelyFiltered
    vpeBasicControl.tuningMode =  VpeBasicControl.TuningMode.Adaptive

    vpeBasicControlCmd = Command(vpeBasicControl.toWriteCommand())

    # Send our commands without blocking
    vs.sendCommand(kmd, Sensor.SendCommandBlockMode.none)
    vs.sendCommand(vpeBasicControlCmd, Sensor.SendCommandBlockMode.none)

    time.sleep(1)

    if not kmd.isAwaitingResponse():
        error = kmd.getError()
        if (error):
            print(f"KMD received error {error.what()}")
        else:
            print(f"KMD response: {str(kmd.getResponse())}")
    else:
        print(f"KMD received no response")
        
    if not vpeBasicControlCmd.isAwaitingResponse():
        error = vpeBasicControlCmd.getError()
        if (error):
            print(f"WRG received error {error.what()}")
        else:
            print(f"WRG response: {vpeBasicControlCmd.getResponse()}")
    else:
        print(f"WRG received no response")

    vs.disconnect()
    print("Commands example complete")

if __name__ == '__main__':
    main(sys.argv[1:])
