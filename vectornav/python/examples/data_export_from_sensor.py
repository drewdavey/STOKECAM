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

import vectornav
from vectornav import Sensor
from vectornav.Plugins import ExporterCsv

def main(argv):

    port = argv[0] if argv else "COM30"
    path = argv[1] if len(argv)==2 else ""
    
    vs = Sensor()

    csvExporter = ExporterCsv(path, True)
    
    vs.autoConnect(port)

    vs.subscribeToMessage(
        csvExporter.getQueuePtr(),
        vectornav.Registers.BinaryOutputMeasurements(),
        vectornav.FaPacketDispatcher.SubscriberFilterType.AnyMatch
    )
    
    vs.subscribeToMessage(
        csvExporter.getQueuePtr(),
        "VN",
        vectornav.AsciiPacketDispatcher.SubscriberFilterType.StartsWith
    )

    csvExporter.start()
    print("logging started")
    
    time.sleep(5)

    csvExporter.stop()
    print("ExportFromSensor example complete.")

if __name__ == '__main__':
    main(sys.argv[1:])
