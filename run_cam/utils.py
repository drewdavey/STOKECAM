# Last updated: 2025-02-04
##################################
# Housekeeping funcs for the stereo camera system
##################################

import os
import time
import yaml
from vectornav import *
from vectornav.Commands import *
from vectornav.Registers import *
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
    return fdir_out, fdir_cam0, fdir_cam1

def config_vecnav(portName):
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 

    ### CONFIGURE ADOR AND AODF 
    asyncDataOutputType = Registers.AsyncOutputType()
    # asyncDataOutputType.ador = Registers.AsyncOutputType.Ador.GPS
    asyncDataOutputType.serialPort = Registers.AsyncOutputType.SerialPort.Serial1
    s.writeRegister(asyncDataOutputType)
    asyncDataOutputFreq= Registers.AsyncOutputFreq()
    asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate50Hz
    asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1
    s.writeRegister(asyncDataOutputFreq)
    
    #### CONFIGURE THE BINARY OUTPUT
    binaryOutput1Register = Registers.BinaryOutput1()
    binaryOutput1Register.rateDivisor = 16           ### 50 Hz (~800/rateDivisor) ###
    binaryOutput1Register.asyncMode.serial1 = 1
    binaryOutput1Register.time.timeUtc = 1
    binaryOutput1Register.time.timeStartup = 1
    binaryOutput1Register.time.timeGps = 1
    binaryOutput1Register.imu.imuStatus = 1
    binaryOutput1Register.imu.temperature = 1
    binaryOutput1Register.imu.pressure = 1
    binaryOutput1Register.imu.accel = 1
    binaryOutput1Register.imu.mag = 1
    binaryOutput1Register.imu.uncompGyro = 1
    binaryOutput1Register.attitude.ypr = 1
    binaryOutput1Register.attitude.quaternion = 1
    binaryOutput1Register.ins.posLla = 1
    binaryOutput1Register.ins.posEcef = 1
    binaryOutput1Register.ins.posU = 1
    binaryOutput1Register.ins.insStatus = 1
    binaryOutput1Register.gnss.gnss1PosLla = 1
    binaryOutput1Register.gnss.gnss1PosEcef = 1
    binaryOutput1Register.gnss.gnss1PosUncertainty = 1
    binaryOutput1Register.gnss.gnss1Fix = 1
    binaryOutput1Register.gnss.gnss1NumSats = 1
    s.writeRegister(binaryOutput1Register)
    s.disconnect()

def sync_clock(portName, gps_timeout):
    s = Sensor() # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)
    gnss = Registers.GnssSolLla()
    s.readRegister(gnss)
    gnssFix = gnss.gnss1Fix.name
    valid_fixes = {'TimeFix', 'Fix2D', 'Fix3D', 'SBAS', 'RtkFloat', 'RtkFix'}
    # Wait for GNSS fix
    t0 = time.time()
    while (time.time() - t0 < gps_timeout):
        s.readRegister(gnss)
        gnssFix = gnss.gnss1Fix.name
        if gnssFix in valid_fixes:
            break
        time.sleep(0.1)
    else:
        print("Timeout waiting for GNSS fix.")
        s.disconnect()
        return False    # GPS timed out
    # Sync system time with VN-200
    t0 = time.time()
    while (time.time() - t0 < gps_timeout):
        cd = s.getNextMeasurement(1)
        rp_time = datetime.now(timezone.utc)
        if tUtc := cd.time.timeUtc:
            # Check time lag between RP and VN-200
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
            if abs(diff_seconds) >= 1:
                adjusted_time = datetime.now(timezone.utc) + timedelta(seconds=diff_seconds)
                formatted_time = adjusted_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                os.system(f"sudo date -s '{formatted_time}'")  # Set system time
                os.system("sudo hwclock --systohc")  # Sync hardware clock
            elif abs(diff_seconds) < 1:
                s.disconnect()
                return True  # Sync successful
        time.sleep(0.01) 
    s.disconnect()
    return False  # Sync failed

