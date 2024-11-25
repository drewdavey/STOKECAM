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
using System.IO;
using VNSDK;

namespace DataExportFromFile
{
    class Program
    {
        static int Main(string[] args)
        {
            Console.WriteLine($"Data Export From File example.");
            string inputFilePath = "";

            if (args.Length > 0)
            {
                inputFilePath = args[1];
            }
            else
            {
                Environment.CurrentDirectory = "../../../../";
                inputFilePath = System.IO.Path.Combine(Directory.GetCurrentDirectory(), "DataExportFromFile.bin");
            }

            Console.WriteLine($"Exporting from {inputFilePath}.");

            ExporterAscii asciiExporter = new ExporterAscii(inputFilePath);
            FileExporter fileExporter = new FileExporter();

            fileExporter.AddExporter(asciiExporter);

            if (fileExporter.ProcessFile(inputFilePath))
            {
                Console.WriteLine("Error: File processing failed.");
                return 1;
            }

            asciiExporter.ExportToFile();

            Console.WriteLine($"Data Export From File example complete.");
            return 0;
        }
    }
}

