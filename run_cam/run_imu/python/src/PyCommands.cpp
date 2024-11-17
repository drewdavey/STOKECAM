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

#include <pybind11/chrono.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "Interface/Command.hpp"
#include "Interface/Commands.hpp"

namespace py = pybind11;
namespace VN {

void init_commands(py::module& m) {
  py::module commands = m.def_submodule("Commands", "Commands submodule");

  py::class_<Command>(commands, "Command")
      .def(py::init<const Command&>())
      .def(py::init<AsciiMessage&, uint8_t>(), py::arg("commandString") = "",
           py::arg("numCharToMatch") = 3)
      .def("isAwaitingResponse", &Command::isAwaitingResponse)
      .def("hasValidResponse", &Command::hasValidResponse)
      .def("getError", &Command::getError)
      .def("getResponse", &Command::getResponse);

  py::class_<WriteSettings, Command>(commands, "WriteSettings")
      .def(py::init<>());

  py::class_<RestoreFactorySettings, Command>(commands,
                                              "RestoreFactorySettings")
      .def(py::init<>());

  py::class_<Reset, Command>(commands, "Reset").def(py::init<>());

  py::class_<FirmwareUpdate, Command>(commands, "FirmwareUpdate")
      .def(py::init<>());

  py::class_<SetInitialHeading, Command>(commands, "SetInitialHeading")
      .def(py::init<float>());

  py::class_<SetFilterBias, Command>(commands, "SetFilterBias")
      .def(py::init<>());

  py::class_<KnownMagneticDisturbance, Command> knownMagneticDisturbance(
      commands, "KnownMagneticDisturbance");

  py::enum_<KnownMagneticDisturbance::State>(knownMagneticDisturbance, "State")
      .value("NotPresent", KnownMagneticDisturbance::State::NotPresent)
      .value("Present", KnownMagneticDisturbance::State::Present);

  knownMagneticDisturbance.def(py::init<KnownMagneticDisturbance::State>());

  py::class_<KnownAccelerationDisturbance, Command>
      knownAccelerationDisturbance(commands, "KnownAccelerationDisturbance");

  knownAccelerationDisturbance.def(
      py::init<KnownAccelerationDisturbance::State>());

  py::enum_<KnownAccelerationDisturbance::State>(knownAccelerationDisturbance,
                                                 "State")
      .value("NotPresent", KnownAccelerationDisturbance::State::NotPresent)
      .value("Present", KnownAccelerationDisturbance::State::Present);

  py::class_<AsyncOutputEnable, Command> asyncOutputEnable(commands,
                                                           "AsyncOutputEnable");

  py::enum_<AsyncOutputEnable::State>(asyncOutputEnable, "State")
      .value("Disable", AsyncOutputEnable::State::Disable)
      .value("Enable", AsyncOutputEnable::State::Enable);

  asyncOutputEnable.def(py::init<AsyncOutputEnable::State>());
}

}  // namespace VN
