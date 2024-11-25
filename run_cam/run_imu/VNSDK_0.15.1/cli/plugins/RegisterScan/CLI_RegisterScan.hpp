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

#ifndef __CLI_REGISTERSCAN_HPP__
#define __CLI_REGISTERSCAN_HPP__

#include "CLI_Sensor.hpp"

#pragma managed(push, off)
#include "RegisterScan.hpp"
#pragma managed(pop)

using namespace System;

namespace VNSDK
{
    public ref class SensorConfigurator
    {
    private:
        VN::SensorConfigurator *_configurator;

    public:
        SensorConfigurator(Sensor^% sensor, String^ port)
        {
            std::string nativePortName = msclr::interop::marshal_as<std::string>(port);

            _configurator = new VN::SensorConfigurator(sensor->GetNativeInstance(), nativePortName);
        }

        ~SensorConfigurator()
        {
            delete _configurator;
        }

        void SaveConfiguration(String^ path)
        {
            std::string unmanagedPath = msclr::interop::marshal_as<std::string>(path);
            if (_configurator->SaveConfiguration(unmanagedPath)) {
                throw gcnew System::Exception("Register Scan save config failed");
            }
        }

        void LoadConfiguration(String^ path)
        {
            std::string unmanagedPath = msclr::interop::marshal_as<std::string>(path);
            if (_configurator->LoadConfiguration(unmanagedPath)) {
                throw gcnew System::Exception("Register Scan load config failed");
            }
        }
    };
} // namespace VNSDK

#endif // __CLI_REGISTERSCAN_HPP__
