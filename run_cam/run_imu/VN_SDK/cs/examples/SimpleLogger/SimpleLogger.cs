// The MIT License (MIT)
// 
//  VectorNav Software Development Kit (v0.15.0)
// Copyright (c) 2024 VectorNav Technologies, LLC
// 
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.


using System;
using VNSDK;

namespace SimpleLogger
{
    class Program
    {
        static int Main(string[] args)
        {
            Console.WriteLine($"Simple Logger example.");

            String port = "COM3";
            String path = "log.bin";

            if (args.Length > 0)
            {
                port = args[0];
            }

            if (args.Length > 1)
            {
                path = args[1];
            }


            Sensor sensor = new Sensor();
            sensor.AutoConnect(port);

            Console.WriteLine($"Connected to {port} at {sensor.ConnectedBaudRate()}");

            VNSDK.Registers.System.Model modelReg = new VNSDK.Registers.System.Model();
            sensor.ReadRegister(modelReg);
            Console.WriteLine($"Sensor Model Number: {modelReg.model}");

            ByteBuffer bufferToLog = new ByteBuffer(1024);
            SimpleLogger logger = new SimpleLogger(bufferToLog, path);

            sensor.RegisterReceivedByteBuffer(bufferToLog);

            if (logger.Start())
            {
                Console.WriteLine("Error: Failed to write to file.");
                return 1;
            }

            Console.WriteLine($"Logging to {path}");
            System.Threading.Thread.Sleep(5000);

            logger.Stop();

            sensor.DeregisterReceivedByteBuffer();

            sensor.Disconnect();
            Console.WriteLine($"Sensor Disconnected.");
            Console.WriteLine($"Simple Logging example complete.");

            return 0;
        }
    }
}

