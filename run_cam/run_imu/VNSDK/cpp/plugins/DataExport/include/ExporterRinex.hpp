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

#ifndef FILE_EXPORT_RINEX_HEADER_H
#define FILE_EXPORT_RINEX_HEADER_H

#include <fstream>
#include <set>
#include <ctime>
#include <cmath>
#include <limits>
#include <vector>
#include <numeric>

#include "Config.hpp"
#include "Exporter.hpp"
#include "HAL/File.hpp"
#include "Interface/CompositeData.hpp"
#include "TemplateLibrary/ByteBuffer.hpp"
#include "Implementation/BinaryHeader.hpp"
#include "Implementation/FaPacketProtocol.hpp"
#include "Implementation/QueueDefinitions.hpp"
#include "Implementation/MeasurementDatatypes.hpp"
#include "Implementation/BinaryMeasurementDefinitions.hpp"

namespace VN
{

static_assert((GNSS_GROUP_ENABLE & GNSS_GNSS1RAWMEAS_BIT) | (GNSS2_GROUP_ENABLE & GNSS2_GNSS2RAWMEAS_BIT), "GNSS raw meas is not enabled");

class ExporterRinex : public Exporter
{
public:
    ExporterRinex(const Filesystem::FilePath& fileName, const uint32_t gnssGroup) : Exporter(2048), _fileName(fileName), _gnssGroup(gnssGroup)
    {
        switch (gnssGroup)
        {
            case GNSS_BIT:
                _fileName = _fileName + "-1";
                break;
            case GNSS2_BIT:
                _fileName = _fileName + "-2";
            default:
                VN_ABORT();
        }
        _file.open(_fileName + ".tmp");
    }

    ~ExporterRinex() { finalize(); }

    void addPacketToProcess([[maybe_unused]] const std::shared_ptr<Packet> ptr) override
    {
        // _queue.push_back(ptr);
    }

    void finalize()
    {
        _file.close();

        _file.open(_fileName + ".obs");

        size_t bytesWritten = 0;

        time_t now = time(0);
        std::tm tm{};
        tm = *gmtime(&now);

        bytesWritten += sprintf(buffer + bytesWritten, "     3.03           OBSERVATION DATA    M: Mixed            RINEX VERSION / TYPE\n");
        bytesWritten += sprintf(buffer + bytesWritten, "%-40s%04d%02d%02d %02d%02d%02d UTC %-20s\n", "VNSDK File Export", tm.tm_year + 1900, tm.tm_mon + 1,
                                tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, "GM / RUN BY / DATE");

        bytesWritten += sprintf(buffer + bytesWritten, "%60c%-20s\n", ' ', "MARKER NAME");
        bytesWritten += sprintf(buffer + bytesWritten, "%60c%-20s\n", ' ', "MARKER NUMBER");
        bytesWritten += sprintf(buffer + bytesWritten, "%60c%-20s\n", ' ', "OBSERVER / AGENCY");
        bytesWritten += sprintf(buffer + bytesWritten, "%60c%-20s\n", ' ', "REC # / TYPE / VERS");
        bytesWritten += sprintf(buffer + bytesWritten, "%60c%-20s\n", ' ', "ANT # / TYPE");
        bytesWritten += sprintf(buffer + bytesWritten, "%14.4f%14.4f%14.4f                  %-20s\n", 0.0, 0.0, 0.0, "APPROX POSITION XYZ");
        bytesWritten += sprintf(buffer + bytesWritten, "%14.4f%14.4f%14.4f                  %-20s\n", 0.0, 0.0, 0.0, "ANTENNA: DELTA H/E/N");

        for (const auto sys : sysId)
        {
            size_t offset = bytesWritten;
            const auto it = _signalMap.find(sys);
            if (it == _signalMap.end()) continue;

            std::vector<uint16_t> tmp(it->second.begin(), it->second.end());
            bytesWritten += sprintf(buffer + bytesWritten, "%c%5d", it->first, tmp.size() * 4);

            for (const auto signal : tmp)
            {
                const uint8_t chan = chanCode[(signal & 0x0F)];
                const uint8_t freq = ((signal >> 8) & 0x0F);
                bytesWritten += sprintf(buffer + bytesWritten, " C%i%c L%i%c D%i%c S%i%c", freq, chan, freq, chan, freq, chan, freq, chan);
            }

            bytesWritten += sprintf(buffer + bytesWritten, "%*c%-20s\n", static_cast<int>(60 - (bytesWritten - offset)), ' ', "SYS / # / OBS TYPES");
        }

        tm = *gmtime(&firstTimeGps);
        bytesWritten += sprintf(buffer + bytesWritten, "%6d%6d%6d%6d%6d%5d.0000000%8s         %-20s\n", tm.tm_year + 1900, tm.tm_mon, tm.tm_mday, tm.tm_hour,
                                tm.tm_min, tm.tm_sec, "GPS", "TIME OF FIRST OBS");
        tm = *gmtime(&lastTimeGps);
        bytesWritten += sprintf(buffer + bytesWritten, "%6d%6d%6d%6d%6d%5d.0000000%8s         %-20s\n", tm.tm_year + 1900, tm.tm_mon, tm.tm_mday, tm.tm_hour,
                                tm.tm_min, tm.tm_sec, "GPS", "TIME OF LAST OBS");

        bytesWritten += sprintf(buffer + bytesWritten, "%-60c%-20s\n", 'G', "SYS / PHASE SHIFT");
        bytesWritten += sprintf(buffer + bytesWritten, "%-60c%-20s\n", 'E', "SYS / PHASE SHIFT");
        bytesWritten += sprintf(buffer + bytesWritten, "%-60c%-20s\n", ' ', "END OF HEADER");

        _file.write(buffer, bytesWritten);

        std::ifstream dataFile(_fileName + ".tmp");
        _file << dataFile.rdbuf();
        dataFile.close();
        std::remove((_fileName + ".tmp").c_str());
    }

