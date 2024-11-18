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

import sys
import vectornav
from vectornav import Registers, Plugins


usage = "[port] -s [fileLocation]\n[port] -l [fileLocation]\n"

def main(argv):

    # Parse command line arguments
    comPort = argv[0]
    
    loadOrSave = 0
    if ("-s" in argv[1]):
        loadOrSave = 1
    elif ("-l" in argv[1]):
        loadOrSave = 2
    else:
        print(usage)
        return

    path = argv[2]

    # Connect to sensor
    vs = vectornav.Sensor()
    vs.autoConnect(comPort)
    print(f"Connected to {comPort} at {vs.connectedBaudRate()}")
    
    # Initialized Configuration object to perform RegisterScan
    configurator = Plugins.SensorConfigurator(vs, comPort)

    # Run RegisterScan
    if (loadOrSave == 1):
        regScanFailure = configurator.SaveConfiguration(path)
    else:
        regScanFailure = configurator.LoadConfiguration(path)
    
    # Disconnect from sensor
    vs.disconnect()
    if regScanFailure:
        raise Exception("Register Scan Failed")
    
    print("RegisterScan example complete")

    
    
if __name__ == '__main__':
    main(sys.argv[1:])
