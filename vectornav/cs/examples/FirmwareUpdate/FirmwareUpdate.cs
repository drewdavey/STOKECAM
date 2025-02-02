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
    public class Parameters
    {
        public string usage { get; }
        public bool valid { get; }
        public string port { get; }
        public string vnxmlPath { get; }
        public string navPath { get; }
        public string gnssPath { get; }
        public string imuPath { get; }

        public Parameters(string[] args)
        {
            usage = "[--PortName={port_name}] [--{Processor}={file_path}... | --vnXml={file_path}]";
            port = string.Empty;
            vnxmlPath = string.Empty;
            navPath = string.Empty;
            gnssPath = string.Empty;
            imuPath = string.Empty;
            valid = true;

            if (args.Length == 0)
            {
                // Change these to your local machine to run executable without arguments
                port = "COM11";
                navPath = "ReferenceModels_v3.vn100.vnx";
            }

            int index = 0;

            foreach (string parameter in args)
            {
                index = parameter.IndexOf('=');
                if (index == -1)
                {
                    valid = false;
                    return;
                }
                string value = parameter.Substring(index + 1);

                // [--PortName={port_name}]
                if (parameter.StartsWith("--PortName"))
                {
                    port = value;
                }

                // [--{Processor}={file_path}...]
                if (parameter.StartsWith("--Nav"))
                {
                    navPath = value;
                }
                if (parameter.StartsWith("--Gnss"))
                {
                    gnssPath = value;
                }
                if (parameter.StartsWith("--Imu"))
                {
                    imuPath = value;
                }

                // [--vnXml={file_path}]
                if (parameter.StartsWith("--vnXml"))
                {
                    vnxmlPath = value;
                }
            }
        }
    }

    class Program
    {
        static int Main(string[] args)
        {
            Parameters parameters = new Parameters(args);
            if (!parameters.valid)
            {
                Console.WriteLine(("Usage: " + parameters.usage));
                return 1;
            }

            Sensor sensor = new Sensor();
            sensor.Connect(parameters.port, 115200);
            if (!sensor.VerifySensorConnectivity)
            {
                throw new Exception($"Failed to connect to {portName}");
            }

            VNSDK.FirmwareUpdater firmwareUpdater = new VNSDK.FirmwareUpdater(ref sensor);

            Console.WriteLine($"Begin updating.");

            if (!string.IsNullOrEmpty(parameters.vnxmlPath))
            {
                Console.WriteLine($"Update firmware with vnxml: {parameters.vnxmlPath}");
                firmwareUpdater.UpdateFirmware(parameters.vnxmlPath);
            }
            else
            {
                Console.WriteLine($"Update NAV Firmware : {parameters.navPath}");
                Console.WriteLine($"Update GNSS Firmware: {parameters.gnssPath}");
                Console.WriteLine($"Update IMU Firmware : {parameters.imuPath}");
                firmwareUpdater.UpdateFirmware(parameters.navPath, parameters.gnssPath, parameters.imuPath);
            }
            sensor.Disconnect();
            return 0;
        }
    }
}

