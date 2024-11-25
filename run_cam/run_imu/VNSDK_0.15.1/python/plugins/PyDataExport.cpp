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

#include <cstdint>
#include <memory>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl/filesystem.h>
#include "Exporter.hpp"
#include "ExporterAscii.hpp"
#include "ExporterCsv.hpp"
#include "ExporterRinex.hpp"
#include "FileExporter.hpp"
#include "HAL/File.hpp"

namespace py = pybind11;

namespace VN {

void init_data_export(py::module& m) {

  py::module Plugins = m.def_submodule("Plugins", "Plugins Module");

  py::class_<Exporter>(Plugins, "Exporter")
    .def("getQueuePtr", &Exporter::getQueuePtr, py::return_value_policy::reference)
    .def("start", &Exporter::start)
    .def("stop", &Exporter::stop)
    .def("isLogging", &Exporter::isLogging);
  

  py::class_<ExporterCsv, Exporter>(Plugins, "ExporterCsv")
    .def(py::init<const Filesystem::FilePath&, bool>(), py::arg("path"), py::arg("enableSystemTimeStamps") = false)
    .def("exportToFile", &ExporterCsv::exportToFile);
  
  py::class_<ExporterRinex, Exporter>(Plugins, "ExporterRinex")
    .def(py::init<const Filesystem::FilePath&, const uint32_t>())
    .def("exportToFile", &ExporterRinex::exportToFile);
  
  py::class_<ExporterAscii, Exporter>(Plugins, "ExporterAscii")
    .def(py::init<const Filesystem::FilePath&>())
    .def("exportToFile", &ExporterAscii::exportToFile);

  py::class_<FileExporter>(Plugins, "FileExporter")
    .def(py::init<>())
    .def("processFile", &FileExporter::processFile)
    .def("addCsvExporter", [](FileExporter& f, const Filesystem::FilePath& path, bool enableSystemTimeStamps = false){
        f.addExporter(std::make_unique<ExporterCsv>(path, enableSystemTimeStamps));
      }
    )
    .def("addAsciiExporter", [](FileExporter& f, const Filesystem::FilePath& path) {
        f.addExporter(std::make_unique<ExporterAscii>(path));
      }
    )
    .def("addRinexExporter", [](FileExporter& f, const Filesystem::FilePath& path, const uint32_t gnssGroup){
        f.addExporter(std::make_unique<ExporterRinex>(path, gnssGroup));
      }
    );

  py::implicitly_convertible<py::str, Filesystem::FilePath>();
          
}

} // namespace VN

