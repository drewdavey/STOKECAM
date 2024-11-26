# Last updated: 2024-10-03
##################################
# Housekeeping funcs for the stereo camera system
##################################

import os
import time
import yaml
from vectornav import *
from datetime import datetime, timezone

# List of VN-200 groups and parameters
vn_parameters = [
    ('time', 'timeUtc'),
    ('time', 'timeStartup'),
    ('time', 'timeGps'),
    ('time', 'timeGpsTow'),
    ('time', 'timeGpsWeek'),
    ('time', 'timeSyncIn'),
    ('time', 'timeGpsPps'),
    ('imu', 'imuStatus'),
    ('imu', 'uncompMag'),
    ('imu', 'uncompAccel'),
    ('imu', 'temperature'),
    ('imu', 'pressure'),
    ('imu', 'mag'),
    ('imu', 'accel'),
    ('gnss', 'gnss1TimeUtc'),
    ('gnss', 'gnss1NumSats'),
    ('gnss', 'gnss1Fix'),
    ('gnss', 'gnss1PosLla'),
    ('gnss', 'gnss1PosEcef'),
    ('gnss', 'gnss1PosUncertainty'),
    ('gnss', 'gnss1TimeUncertainty'),
    ('attitude', 'ypr'),
    ('attitude', 'quaternion'),
    ('attitude', 'magNed'),
    ('ins', 'insStatus'),
    ('ins', 'posLla'),
    ('ins', 'posEcef'),
    ('ins', 'posU'),
    ('gnss2', 'gnss2PosLla')
]

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
""".format(datetime.now(timezone.utc).strftime('%Y-%m-%d-%H-%M-%S'))
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
    asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate20Hz
    asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1
    s.writeRegister(asyncDataOutputFreq)
    print(f"{tstr}:     ADOF Configured\n")
    
    #### CONFIGURE THE BINARY OUTPUT
    binaryOutput1Register = Registers.BinaryOutput1()
    binaryOutput1Register.rateDivisor = 100
    binaryOutput1Register.asyncMode.serial1 = 1
    binaryOutput1Register.asyncMode.serial2 = 0
    binaryOutput1Register.common.timeStartup = 1
    binaryOutput1Register.common.accel = 1
    binaryOutput1Register.common.angularRate = 1
    # Execute the configuration lines dynamically
    for category, parameter in vn_parameters:
        category_obj = getattr(binaryOutput1Register, category)
        setattr(category_obj, parameter, 1)

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
                # formatted_time = f"20{tUtc.year}-{tUtc.month}-{tUtc.day}-{tUtc.hour}-{tUtc.minute}-{tUtc.second}-{tUtc.fracSec}"
                formatted_time = f"20{tUtc.year}-{tUtc.month}-{tUtc.day} {tUtc.hour}:{tUtc.minute}:{tUtc.second}"
        # Set the system time (requires root privileges)
        os.system(f"sudo date -s '{formatted_time}'")
        print(f"{tstr}:     Setting system time to: {formatted_time}")
        tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
        print(f"{tstr}:     RP clock synced to VN-200.\n")
    s.disconnect()

def parse_time(time_str):
    hours = int(time_str[:2])
    minutes = int(time_str[2:4])
    seconds = int(time_str[4:6])
    milliseconds = int(time_str[6:])
    return datetime(2000, 1, 1, hours, minutes, seconds, milliseconds * 1000)

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
                if not cd: continue
                if tUtc := cd.time.timeUtc:
                    # Format the time as 'HHMMSSfff'
                    vn_time = f"{tUtc.hour}{tUtc.minute}{tUtc.second}{tUtc.fracSec}"
                    rp_time = datetime.now(timezone.utc).strftime('%H%M%S%f')[:-3]
            vn_time = parse_time(vn_time)
            rp_time = parse_time(rp_time)
            diff_time = rp_time - vn_time
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 Time: {vn_time}\n")
            log.write(f"{tstr}:     RP Time: {rp_time}\n")
            log.write(f"{tstr}:     Clock Offset (RP - VN200): {diff_time}\n")
        if cd:
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 timeStartup: ({cd.time.timeStartup})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 timeGps: ({cd.time.timeGps})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 timeGpsTow: ({cd.time.timeGpsTow})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 timeGpsWeek: ({cd.time.timeGpsWeek})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 timeSyncIn: ({cd.time.timeSyncIn})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 timeGpsPps: ({cd.time.timeGpsPps})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 timeUtc: ({cd.time.timeUtc})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 imuStatus: ({cd.imu.imuStatus})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 uncompMag: ({cd.imu.uncompMag})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 uncompAccel: ({cd.imu.uncompAccel})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 temperature: ({cd.imu.temperature})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 pressure: ({cd.imu.pressure})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 mag: ({cd.imu.mag})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 accel: ({cd.imu.accel})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 gnss1TimeUtc: ({cd.gnss.gnss1TimeUtc})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 gnss1NumSats: ({cd.gnss.gnss1NumSats})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 gnss1Fix: ({cd.gnss.gnss1Fix})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 gnss1PosLla: ({cd.gnss.gnss1PosLla})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 gnss1PosEcef: ({cd.gnss.gnss1PosEcef})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 gnss1PosUncertainty: ({cd.gnss.gnss1PosUncertainty})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 gnss1TimeUncertainty: ({cd.gnss.gnss1TimeUncertainty})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 ypr: ({cd.attitude.ypr})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 quaternion: ({cd.attitude.quaternion})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 magNed: ({cd.attitude.magNed})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 insStatus: ({cd.ins.insStatus})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 posLla: ({cd.ins.posLla})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 posEcef: ({cd.ins.posEcef})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 posU: ({cd.ins.posU})\n")
            cd = s.getNextMeasurement(1)
            tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
            log.write(f"{tstr}:     VN-200 gnss2PosLla: ({cd.gnss2.gnss2PosLla})\n")
    log.close()
    s.disconnect()