def vecnav_status(portName, fname_log, gps_timeout):
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 
    # Write connection status
    log = open(fname_log, 'a')
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
    # Write KnownMagneticDisturbance and VpeBasicControl
    kmd = KnownMagneticDisturbance(KnownMagneticDisturbance.State.Present)  
    vpeBasicControl = VpeBasicControl()
    vpeBasicControl.headingMode = VpeBasicControl.HeadingMode.Absolute
    vpeBasicControl.filteringMode =  VpeBasicControl.FilteringMode.AdaptivelyFiltered
    vpeBasicControl.tuningMode =  VpeBasicControl.TuningMode.Adaptive
    vpeBasicControlCmd = Command(vpeBasicControl.toWriteCommand())
    if not kmd.isAwaitingResponse():
        error = kmd.getError()
        if (error):
            log.write(f"{tstr}:     KMD received error {error.what()}\n")
        else:
            log.write(f"{tstr}:     KMD response: {str(kmd.getResponse())}\n")
    else:
        log.write(f"{tstr}:     KMD received no response\n")
    if not vpeBasicControlCmd.isAwaitingResponse():
        error = vpeBasicControlCmd.getError()
        if (error):
            log.write(f"{tstr}:     WRG received error {error.what()}\n")
        else:
            log.write(f"{tstr}:     WRG response: {vpeBasicControlCmd.getResponse()}\n")
    else:
        log.write(f"{tstr}:     WRG received no response\n")
    
    # Wait for GPS
    log.write(f"{tstr}:     Waiting for VN-200 to acquire GPS fix...\n")
    gnss = Registers.GnssSolLla()
    s.readRegister(gnss)
    gnssFix = gnss.gnss1Fix.name
    num_sats = gnss.gnss1NumSats
    valid_fixes = {'TimeFix', 'Fix2D', 'Fix3D', 'SBAS', 'RtkFloat', 'RtkFix'}
    t0 = time.time()
    while gnssFix not in valid_fixes and (time.time() - t0 < gps_timeout):
        s.readRegister(gnss)
        gnssFix = gnss.gnss1Fix.name
        num_sats = gnss.gnss1NumSats
        time.sleep(0.1)
    # Log clock offset between RP and VN200 before starting session
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    if gnssFix in valid_fixes:
        log.write(f"{tstr}:     GNSS Fix:  {gnssFix}, Number of satellites: {num_sats}\n")
        t0 = time.time()
        while (time.time() - t0 < gps_timeout):
            cd = s.getNextMeasurement(1)
            rp_time = datetime.now(timezone.utc)
            rp_mono_time = time.monotonic_ns()
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
                break
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
        log.write(f"{tstr}:     VN-200 Time: {vn_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
        log.write(f"{tstr}:     RP Time: {rp_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
        log.write(f"{tstr}:     System Clock Offset (VN200 - RP): {diff_seconds:.6f} seconds\n")
        vn_mono_time = cd.time.timeStartup.microseconds() * 1e3
        delta_mono_time = (vn_mono_time - rp_mono_time) * 1e-9
        log.write(f"{tstr}:     Startup Time Offset (VN200 - RP): {delta_mono_time} seconds\n\n")
    else:
        log.write(f"{tstr}:     VN-200 could not acquire GPS fix. Exiting.\n")

    t0 = time.time()
    while (time.time() - t0 < gps_timeout):
        cd = s.getNextMeasurement()
        if not cd: continue
        if tUtc := cd.time.timeUtc:
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 Initial Measurements...\n")
            tUtc = f"20{tUtc.year:02}-{tUtc.month:02}-{tUtc.day:02} {tUtc.hour:02}:{tUtc.minute:02}:{tUtc.second:02}.{tUtc.fracSec:03}"
            log.write(f"{tstr}:     timeUtc: {tUtc}\n")
            log.write(f"{tstr}:     timeStartup (μs): {cd.time.timeStartup.microseconds()}\n")
            log.write(f"{tstr}:     timeGps (μs): {cd.time.timeGps.microseconds()}\n")
            log.write(f"{tstr}:     imuStatus: Accel: {cd.imu.imuStatus.accelStatus}, Gyro: {cd.imu.imuStatus.gyroStatus}, Mag: {cd.imu.imuStatus.magStatus}, PresTemp: {cd.imu.imuStatus.presTempStatus}\n")
            log.write(f"{tstr}:     temperature: {cd.imu.temperature}\n")
            log.write(f"{tstr}:     pressure: {cd.imu.pressure}\n")
            log.write(f"{tstr}:     mag: {cd.imu.mag}\n")
            log.write(f"{tstr}:     accel: {cd.imu.accel}\n")
            log.write(f"{tstr}:     ypr: {cd.attitude.ypr}\n")
            log.write(f"{tstr}:     quaternion: Scalar: {cd.attitude.quaternion.scalar}, Vector: {cd.attitude.quaternion.vector}\n")
            log.write(f"{tstr}:     gnss1Fix: {cd.gnss.gnss1Fix}\n")
            log.write(f"{tstr}:     gnss1NumSats: {cd.gnss.gnss1NumSats}\n")
            log.write(f"{tstr}:     gnss1PosLla: Lat: {cd.gnss.gnss1PosLla.lat}, Lon: {cd.gnss.gnss1PosLla.lon}, Alt: {cd.gnss.gnss1PosLla.alt}\n")
            log.write(f"{tstr}:     gnss1PosEcef: {cd.gnss.gnss1PosEcef}\n")
            log.write(f"{tstr}:     gnss1PosUncertainty: {cd.gnss.gnss1PosUncertainty}\n")
            log.write(f"{tstr}:     insStatus: GnssCompassFix: {cd.ins.insStatus.gnssCompassFix}, GnssErr: {cd.ins.insStatus.gnssErr}, GnssFix: {cd.ins.insStatus.gnssFix}\n")
            log.write(f"{tstr}:     INS posLla: Lat: {cd.ins.posLla.lat}, Lon: {cd.ins.posLla.lon}, Alt: {cd.ins.posLla.alt}\n")
            log.write(f"{tstr}:     INS posEcef: {cd.ins.posEcef}\n")
            log.write(f"{tstr}:     INS posU: {cd.ins.posU}\n\n")
            break
        else:
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     Error reading VN-200 data\n\n")
    log.close()
    s.disconnect()