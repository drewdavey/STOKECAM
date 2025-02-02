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

#ifndef __CLI_EXPORTER_HPP__
#define __CLI_EXPORTER_HPP__

#pragma managed(push, off)
#include "Exporter.hpp"
#include "ExporterAscii.hpp"
#include "ExporterCsv.hpp"
//#include "ExporterImr.hpp" // Not fully working yet
//#include "ExporterRinex.hpp" // Needs GNSS Raw Measurements
#include "FileExporter.hpp"
#pragma managed(pop)

using namespace System;

namespace VNSDK
{

    public ref class Exporter
    {
    protected:
        VN::Exporter *_exporter;
        VN::Filesystem::FilePath* _filePath;

    public:
        Exporter(String^ filePath)
        {
            marshal_context^ context = gcnew marshal_context();
            _filePath = new VN::Filesystem::FilePath(context->marshal_as<const char*>(filePath));
            delete context;
        }

        virtual ~Exporter()
        {
            if (_exporter != nullptr)
            {
                delete _exporter;
            }

            delete _filePath;
        };

        VN::Exporter* GetRawExporter()
        {
            return _exporter;
        }

        VN::PacketQueue_Interface* GetQueuePointer()
        {
            return _exporter->getQueuePtr();
        }

        /// @brief start logging
        bool Start()
        {
            return _exporter->start();
        }

        /// @brief stop logging
        void Stop()
        {
            _exporter->stop();
        }

        /// @brief is logging
        bool IsLogging()
        {
            return _exporter->isLogging();
        }

        /// @brief export data to a file
        void ExportToFile()
        {
            _exporter->exportToFile();
        }

        /// @brief finalize the file before exporting
        virtual void FinalizeFile()
        {
        }

    };

    public ref class ExporterAscii : Exporter
    {
        public:
        
        ExporterAscii(String ^filePath) : Exporter(filePath)
        {
            _exporter = new VN::ExporterAscii(*_filePath);
        }

    }; // public ref class ExporterAscii

    public ref class ExporterCsv : Exporter
    {
    public:
        
        ExporterCsv(String^ filePath) : Exporter(filePath)
        {
            _exporter = new VN::ExporterCsv(*_filePath, false);
        }

        ExporterCsv(String^ filePath, bool enableSystemTimeStamps) : Exporter(filePath)
        {
            _exporter = new VN::ExporterCsv(*_filePath, enableSystemTimeStamps);
        }

    }; // public ref class ExporterAscii

    //public ref class ExporterImr : Exporter
    //{
    //public:
    //    
    //    ExporterImr(String ^filePath) : Exporter(filePath)
    //    {
    //        _exporter = new VN::ExporterImr(*_filePath);
    //    }

    //    virtual void FinalizeFile() override
    //    {
    //        ((VN::ExporterImr *)_exporter)->finalize();
    //    }

    //}; // public ref class ExporterAscii

    //public ref class ExporterRinex : Exporter
    //{
    //public:
    //    
    //    ExporterRinex(String ^filePath, UInt32 gnssGroup) : Exporter(filePath)
    //    {
    //        _exporter = new VN::ExporterRinex(*_filePath, gnssGroup);
    //    }

    //}; // public ref class ExporterAscii


    public ref class FileExporter
    {
    private:
        VN::FileExporter *_fileExporter = nullptr;
        VN::Filesystem::FilePath* _filePath;

    public:
        FileExporter()
        {
            _fileExporter = new VN::FileExporter();
        }

        ~FileExporter()
        {
            delete _fileExporter;
        }

        bool AddExporter(Exporter^ exporter)
        {
            return _fileExporter->addExporter(std::unique_ptr<VN::Exporter>(exporter->GetRawExporter()));
        }

        bool ProcessFile(String^ filePath)
        {
            marshal_context^ context = gcnew marshal_context();
            _filePath = new VN::Filesystem::FilePath(context->marshal_as<const char*>(filePath));
            delete context;

            return _fileExporter->processFile(*_filePath);
        }

    };
} // namespace VNSDK
#endif // __CLI_EXPORTER_HPP__
