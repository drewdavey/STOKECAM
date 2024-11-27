# Last updated: 2024-10-03
##################################
# Housekeeping funcs for the stereo camera system
##################################

import os
import time
import yaml
from vectornav import *
from datetime import datetime, timezone, timedelta

def setup_logging():
    fdir = f"../../DATA/{datetime.now(timezone.utc).strftime('%Y%m%d')}/"
    if not os.path.exists(fdir):
        os.makedirs(fdir)
    fname_log = os.path.join(fdir, f"{datetime.now(timezone.utc).strftime('%Y%m%d')}_LOG.txt")
    if not os.path.exists(fname_log) or os.stat(fname_log).st_size == 0:
        header_block = """
########################################################################################################################
#                                                                                                                      #
#            *****      *******      ****      *    *     *******       ******         *             *   *             # 
#           *              *        *    *     *  *       *            *              * *           * * * *            #
#            *****         *        *    *     * *        ****        *              *   *         *   *   *           #
#                 *        *        *    *     *  *       *            *            *******       *         *          #
#            *****         *         ****      *    *     *******       ******     *       *     *           *         #   
#                                                                                                                      #
########################################################################################################################
                    # STereo camera system for Overturning wave KinEmatiCs and dynAMics #
                    #          Developed at Scripps Institution of Oceanography         #
                    #                       Date: {}                   #
                    #####################################################################
""".format(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
        with open(fname_log, 'w') as log:
            tstr = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            log.write(f"Startup complete - created log for {tstr}.\n\n")
            log.write(header_block)
            log.write("\n\n\n")
    return fdir, fname_log

def read_inputs_yaml(fname_log):
    inputs_path = '../inputs.yaml'
    with open(fname_log, 'a') as log:
        try:
            with open(inputs_path, 'r') as file:
                inputs = yaml.safe_load(file)
            return inputs
        except FileNotFoundError:
            log.write(f"Error: The file {inputs_path} was not found.")
            return None
        except yaml.YAMLError as exc:
            log.write(f"Error parsing YAML file: {exc}")
            return None
        
def create_dirs(fdir, mode):
    session = datetime.now(timezone.utc).strftime('%H%M%S_' + mode)
    fdir_out = os.path.join(fdir, session + '/')
    fdir_cam0 = os.path.join(fdir_out, 'cam0/')
    fdir_cam1 = os.path.join(fdir_out, 'cam1/')
    os.makedirs(fdir_cam0, exist_ok=True)
    os.makedirs(fdir_cam1, exist_ok=True)
    fname_imu = f'{fdir_out}IMU_{session}.txt'
    return fdir_out, fdir_cam0, fdir_cam1, fname_imu

def config_VN200_output(portName):
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 
    
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    #### CONFIGURE ADOR AND AODF 
    asyncDataOutputType = Registers.AsyncOutputType()
    asyncDataOutputType.ador = Registers.AsyncOutputType.Ador.YPR
    asyncDataOutputType.serialPort = Registers.AsyncOutputType.SerialPort.Serial1
    s.writeRegister(asyncDataOutputType)
    print(f"{tstr}:     ADOR Configured\n")
    asyncDataOutputFreq= Registers.AsyncOutputFreq()
    asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate40Hz
    asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1
    s.writeRegister(asyncDataOutputFreq)
    print(f"{tstr}:     ADOF Configured\n")
    
    #### CONFIGURE THE BINARY OUTPUT
    binaryOutput1Register = Registers.BinaryOutput1()
    binaryOutput1Register.rateDivisor = 100
    binaryOutput1Register.asyncMode.serial1 = 1
    binaryOutput1Register.asyncMode.serial2 = 0
    binaryOutput1Register.time.timeUtc = 1
    binaryOutput1Register.common.timeStartup = 1
    binaryOutput1Register.attitude.ypr = 1
    binaryOutput1Register.common.accel = 1
    binaryOutput1Register.gnss.gnss1PosLla = 1
    binaryOutput1Register.ins.posLla = 1
    binaryOutput1Register.time.timeStartup = 1
    binaryOutput1Register.time.timeGps = 1
    binaryOutput1Register.time.timeGpsTow = 1
    binaryOutput1Register.time.timeGpsWeek = 1
    binaryOutput1Register.time.timeSyncIn = 1
    binaryOutput1Register.time.timeGpsPps = 1
    binaryOutput1Register.imu.imuStatus = 1
    binaryOutput1Register.imu.temperature = 1
    binaryOutput1Register.imu.pressure = 1
    binaryOutput1Register.imu.mag = 1
    binaryOutput1Register.attitude.quaternion = 1
    binaryOutput1Register.imu.accel = 1
    binaryOutput1Register.imu.uncompMag = 0
    binaryOutput1Register.imu.uncompAccel = 0
    binaryOutput1Register.gnss.gnss1TimeUtc = 0
    binaryOutput1Register.gnss.gnss1NumSats = 0
    binaryOutput1Register.gnss.gnss1Fix = 0
    binaryOutput1Register.gnss.gnss1PosEcef = 0
    binaryOutput1Register.gnss.gnss1PosUncertainty = 0
    binaryOutput1Register.gnss.gnss1TimeUncertainty = 0
    binaryOutput1Register.attitude.magNed = 0
    binaryOutput1Register.ins.insStatus = 0
    binaryOutput1Register.ins.posEcef = 0
    binaryOutput1Register.ins.posU = 0
    binaryOutput1Register.gnss2.gnss2PosLla = 0
    s.writeRegister(binaryOutput1Register)
    print(f"{tstr}:     Binary output message configured\n")
    s.disconnect()

def sync_clock(portName, clock_timeout):
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 

    # Wait for GPS
    i = 0 
    gnss = Registers.GnssSolLla()
    s.readRegister(gnss)
    gnssFix = gnss.gnss1Fix.name
    num_sats = gnss.gnss1NumSats
    while gnssFix == 'NoFix':
        s.readRegister(gnss)
        gnssFix = gnss.gnss1Fix.name
        num_sats = gnss.gnss1NumSats
        time.sleep(1)
        i += 1
        if i > clock_timeout:
            break
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    print(f"{tstr}:     GNSS Fix:  {gnssFix}, Number of satellites: {num_sats}\n")

    # Sync the RP clock to the VN-200
    if gnssFix != 'NoFix':
        t0 = time.time()
        while (time.time() - t0 < 5):
            cd = s.getNextMeasurement()
            if not cd: continue
            if tUtc := cd.time.timeUtc:
                # Format the time as 'YYYY-MM-DD HH:MM:SS'
                # formatted_time = f"20{tUtc.year}-{tUtc.month}-{tUtc.day} {tUtc.hour}:{tUtc.minute}:{tUtc.second}.{tUtc.fracSec}"
                # formatted_time = f"20{tUtc.year:02}-{tUtc.month:02}-{tUtc.day:02} {tUtc.hour:02}:{tUtc.minute:02}:{tUtc.second:02}.{tUtc.fracSec:03}"
                
                vn_time = datetime(
                year=2000 + tUtc.year,  # Adjust year since it's likely offset
                month=tUtc.month,
                day=tUtc.day,
                hour=tUtc.hour,
                minute=tUtc.minute,
                second=tUtc.second,
                microsecond=tUtc.fracSec * 1000,
                tzinfo=timezone.utc)

                # Add [delay] seconds to VN-200 time if systematic offset
                vn_time_adjusted = vn_time + timedelta(seconds=0)
                
                # Format adjusted time for `date` command
                formatted_time = vn_time_adjusted.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                os.system(f"sudo date -s '{formatted_time}'") # Set the system time
                tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
                print(f"{tstr}:     Setting RP clock to: {formatted_time}")
    s.disconnect()

def VN200_status(portName, fname_log, gps_timeout):
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 

    with open(fname_log, 'a') as log:
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
        log.write(f"{tstr}:     Connected to {portName} at {s.connectedBaudRate().name}\n")
        model = Registers.Model()
        s.readRegister(model)
        model_num = model.model
        serial = Registers.Serial()
        s.readRegister(serial)
        serial_num = serial.serialNum
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
        log.write(f"{tstr}:     Connected to VN-200: Model {model_num}, Serial: {serial_num}\n")
        log.write(f"{tstr}:     Waiting for VN-200 to acquire GPS fix...\n")

        # Wait for GPS
        i = 0 
        gnss = Registers.GnssSolLla()
        s.readRegister(gnss)
        gnssFix = gnss.gnss1Fix.name
        num_sats = gnss.gnss1NumSats
        while gnssFix == 'NoFix':
            s.readRegister(gnss)
            gnssFix = gnss.gnss1Fix.name
            num_sats = gnss.gnss1NumSats
            time.sleep(1)
            i += 1
            if i > gps_timeout:
                log.write(f"{tstr}:     VN-200 could not acquire GPS fix. Exiting.\n")
                break
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
        log.write(f"{tstr}:     GNSS Fix:  {gnssFix}, Number of satellites: {num_sats}\n")

        # Log any time offset between RP and VN200 before starting session
        if gnssFix != 'NoFix':
            t0 = time.time()
            while (time.time() - t0 < 5):
                cd = s.getNextMeasurement()
                rp_time = datetime.now(timezone.utc)
                if not cd: continue
                if tUtc := cd.time.timeUtc:
                    # Format the time as 'HHMMSSfff'
                    vn_time = f"20{tUtc.year:02}{tUtc.month:02}{tUtc.day:02}{tUtc.hour:02}{tUtc.minute:02}{tUtc.second:02}{tUtc.fracSec:03}"
                    year = int(vn_time[:4])
                    month = int(vn_time[4:6])
                    day = int(vn_time[6:8])
                    hours = int(vn_time[8:10])
                    minutes = int(vn_time[10:12])
                    seconds = int(vn_time[12:14])
                    milliseconds = int(vn_time[14:])
                    vn_time = datetime(year, month, day, hours, minutes, seconds, milliseconds * 1000, tzinfo=timezone.utc)
                    diff_time = vn_time - rp_time
                    diff_seconds = diff_time.total_seconds()
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 Time: {vn_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
            log.write(f"{tstr}:     RP Time: {rp_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
            log.write(f"{tstr}:     Clock Offset (VN200 - RP): {diff_seconds:.6f} seconds\n\n")
        
        t0 = time.time()
        while (time.time() - t0 < 5):
            cd = s.getNextMeasurement()
            if not cd: continue

        try:
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            tUtc = cd.time.timeUtc
            tUtc = f"20{tUtc.year:02}-{tUtc.month:02}-{tUtc.day:02} {tUtc.hour:02}:{tUtc.minute:02}:{tUtc.second:02}"
            log.write(f"{tstr}:     VN-200 timeUtc: {tUtc}\n")
            log.write(f"{tstr}:     VN-200 timeStartup (μs): {cd.time.timeStartup.microseconds()}\n")
            log.write(f"{tstr}:     VN-200 timeGps (μs): {cd.time.timeGps.microseconds()}\n")
            log.write(f"{tstr}:     VN-200 timeGpsTow (μs): {cd.time.timeGpsTow.microseconds()}\n")
            log.write(f"{tstr}:     VN-200 timeGpsWeek: {cd.time.timeGpsWeek}\n")
            log.write(f"{tstr}:     VN-200 timeSyncIn (μs): {cd.time.timeSyncIn.microseconds()}\n")
            log.write(f"{tstr}:     VN-200 timeGpsPps (μs): {cd.time.timeGpsPps.microseconds()}\n")
            log.write(f"{tstr}:     VN-200 imuStatus: Accel: {cd.imu.imuStatus.accelStatus}, Gyro: {cd.imu.imuStatus.gyroStatus}, Mag: {cd.imu.imuStatus.magStatus}, PresTemp: {cd.imu.imuStatus.presTempStatus}\n")
            log.write(f"{tstr}:     VN-200 temperature: {cd.imu.temperature}\n")
            log.write(f"{tstr}:     VN-200 pressure: {cd.imu.pressure}\n")
            log.write(f"{tstr}:     VN-200 mag: {cd.imu.mag}\n")
            log.write(f"{tstr}:     VN-200 accel: {cd.imu.accel}\n")
            log.write(f"{tstr}:     VN-200 gnss1PosLla: Lat: {cd.gnss.gnss1PosLla.lat}, Lon: {cd.gnss.gnss1PosLla.lon}, Alt: {cd.gnss.gnss1PosLla.alt}\n")
            log.write(f"{tstr}:     VN-200 ypr: {cd.attitude.ypr}\n")
            log.write(f"{tstr}:     VN-200 quaternion: Scalar: {cd.attitude.quaternion.scalar}, Vector: {cd.attitude.quaternion.vector}\n")
            log.write(f"{tstr}:     VN-200 posLla: Lat: {cd.ins.posLla.lat}, Lon: {cd.ins.posLla.lon}, Alt: {cd.ins.posLla.alt}\n")
            # tUtc = cd.gnss.gnss1TimeUtc
            # tUtc = f"20{tUtc.year:02}-{tUtc.month:02}-{tUtc.day:02} {tUtc.hour:02}:{tUtc.minute:02}:{tUtc.second:02}"
            # log.write(f"{tstr}:     VN-200 gnss1TimeUtc: {tUtc}\n")
            # log.write(f"{tstr}:     VN-200 uncompMag: {cd.imu.uncompMag}\n")
            # log.write(f"{tstr}:     VN-200 uncompAccel: {cd.imu.uncompAccel}\n")
            # log.write(f"{tstr}:     VN-200 gnss1NumSats: {cd.gnss.gnss1NumSats}\n")
            # log.write(f"{tstr}:     VN-200 gnss1Fix: {cd.gnss.gnss1Fix}\n")
            # log.write(f"{tstr}:     VN-200 gnss1PosEcef: {cd.gnss.gnss1PosEcef}\n")
            # log.write(f"{tstr}:     VN-200 gnss1PosUncertainty: {cd.gnss.gnss1PosUncertainty}\n")
            # log.write(f"{tstr}:     VN-200 gnss1TimeUncertainty: {cd.gnss.gnss1TimeUncertainty}\n")
            # log.write(f"{tstr}:     VN-200 magNed: {cd.attitude.magNed}\n")
            # log.write(f"{tstr}:     VN-200 insStatus: GnssCompassFix: {cd.ins.insStatus.gnssCompassFix}, GnssErr: {cd.ins.insStatus.gnssErr}, GnssFix: {cd.ins.insStatus.gnssFix}\n")
            # log.write(f"{tstr}:     VN-200 posEcef: {cd.ins.posEcef}\n")
            # log.write(f"{tstr}:     VN-200 posU: {cd.ins.posU}\n")
            # log.write(f"{tstr}:     VN-200 gnss2PosLla: Lat: {cd.gnss2.gnss2PosLla.lat}, Lon: {cd.gnss2.gnss2PosLla.lon}, Alt: {cd.gnss2.gnss2PosLla.alt}\n\n")
        except:
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     Error reading VN-200 data\n\n")
    log.close()
    s.disconnect()