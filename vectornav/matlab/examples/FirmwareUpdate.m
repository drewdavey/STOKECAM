% The MIT License (MIT)
% 
%  VectorNav Software Development Kit (v0.15.1)
% Copyright (c) 2024 VectorNav Technologies, LLC
% 
% 
% Permission is hereby granted, free of charge, to any person obtaining a copy
% of this software and associated documentation files (the "Software"), to deal
% in the Software without restriction, including without limitation the rights
% to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
% copies of the Software, and to permit persons to whom the Software is
% furnished to do so, subject to the following conditions:
% 
% The above copyright notice and this permission notice shall be included in
% all copies or substantial portions of the Software.
% 
% THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
% IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
% FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
% AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
% LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
% OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
% THE SOFTWARE.

disp('Starting Firmware Update example.')

vnsdkAssembly = NET.addAssembly([pwd '\..\..\net\VnSdk_Net.dll']); % change to file path
import VNSDK.* % Get rid of 'VNSDK' namespace qualifications

if exist('sensor','var')
    sensor.Disconnect();  % We don't want to replace an object that already exists, and may keep the serial port locked
else
    sensor = Sensor();
end

if ~exist('port_name', 'var')
    port_name = 'COM11'; % Change the sensor port name to the COM port of your local machine
end
if ~exist('Nav', 'var')
    Nav = fullfile(pwd, 'ReferenceModels_v3.vn100.vnx'); % Change this to your sensor
else
    fprintf('Loading Nav firmware from %s\n', Nav);
end
if ~exist('Gnss', 'var')
    Gnss = '';
else
    fprintf('Loading Gnss firmware from %s\n', Gnss);
end
if ~exist('Imu', 'var')
    Imu = '';
else
    fprintf('Loading Imu firmware from %s\n', Imu);
end
if ~exist('vnXml', 'var')
    vnXml = '';
else
    fprintf('Loading VnXml from %s\n', vnXml);
end

sensor.Connect(port_name, 115200); % Firmware update requires 115200 baud
if (~sensor.VerifySensorConnectivity())
    error('Could not verify connectivity of %s', port_name);
end
fprintf('Connected to %s at %s\n', sensor.ConnectedPortName(), sensor.ConnectedBaudRate())


firmwareUpdater = FirmwareUpdater(sensor);
if ~isempty(vnXml)
    firmwareUpdater.UpdateFirmware(vnXml);
else
    firmwareUpdater.UpdateFirmware(Nav, Gnss, Imu);
end

sensor.Disconnect();
fprintf('Firmware update example complete.\n');