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

#ifndef HAL_SERIALLINUX_HPP
#define HAL_SERIALLINUX_HPP

#include <unistd.h>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <optional>
#include <sys/ioctl.h>  // Used for exclusive locking
#include <termios.h>
#include <linux/serial.h>
#include <fcntl.h>

#include "HAL/Serial_Base.hpp"
#include "Interface/Errors.hpp"
#include "Serial_Base.hpp"

namespace VN
{

class Serial : public Serial_Base
{
public:
    using Serial_Base::Serial_Base;

    // ***********
    // Port access
    // ***********
    Error open(const PortName& portName, const uint32_t baudRate) noexcept override final;
    void close() noexcept override;
    bool isSupportedBaudRate(const uint32_t baudRate) const noexcept override;
    Error changeBaudRate(const uint32_t baudRate) noexcept override final;

    // ***************
    // Port read/write
    // ***************
    Error getData() noexcept override final;
    Error send(const AsciiMessage& message) noexcept override final;

private:
    // ***********
    // Port access
    // ***********
    int _portHandle = 0;
    bool _configurePort(const tcflag_t osBaudRate);

    // ***************
    // Port read/write
    // ***************
    void _flush();
    static std::optional<tcflag_t> _getOsBaudRate(uint32_t baudRate);
    std::array<uint8_t, _numBytesToReadPerGetData> _inputBuffer = {0};
};

// ######################
//     Implementation
// ######################

inline Error Serial::open(const PortName& portName, const uint32_t baudRate) noexcept
{
    if (_isOpen) { close(); }

    _portHandle = ::open(portName.c_str(), O_RDWR | O_NOCTTY);

    if (_portHandle == -1)
    {
        switch (errno)
        {
            case EACCES:
            case EBUSY:
                return Error::AccessDenied;
            case ENXIO:
            case ENOTDIR:
            case ENOENT:
                return Error::InvalidPortName;
            default:
                return Error::UnexpectedSerialError;
        }
    }

    ioctl(_portHandle, TIOCEXCL);

    auto osBaudRate = _getOsBaudRate(baudRate);
    if (!osBaudRate.has_value()) { return Error::UnsupportedBaudRate; }
    if (_configurePort(osBaudRate.value())) { return Error::UnexpectedSerialError; }

    _flush();
    _portName = portName;
    _baudRate = baudRate;
    _isOpen = true;
    return Error::None;
}

inline void Serial::close() noexcept
{
    ioctl(_portHandle, TIOCNXCL);
    ::close(_portHandle);
    _isOpen = false;
}

inline bool Serial::isSupportedBaudRate(const uint32_t baudRate) const noexcept
{
    auto osBaudRate = _getOsBaudRate(baudRate);
    return osBaudRate.has_value();
}

inline Error Serial::changeBaudRate(const uint32_t baudRate) noexcept
{
    if (!_isOpen) { return Error::SerialPortClosed; }
    _flush();

    auto osBaudRate = _getOsBaudRate(baudRate);
    if (!osBaudRate.has_value()) { return Error::UnsupportedBaudRate; }
    if (_configurePort(osBaudRate.value())) { return Error::UnexpectedSerialError; }

    _baudRate = baudRate;
    return Error::None;
}

inline Error Serial::getData() noexcept
{
    if (!_isOpen) { return Error::SerialPortClosed; }

    size_t numBytesAvailable = 0;
    ioctl(_portHandle, FIONREAD, &numBytesAvailable);
    if (numBytesAvailable == 0) { return Error::None; }

    ssize_t numBytesActuallyRead = ::read(_portHandle, &_inputBuffer[0], std::min(numBytesAvailable, _inputBuffer.size()));
    if (numBytesActuallyRead == -1) { return Error::SerialReadFailed; }

    if (_byteBuffer.put(&_inputBuffer[0], static_cast<size_t>(numBytesActuallyRead))) { return Error::PrimaryBufferFull; }
    return Error::None;
}

inline Error Serial::send(const AsciiMessage& message) noexcept
{
    if (!_isOpen) { return Error::SerialPortClosed; }

    ssize_t numOfBytesWritten = ::write(_portHandle, message.c_str(), message.length());
    if (numOfBytesWritten == -1) { return Error::SerialWriteFailed; }
    return Error::None;
}

inline std::optional<tcflag_t> Serial::_getOsBaudRate(uint32_t baudRate)
{
    tcflag_t baudRateFlag;
    switch (baudRate)
    {
        case 9600:
            baudRateFlag = B9600;
            break;
        case 19200:
            baudRateFlag = B19200;
            break;
        case 38400:
            baudRateFlag = B38400;
            break;
        case 57600:
            baudRateFlag = B57600;
            break;
        case 115200:
            baudRateFlag = B115200;
            break;
        case 230400:
            baudRateFlag = B230400;
            break;
        case 460800:
            baudRateFlag = B460800;
            break;
        case 921600:
            baudRateFlag = B921600;
            break;
        default:
            return std::nullopt;
    }
    return std::make_optional(baudRateFlag);
}

inline bool Serial::_configurePort(const tcflag_t osBaudRate)
{
    termios portSettings;
    if (tcgetattr(_portHandle, &portSettings) == -1) { return true; }

    portSettings.c_cflag |= (CLOCAL | CREAD);
    portSettings.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
    portSettings.c_oflag &= ~OPOST;
    portSettings.c_lflag &= ~(ICANON | ECHO | ECHOE | ECHOK | ECHONL | ISIG | IEXTEN);
    portSettings.c_cflag &= ~(CSIZE | PARENB);
    portSettings.c_cflag |= CS8;

    cfsetispeed(&portSettings, osBaudRate);
    cfsetospeed(&portSettings, osBaudRate);

    // optimize serial port for low latency communication
    struct serial_struct serial;
    ioctl(_portHandle, TIOCGSERIAL, &serial);
    serial.flags |= ASYNC_LOW_LATENCY;
    ioctl(_portHandle, TIOCSSERIAL, &serial);

    tcsetattr(_portHandle, TCSANOW, &portSettings);

    return false;
}

inline void Serial::_flush()
{
    tcdrain(_portHandle);
    tcflush(_portHandle, TCIFLUSH);
}
}  // Namespace VN

#endif  // HAL_SERIALLINUX_HPP