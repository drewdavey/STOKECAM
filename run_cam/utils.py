# Last updated: 2025-02-04
##################################
# Housekeeping funcs for the stereo camera system
##################################

import os
import time
import yaml
from vectornav import *
from ruamel.yaml import YAML
from picamera2 import Picamera2
from vectornav.Commands import *
from vectornav.Registers import *
from datetime import datetime, timezone, timedelta

def setup_logging():
    """Set up logging directory and file"""
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

def write_inputs_yaml(fname_log):
    """Write exposure times to inputs.yaml file"""
    with open(fname_log, 'a') as log:
        # Create a camera instance with auto exposure turned on
        cam = Picamera2()
        config = cam.create_still_configuration(buffer_count=10)
        config['main']['size'] = (1440, 1080)
        config['main']['format'] = 'RGB888'
        config['controls']['AeEnable'] = True
        config['controls']['AwbEnable'] = True
        cam.configure(config)
        cam.start()
        # Allow time for auto-exposure to converge
        time.sleep(5)
        # Get auto exposure time from metadata 
        while not (auto_exposure_us := cam.capture_metadata(wait=True)['ExposureTime']):
            time.sleep(0.1)                                                          
        auto_exposure_ms = auto_exposure_us / 1000.0 # convert to ms
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
        log.write(f"{tstr}:     [INFO] ========== write_inputs_yaml() ==========\n")
        log.write(f"{tstr}:     [INFO] Measured auto exposure from metadata: {auto_exposure_us} µs ({auto_exposure_ms:.3f} ms)\n")
        cam.stop()
        cam.close()
        # Define brighter/darker exposures; e.g. half and double
        bright_us = max(auto_exposure_us / 2, 1)
        dark_us   = max(auto_exposure_us * 2, 1)
        bright_ms = bright_us / 1000.0 # convert to ms
        dark_ms   = dark_us / 1000.0 # convert to ms
        log.write(f"{tstr}:     [INFO] Setting bright mode = {bright_ms:.3f} ms, dark mode = {dark_ms:.3f} ms\n")
        yaml_path = "../inputs.yaml"
        if not os.path.exists(yaml_path):
            log.write(f"{tstr}:     [WARN] inputs.yaml not found, creating minimal file...\n")
            with open(yaml_path, "w") as fh:
                fh.write("# Minimal inputs.yaml created by write_inputs_yaml\n")
                fh.write("fps: 25\ncalib_dt: 2\ncalib_frames: 50\ngps_timeout: 60\n")
                fh.write("shooting_mode0: auto\nexposure_ms0: 1\n")
                fh.write("shooting_mode1: bright\nexposure_ms1: 2\n")
                fh.write("shooting_mode2: dark\nexposure_ms2: 4\n")
        ry = YAML()
        ry.preserve_quotes = True
        with open(yaml_path, "r") as f:
            yaml_data = ry.load(f)
        if not yaml_data:
            yaml_data = {}
        yaml_data["shooting_mode0"] = "auto"
        yaml_data["exposure_ms0"]   = int(round(auto_exposure_ms))
        yaml_data["shooting_mode1"] = "bright"
        yaml_data["exposure_ms1"]   = int(round(bright_ms))
        yaml_data["shooting_mode2"] = "dark"
        yaml_data["exposure_ms2"]   = int(round(dark_ms))
        with open(yaml_path, "w") as f:
            ry.dump(yaml_data, f)
        log.write(f"{tstr}:     [INFO] Successfully updated inputs.yaml.\n\n")

def read_inputs_yaml(fname_log):
    """Read inputs.yaml file and return parameters"""
    inputs_path = '../inputs.yaml'
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    with open(fname_log, 'a') as log:
        try:
            with open(inputs_path, 'r') as file:
                inputs = yaml.safe_load(file)
            return inputs
        except FileNotFoundError:
            log.write(f"{tstr}:     Error: The file {inputs_path} was not found.")
            return None
        except yaml.YAMLError as exc:
            log.write(f"{tstr}:     Error parsing YAML file: {exc}")
            return None

