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

#ifndef __CLI_SIMPLELOGGER_HPP__
#define __CLI_SIMPLELOGGER_HPP__

#include "CLI_ByteBuffer.hpp"

#pragma managed(push, off)
#include "SimpleLogger.hpp"
#pragma managed(pop)

using namespace System;

namespace VNSDK
{
    public ref class SimpleLogger
    {
    private:
        VN::SimpleLogger *_simpleLogger = nullptr;
        VN::Filesystem::FilePath *_filePath;

    public:
        
        SimpleLogger(ByteBuffer^ bufferToLog, String ^filePath)
        {
            marshal_context^ context = gcnew marshal_context();
            _filePath = new VN::Filesystem::FilePath(context->marshal_as<const char*>(filePath));
            delete context;

            _simpleLogger = new VN::SimpleLogger(*(bufferToLog->GetReference()), *_filePath);
        }

        ~SimpleLogger()
        {
            delete _simpleLogger;
            delete _filePath;
        }

        /// @brief start logging
        bool Start()
        {
            return _simpleLogger->start();
        }

        /// @brief stop logging
        void Stop()
        {
            _simpleLogger->stop();
        }

        /// @brief is logging
        bool IsLogging()
        {
            return _simpleLogger->isLogging();
        }

    }; // public ref class SimpleLogger
} // namespace VNSDK
#endif // __CLI_SIMPLELOGGER_HPP__
