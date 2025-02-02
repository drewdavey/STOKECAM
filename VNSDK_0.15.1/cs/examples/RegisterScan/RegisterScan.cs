// The MIT License (MIT)
// 
//  VectorNav Software Development Kit (v0.15.1)
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

namespace Examples
{
    class Program
    {
        static void Usage()
        {
            Console.WriteLine("Usage: ");
            Console.WriteLine(" [port] -s [fileLocation]");
            Console.WriteLine(" [port] -l [fileLocation]");
        }

        static int Main(string[] args)
        {
            if (args.Length < 3)
            {
                Usage();
                return 1;
            }

            String port = args[0];
            bool saveConfiguration = false;

            if (args[1] == "-s")
            {
                saveConfiguration = true;
            }
            else if (args[1] != "-l")
            {
                Usage();
                return 1;
            }
            string path = args[2];

            Sensor sensor = new Sensor();
            sensor.AutoConnect(port);

            VNSDK.SensorConfigurator configurator = new VNSDK.SensorConfigurator(ref sensor, port);

            if (saveConfiguration)
            {
                configurator.SaveConfiguration(path);
            }
            else
            {
                configurator.LoadConfiguration(path);
            }

            sensor.Disconnect();
            return 0;
        }
    }
}