def parse_inputs(fname_log):
    """Parse inputs.yaml file and return parameters"""
    inputs = read_inputs_yaml(fname_log)
    if not inputs:
        # add error handling here
        return None
    # Basic parameters
    frame_rate = inputs['fps']              # e.g. 25 Hz
    calib_dt = inputs['calib_dt'] * 1e9     # code logic uses ns
    calib_frames = inputs['calib_frames']
    # Shooting modes & exposure times
    shooting_modes = [inputs['shooting_mode0'], inputs['shooting_mode1'], inputs['shooting_mode2']]
    exposure_times = [inputs['exposure_ms0'], inputs['exposure_ms1'], inputs['exposure_ms2']]
    return frame_rate, calib_dt, calib_frames, shooting_modes, exposure_times

def calc_dt(frame_rate, exposure_ms):
    """Calculate the time difference between camera and VN-200"""
    frame_period = 1.0 / frame_rate       # e.g. 0.04 s ~ 25 Hz
    latency = 14.26e-6                    # 14.26 microseconds
    exposure_sec = exposure_ms / 1e3      # ms -> sec
    exposure = exposure_sec - latency     # hardware trigger offsets
    dt = (frame_period - exposure) * 1e9  # remainder in nanoseconds
    return exposure, dt

def create_dirs(fdir, mode):
    """Create directories for storing images"""
    session = datetime.now(timezone.utc).strftime('%H%M%S_' + mode)
    fdir_out = os.path.join(fdir, session + '/')
    fdir_cam0 = os.path.join(fdir_out, 'cam0/')
    fdir_cam1 = os.path.join(fdir_out, 'cam1/')
    os.makedirs(fdir_cam0, exist_ok=True)
    os.makedirs(fdir_cam1, exist_ok=True)
    return fdir_out, fdir_cam0, fdir_cam1

def get_config(mode, exposure_ms):
    """Get camera configuration based on mode and exposure time"""
    cam = Picamera2()
    cfg = cam.create_still_configuration(buffer_count=50)
    cfg['main']['size'] = (1440, 1080)
    cfg['main']['format'] = 'RGB888'
    cfg['controls']['ExposureTime'] = exposure_ms * 1000  # exposure in microseconds
    cfg['controls']['AeEnable'] = False                   # disable auto exposure
    cfg['controls']['AwbEnable'] = False                  # disable auto white balance
    # Select parameters
    if mode == 'auto':
        cfg['controls']['FrameDurationLimits'] = (0, 100)
        # add other settings by mode here
    elif mode == 'fast':
        cfg['controls']['FrameDurationLimits'] = (0, 100)
    elif mode == 'max':
        cfg['controls']['FrameDurationLimits'] = (33333, 33333)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    cam.close()
    return cfg

def config_vecnav(portName):
    """Configure the VN-200 sensor"""
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
    """Sync system clock with VN-200"""
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
    """Check the status of the VN-200 sensor"""
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 
    # Write connection status
    log = open(fname_log, 'a')
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    log.write(f"{tstr}:     Connected to {portName} at {s.connectedBaudRate().name}\n")
    model_num = None
    model = Registers.Model()
    serial_num = None
    serial = Registers.Serial()
    try:
        s.readRegister(model)
        model_num = model.model
        s.readRegister(serial)
        serial_num = serial.serialNum
        log.write(f"{tstr}:     VN-200 Model: {model_num}\n")
        log.write(f"{tstr}:     VN-200 Serial: {serial_num}\n")
    except Exception as e:
        log.write(f"{tstr}:     ERROR reading VN-200 Model/Serial register: {str(e)}\n")
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
    gnssFix = None
    num_sats = None
    gnss = Registers.GnssSolLla()
    try:
        s.readRegister(gnss)
        gnssFix = gnss.gnss1Fix.name
        num_sats = gnss.gnss1NumSats
    except Exception as e:
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
        log.write(f"{tstr}:     ERROR reading VN-200 GNSS register: {str(e)}\n")
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