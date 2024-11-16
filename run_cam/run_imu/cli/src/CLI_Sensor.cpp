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


#include "CLI_Sensor.hpp"

#include <conio.h>
#include <msclr/marshal.h>

#include <string>

using namespace msclr::interop;

namespace VNSDK
{
    void Sensor::Connect(String ^ portName, UInt32 baudRate)
    {
        marshal_context ^ context = gcnew marshal_context();
        VN::Error error = _sensor->connect(context->marshal_as<const char*>(portName), static_cast<VN::Registers::System::BaudRate::BaudRates>(baudRate));
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
        delete context;
    }

    void Sensor::AutoConnect(String ^ portName)
    {
        marshal_context ^ context = gcnew marshal_context();
        VN::Error error = _sensor->autoConnect(context->marshal_as<const char*>(portName));
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
        delete context;
    }

    bool Sensor::VerifySensorConnectivity()
    {
        return _sensor->verifySensorConnectivity();
    }

    String ^ Sensor::ConnectedPortName()
    {
        auto connectedPortName = _sensor->connectedPortName();
        if (!connectedPortName.has_value())
        {
            throw gcnew VnException(VN::Error::SerialPortClosed);
        }
        String ^ portName = msclr::interop::marshal_as<String ^>(connectedPortName.value().c_str());
        return portName;
    }
    
    uint32_t Sensor::ConnectedBaudRate()
    {
        auto connectedBaudRate = _sensor->connectedBaudRate();
        if (!connectedBaudRate.has_value())
        {
            throw gcnew VnException(VN::Error::SerialPortClosed);
        }
        return static_cast<uint32_t>(connectedBaudRate.value());
    }

    void Sensor::ChangeBaudRate(UInt32 baudRate)
    {
        VN::Error error = _sensor->changeBaudRate(static_cast<VN::Registers::System::BaudRate::BaudRates>(baudRate));
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::ChangeHostBaudRate(UInt32 baudRate)
    {
        VN::Error error = _sensor->changeHostBaudRate(static_cast<VN::Registers::System::BaudRate::BaudRates>(baudRate));
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::Disconnect()
    {
        _sensor->disconnect();
    }

    // ----------------------
    // Accessing Measurements
    // ----------------------

    bool Sensor::HasMeasurement()
    {
        return _sensor->hasMeasurement();
    }

    Nullable<CompositeData> Sensor::GetNextMeasurement()
    {
        auto measurement = _sensor->getNextMeasurement();
        if (measurement)
        {
            return CompositeData(*measurement);
        }
        return Nullable<CompositeData>();
    }

    Nullable<CompositeData> Sensor::GetMostRecentMeasurement()
    {
        auto measurement = _sensor->getMostRecentMeasurement();
        if (measurement)
        {
            return CompositeData(*measurement);
        }
        return Nullable<CompositeData>();
    }

    // ----------------------
    // Commands
    // ----------------------

    void Sensor::ReadRegister(VNSDK::Registers::Register ^ reg)
    {
        VN::Error error = _sensor->readRegister(reg->GetReference());
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::WriteRegister(VNSDK::Registers::Register ^ reg)
    {
        VN::Error error = _sensor->writeRegister((VN::ConfigurationRegister*)reg->GetReference());
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::WriteSettings()
    {
        VN::Error error = _sensor->writeSettings();
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::Reset()
    {
        VN::Error error = _sensor->reset();
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::RestoreFactorySettings()
    {
        VN::Error error = _sensor->restoreFactorySettings();
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::KnownMagneticDisturbance(uint8_t state)
    {
        VN::Error error = _sensor->knownMagneticDisturbance(static_cast<VN::KnownMagneticDisturbance::State>(state));
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::KnownAccelerationDisturbance(uint8_t state)
    {
        VN::Error error = _sensor->knownAccelerationDisturbance(static_cast<VN::KnownAccelerationDisturbance::State>(state));
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::SetInitialHeading(float heading)
    {
        VN::Error error = _sensor->setInitialHeading(heading);
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::SetInitialHeading(Ypr ypr)
    {
        VN::Ypr nativeYpr{ypr.yaw, ypr.pitch, ypr.roll};
        VN::Error error = _sensor->setInitialHeading(nativeYpr);
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::SetInitialHeading(Quaternion quat)
    {
        VN::Quat nativeQuat{VN::Vec3f{quat.vector.x, quat.vector.y, quat.vector.z}, quat.scalar};
        VN::Error error = _sensor->setInitialHeading(nativeQuat);
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::AsyncOutputEnable(uint8_t state)
    {
        VN::Error error = _sensor->asyncOutputEnable(static_cast<VN::AsyncOutputEnable::State>(state));
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    void Sensor::SetFilterBias()
    {
        VN::Error error = _sensor->setFilterBias();
        if (error != VN::Error::None)
        {
            throw gcnew VnException(error);
        }
    }

    // // Blocking call
    // void Sensor::SendCommand(String ^ commandToSend) {
    //   VN::AsciiMessage commandString;
    //   int length = commandToSend->Length;

    //   for (int i = 0; i < length; i++) {
    //     commandString.push_back(commandToSend[i]);
    //   }

    //   VN::Command command(commandString);

    //   VN::Error error = _sensor->sendCommand(
    //       &command, VN::Sensor::cmdWaitMode::blockingWithRetry);
    //   if (error != VN::Error::None) {
    //     VnException ^ pVnException = gcnew VnException;
    //     pVnException->error = error;
    //     throw pVnException;
    //   }
    // }

    // // None blocking call
    // void Sensor::SendCommand(Commands::Command^% commandToSend)
    // {
    // 	VN::Error error = _sensor->sendCommand(commandToSend->GetReference(),
    // VN::Sensor::cmdWaitMode::none); 	if (error != VN::Error::None)
    // 	{
    // 		VnException^ pVnException = gcnew VnException;
    // 		pVnException->error = error;
    // 		throw pVnException;
    // 	}
    // }

    void Sensor::SerialSend(String ^ msgToSend)
    {
        marshal_context ^ context = gcnew marshal_context();
        _sensor->serialSend(context->marshal_as<const char*>(msgToSend));
        delete context;
    }

    // ----------------------
    // Additional logging
    // ----------------------

    void Sensor::RegisterReceivedByteBuffer(ByteBuffer^ buffer)
    {
        _sensor->registerReceivedByteBuffer(buffer->GetReference());
    }

    void Sensor::DeregisterReceivedByteBuffer()
    {
        _sensor->deregisterReceivedByteBuffer();
    }

    void Sensor::RegisterSkippedByteBuffer(ByteBuffer^ buffer)
    {
        _sensor->registerSkippedByteBuffer(buffer->GetReference());
    }

    void Sensor::DeregisterSkippedByteBuffer()
    {
        _sensor->deregisterSkippedByteBuffer();
    }


    void Sensor::RegisterDataExporter(Exporter^ exporter)
    {
        VN::Error error = _sensor->subscribeToMessage(exporter->GetQueuePointer(), "VN", VN::Sensor::AsciiSubscriberFilterType::StartsWith);
        error = _sensor->subscribeToMessage(exporter->GetQueuePointer(), VN::Sensor::BinaryOutputMeasurements{}, VN::Sensor::FaSubscriberFilterType::AnyMatch);
    }
    
    void Sensor::DeregisterDataExporter(Exporter^ exporter)
    {
        _sensor->unsubscribeFromMessage(exporter->GetQueuePointer(), "VN");
        _sensor->unsubscribeFromMessage(exporter->GetQueuePointer(), VN::Sensor::BinaryOutputMeasurements{});
    }

} // namespace VNSDK
