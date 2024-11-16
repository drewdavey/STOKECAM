# The MIT License (MIT)
# 
#  VectorNav Software Development Kit (v0.15.0)
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

from vectornav import Sensor, ByteBuffer, Registers
from vectornav.Plugins import SimpleLogger

def main(argv):

    sensorComPort = argv[0] if len(argv) == 1 else "'/dev/ttyUSB0'"
    filePath = argv[1] if len(argv) == 2 else "log.bin"
    
    vs = Sensor()
    vs.autoConnect(sensorComPort)

    modelRegister = Registers.Model()
    vs.readRegister(modelRegister)

    print(f"Sensor Model Number: {modelRegister.model}")

    # Set up resources needed for data logging
    bufferToLog = ByteBuffer(8192)
    logger = SimpleLogger(bufferToLog, "log.bin")
    
    # Register the logger's input buffer to receive all bytes from the sensor
    vs.registerReceivedByteBuffer(bufferToLog);

    if (logger.start()):
        print("Error: Failed to write to file")

    print(f"Logging to {filePath}")

    time.sleep(5)

    logger.stop()

    vs.deregisterReceivedByteBuffer()
    vs.disconnect()
    
    print("SimpleLogger example complete.")

if __name__ == '__main__':
    main(sys.argv[1:])