    void exportToFile() override
    {
        while (_queue.size() > 0)
        {
            const auto p = _queue.get();
            if (!p) { return; }

            if (!p->details.faMetadata.header.contains(_gnssGroup, static_cast<uint32_t>(GNSS_GNSS1RAWMEAS_BIT))) { return; }

            ByteBuffer byteBuffer(p->buffer, p->size, p->size);

            const auto cdOpt = FaPacketProtocol::parsePacket(byteBuffer, 0, p->details.faMetadata, Config::PacketDispatchers::cdEnabledMeasTypes);
            if (!cdOpt) return;
            const auto cd = cdOpt.value();

            const GnssRawMeas& gnssRawMeas = [](const CompositeData& cd, const uint8_t _gnssGroup) -> const GnssRawMeas&
            {
                switch (_gnssGroup)
                {
#if (GNSS_GROUP_ENABLE & GNSS_GNSS1RAWMEAS_BIT)
                    case GNSS_BIT:
                        return cd.gnss.gnss1RawMeas.value();
#endif
#if (GNSS2_GROUP_ENABLE & GNSS2_GNSS2RAWMEAS_BIT)
                    case GNSS2_BIT:
                        return cd.gnss2.gnss2RawMeas.value();
#endif
                    default:
                        VN_ABORT();
                }
            }(cd, _gnssGroup);

            std::vector<int> index(gnssRawMeas.numMeas);
            std::iota(index.begin(), index.end(), 0);

            // sort based on sys -> svId -> freq
            std::sort(index.begin(), index.end(),
                      [&](int i, int j)
                      {
                          return static_cast<uint64_t>((gnssRawMeas.sys[i] << 24) | (gnssRawMeas.svId[i] << 16) | (gnssRawMeas.band[i] << 8)) <
                                 static_cast<uint64_t>((gnssRawMeas.sys[j] << 24) | (gnssRawMeas.svId[j] << 16) | (gnssRawMeas.band[j] << 8));
                      });

            for (size_t i = 0; i < gnssRawMeas.numMeas; i++)
            {
                _signalMap[sysId[gnssRawMeas.sys[i]]].insert((gnssRawMeas.band[i] << 8) | (gnssRawMeas.chan[i]));
            }

            size_t bytesToWrite = 0;

            constexpr uint64_t gpsWeekToSeconds = 7 * 24 * 3600;

            double seconds = 0;
            double timeleft = std::modf(gnssRawMeas.tow, &seconds);
            double timeTarget = static_cast<uint64_t>((timeleft * 10) + 0.5) / 10.0;
            if (timeTarget >= 1.0)
            {
                timeTarget -= 1.0;
                seconds += 1;
                timeleft = gnssRawMeas.tow - seconds;
            }
            uint64_t subseconds = static_cast<uint64_t>(timeTarget * 10000000);

            double compMeters = (timeleft - timeTarget) * GPS_C;

            // First GPS Epoch: January 6 1980 00:00:00
            // FIrst UTC Epoch: January 1 1970 00:00:00
            // gmtime uses UTC time, so we must add an offset to get the equivalent GPS Time
            // 315964800 = (10 * 365 + 7)*24*3600
            time_t timeGps = static_cast<uint64_t>(seconds) + gnssRawMeas.week * gpsWeekToSeconds + 315964800;

            firstTimeGps = std::min(firstTimeGps, timeGps);
            lastTimeGps = timeGps;

            std::tm tm{};
            tm = *gmtime(&timeGps);

            bytesToWrite += std::sprintf(buffer, "> %4d %2d %2d %2d %2d %2d.%07d  0 %2d\n", tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min,
                                         tm.tm_sec, static_cast<int>(subseconds), gnssRawMeas.numMeas);

            for (size_t i = 0; i < index.size(); i++)
            {
                // we are either at the first frquency or we are at the second
                auto idx = index[i];
                if (gnssRawMeas.band[idx] == 1)
                {
                    bytesToWrite += sprintf(buffer + bytesToWrite, "%c%02d %14.3f %14.3f %14.3f %11d.000", sysId[gnssRawMeas.sys[index[i]]],
                                            gnssRawMeas.svId[index[i]] % 100, gnssRawMeas.pr[index[i]] - compMeters, gnssRawMeas.cp[index[i]],
                                            gnssRawMeas.dp[index[i]], gnssRawMeas.cno[index[i]]);

                    if ((i + 1) >= index.size()) break;  // end of list

                    // lets check if we have the L2 frequency with the same satellite

                    if ((gnssRawMeas.sys[index[i + 1]] == gnssRawMeas.sys[index[i]]) && (gnssRawMeas.svId[index[i]] == gnssRawMeas.svId[index[i + 1]]))
                    {
                        i++;
                        bytesToWrite += sprintf(buffer + bytesToWrite, "    %14.3f %14.3f %14.3f %11d.000\n", gnssRawMeas.pr[index[i]],
                                                gnssRawMeas.cp[index[i]], gnssRawMeas.dp[index[i]], gnssRawMeas.cno[index[i]]);
                    }
                    else { bytesToWrite += sprintf(buffer + bytesToWrite, "\n"); }
                    // we only have the L2 frequency
                }
                else
                {
                    bytesToWrite += sprintf(buffer + bytesToWrite, "%c%02d%*c %14.3f %14.3f %14.3f %11d.000\n", sysId[gnssRawMeas.sys[index[i]]],
                                            gnssRawMeas.svId[index[i]] % 100, 65, ' ', gnssRawMeas.pr[index[i]], gnssRawMeas.cp[index[i]],
                                            gnssRawMeas.dp[index[i]], gnssRawMeas.cno[index[i]]);
                }
            }

            bytesToWrite += sprintf(buffer + bytesToWrite, "\n");

            _file.write(buffer, bytesToWrite);
        }
    }

private:
    char buffer[4096];
    static constexpr double GPS_C = 299792458.0;
    static constexpr std::array<char, 9> sysId = {'G', 'S', 'E', 'C', 'x', 'J', 'R', 'I', 'L'};
    static constexpr std::array<char, 15> chanCode = {'P', 'C', 'D', 'Y', 'M', 'N', 'A', 'B', 'I', 'Q', 'S', 'L', 'X', 'W', 'Z'};

    time_t firstTimeGps = std::numeric_limits<time_t>::max();
    time_t lastTimeGps = 0;

    Filesystem::FilePath _fileName;
    std::ofstream _file;
    const uint32_t _gnssGroup;

    std::unordered_map<char, std::set<uint16_t>> _signalMap;
};

}  // namespace VN

#endif  // FILE_EXPORT_RINEX_HEADER_H
