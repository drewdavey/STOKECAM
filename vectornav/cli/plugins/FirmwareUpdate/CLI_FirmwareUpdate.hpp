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

#ifndef __CLI__FIRMWAREUPDATE_HPP__
#define __CLI__FIRMWAREUPDATE_HPP__

#pragma managed(push, off)
#include "FirmwareUpdater.hpp"
#pragma managed(pop)

#include <msclr/marshal_cppstd.h>

using namespace System;
namespace VNSDK
{
public
ref class FirmwareUpdater
{
  private:
    VN::FirmwareUpdater &_firmwareUpdater = VN::FirmwareUpdater();
    Sensor ^ _sensor = nullptr;
    VN::Sensor::BaudRate _firmwareBaudRate = VN::Sensor::BaudRate::Baud115200;
    VN::Sensor::BaudRate _bootloaderBaudRate = VN::Sensor::BaudRate::Baud115200;

  public:
    FirmwareUpdater(Sensor ^ % sensor)
    {
        _sensor = sensor;
    }

    void UpdateFirmware(String ^ vnxmlPath)
    {
        std::string unmanagedPath = msclr::interop::marshal_as<std::string>(vnxmlPath);
        const bool failed = _firmwareUpdater.updateFirmware(&_sensor->GetNativeInstance(), (VN::Filesystem::FilePath)unmanagedPath,
            { _firmwareBaudRate, _bootloaderBaudRate });
            if (failed) {
                throw gcnew System::Exception("Firmware update failed");
            }
    }

    void UpdateFirmware(String ^ navPath, String ^ gnssPath, String ^ imuPath)
    {
        std::string unmanagedNavPath = msclr::interop::marshal_as<std::string>(navPath);
        std::string unmanagedGnssPath = msclr::interop::marshal_as<std::string>(gnssPath);
        std::string unmanagedImuPath = msclr::interop::marshal_as<std::string>(imuPath);
        bool failed = true;
        VN::FirmwareUpdater::FilePaths filePaths;

        if (navPath->Length > 0)
        {
            if (filePaths.push_back({unmanagedNavPath, VN::FirmwareUpdater::Processor::Nav})) { throw gcnew System::Exception("Failed to push filepaths"); }
        }
        if (gnssPath->Length > 0)
        {
            if (filePaths.push_back({unmanagedGnssPath, VN::FirmwareUpdater::Processor::Gnss})) { throw gcnew System::Exception("Failed to push filepaths"); }
        }
        if (imuPath->Length > 0)
        {
            if (filePaths.push_back({unmanagedImuPath, VN::FirmwareUpdater::Processor::Imu})) { throw gcnew System::Exception("Failed to push filepaths"); }
        }

        if (!filePaths.empty())
        {
            failed = _firmwareUpdater.updateFirmware(
                &_sensor->GetNativeInstance(),
                filePaths,
                { _firmwareBaudRate, _bootloaderBaudRate });
        }


        if (failed) {
            throw gcnew System::Exception("Firmware update failed");
        }
    }
};
} // namespace VNSDK

#endif // __CLI_FIRMWAREUPDATE_HPP__
