# Last updated: 2024-11-26
##################################
# Housekeeping funcs for the stereo camera system
##################################

import os
import time
import yaml
from vectornav import *
from datetime import datetime, timezone
from vectornav.Registers import VpeBasicControl
from vectornav.Commands import Command, KnownMagneticDisturbance

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

    #### CONFIGURE ADOR AND AODF 
    asyncDataOutputType = Registers.AsyncOutputType()
    asyncDataOutputType.ador = Registers.AsyncOutputType.Ador.YPR
    asyncDataOutputType.serialPort = Registers.AsyncOutputType.SerialPort.Serial1
    s.writeRegister(asyncDataOutputType)
    asyncDataOutputFreq= Registers.AsyncOutputFreq()
    asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate40Hz
    asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1
    s.writeRegister(asyncDataOutputFreq)
    
    #### CONFIGURE THE BINARY OUTPUT
    binaryOutput1Register = Registers.BinaryOutput1()
    binaryOutput1Register.rateDivisor = 20           ### 40 Hz (~800/rateDivisor) ###
    binaryOutput1Register.asyncMode.serial1 = 1
    binaryOutput1Register.asyncMode.serial2 = 0
    binaryOutput1Register.time.timeUtc = 1
    binaryOutput1Register.time.timeStartup = 1
    binaryOutput1Register.time.timeGps = 1
    binaryOutput1Register.time.timeSyncIn = 1
    binaryOutput1Register.time.timeGpsPps = 1
    binaryOutput1Register.imu.imuStatus = 1
    binaryOutput1Register.imu.temperature = 1
    binaryOutput1Register.imu.pressure = 1
    binaryOutput1Register.imu.accel = 1
    binaryOutput1Register.imu.mag = 1
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
    binaryOutput1Register.gnss.gnss1TimeUtc = 1

    s.writeRegister(binaryOutput1Register)
    s.disconnect()

def sync_clock(portName, clock_timeout):
    s = Sensor() # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)
    # Wait for GPS
    gnss = Registers.GnssSolLla()
    s.readRegister(gnss)
    gnssFix = gnss.gnss1Fix.name
    valid_fixes = {'TimeFix', 'Fix2D', 'Fix3D', 'SBAS', 'RtkFloat', 'RtkFix'}
    t0 = time.time()
    while (time.time() - t0 < clock_timeout):
        s.readRegister(gnss)
        gnssFix = gnss.gnss1Fix.name
        if gnssFix in valid_fixes:
            break
        time.sleep(0.01)
    else:
        s.disconnect()
        return False    # Sync failed
    # Sync the RP clock to the VN-200
    t0 = time.time()
    while (time.time() - t0 < clock_timeout):
        cd = s.getNextMeasurement(1)
        if not cd: continue
        if tUtc := cd.time.timeUtc:
            # Format the time as 'YYYY-MM-DD HH:MM:SS.fff'
            vn_time = f"20{tUtc.year:02}-{tUtc.month:02}-{tUtc.day:02} {tUtc.hour:02}:{tUtc.minute:02}:{tUtc.second:02}.{tUtc.fracSec:03}"
            os.system(f"sudo date -s '{vn_time}'") # Set the system time
            os.system("sudo hwclock --systohc")    # Sync the hardware clock
        # Check time lag between RP and VN-200
        cd = s.getNextMeasurement(1)
        rp_time = datetime.now(timezone.utc)
        if not cd: continue
        if tUtc := cd.time.timeUtc:
            vn_time = datetime(
                year=2000 + tUtc.year,  # VN-200 time is 2000 + YY
                month=tUtc.month,
                day=tUtc.day,
                hour=tUtc.hour,
                minute=tUtc.minute,
                second=tUtc.second,
                microsecond=tUtc.fracSec * 1000,
                tzinfo=timezone.utc)
            diff_time = vn_time - rp_time
            diff_seconds = abs(diff_time.total_seconds())
            # Check if the time difference is < 1ms
            if diff_seconds < 0.01:
                s.disconnect()
                return True  # Sync successful
        time.sleep(0.1)  
    s.disconnect()
    return False  # Sync failed

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
        # Log any time offset between RP and VN200 before starting session
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
        if gnssFix in valid_fixes:
            log.write(f"{tstr}:     GNSS Fix:  {gnssFix}, Number of satellites: {num_sats}\n")
            t0 = time.time()
            while (time.time() - t0 < gps_timeout):
                cd = s.getNextMeasurement()
                rp_time = datetime.now(timezone.utc)
                if not cd: continue
                if tUtc := cd.time.timeUtc:
                    # Format the time as 'HHMMSSfff'
                    vn_time = datetime(
                    year=2000 + tUtc.year,  # VN-200 time is 2000 + YY
                    month=tUtc.month,
                    day=tUtc.day,
                    hour=tUtc.hour,
                    minute=tUtc.minute,
                    second=tUtc.second,
                    microsecond=tUtc.fracSec * 1000,
                    tzinfo=timezone.utc)
                    diff_time = vn_time - rp_time
                    diff_seconds = diff_time.total_seconds()
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 Time: {vn_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
            log.write(f"{tstr}:     RP Time: {rp_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
            log.write(f"{tstr}:     Clock Offset (VN200 - RP): {diff_seconds:.6f} seconds\n\n")
        else:
            log.write(f"{tstr}:     VN-200 could not acquire GPS fix. Exiting.\n")

        t0 = time.time()
        while (time.time() - t0 < gps_timeout):
            cd = s.getNextMeasurement()
            if not cd: continue
            if tUtc := cd.time.timeUtc:
                tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
                log.write(f"{tstr}:     VN-200 Initial Measurements...\n")
                tUtc = f"20{tUtc.year:02}-{tUtc.month:02}-{tUtc.day:02} {tUtc.hour:02}:{tUtc.minute:02}:{tUtc.second:02}"
                log.write(f"{tstr}:     timeUtc: {tUtc}\n")
                log.write(f"{tstr}:     timeStartup (μs): {cd.time.timeStartup.microseconds()}\n")
                log.write(f"{tstr}:     timeGps (μs): {cd.time.timeGps.microseconds()}\n")
                log.write(f"{tstr}:     timeSyncIn (μs): {cd.time.timeSyncIn.microseconds()}\n")
                log.write(f"{tstr}:     timeGpsPps (μs): {cd.time.timeGpsPps.microseconds()}\n")
                log.write(f"{tstr}:     imuStatus: Accel: {cd.imu.imuStatus.accelStatus}, Gyro: {cd.imu.imuStatus.gyroStatus}, Mag: {cd.imu.imuStatus.magStatus}, PresTemp: {cd.imu.imuStatus.presTempStatus}\n")
                log.write(f"{tstr}:     temperature: {cd.imu.temperature}\n")
                log.write(f"{tstr}:     pressure: {cd.imu.pressure}\n")
                log.write(f"{tstr}:     mag: {cd.imu.mag}\n")
                log.write(f"{tstr}:     accel: {cd.imu.accel}\n")
                log.write(f"{tstr}:     ypr: {cd.attitude.ypr}\n")
                log.write(f"{tstr}:     quaternion: Scalar: {cd.attitude.quaternion.scalar}, Vector: {cd.attitude.quaternion.vector}\n")
                log.write(f"{tstr}:     gnss1Fix: {cd.gnss.gnss1Fix}\n")
                log.write(f"{tstr}:     gnss1NumSats: {cd.gnss.gnss1NumSats}\n")
                tUtc = cd.gnss.gnss1TimeUtc
                tUtc = f"20{tUtc.year:02}-{tUtc.month:02}-{tUtc.day:02} {tUtc.hour:02}:{tUtc.minute:02}:{tUtc.second:02}"
                log.write(f"{tstr}:     gnss1TimeUtc: {tUtc}\n")
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