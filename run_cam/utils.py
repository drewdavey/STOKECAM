# Last updated: 2024-10-03
##################################
# Housekeeping funcs for the stereo camera system
##################################

import os
import time
import yaml
from vectornav import *
from datetime import datetime, timezone

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

def sync_clock(clock_timeout):
    portName = '/dev/ttyUSB0'
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)           # at the baud rate of 115200 (115,200 bytes/s) 
    # binaryOutput1Register = Registers.BinaryOutput1()
    # binaryOutput1Register.asyncMode.serial1 = 1
    # binaryOutput1Register.time.timeUtc = 1
    # s.writeRegister(binaryOutput1Register)
    
    # Wait for GPS
    i = 0 
    gnss = Registers.GnssSolLla()
    s.readRegister(gnss)
    gnssFix = gnss.gnss1Fix.name
    while gnssFix == 'NoFix':
        s.readRegister(gnss)
        gnssFix = gnss.gnss1Fix.name
        num_sats = gnss.gnss1NumSats
        timeUtc = gnss.gnss1TimeUtc
        time.sleep(1)
        i += 1
        if i > clock_timeout:
            break
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    print(f"{tstr}:     GNSS Fix:  {gnssFix}, Number of satellites: {num_sats}\n")
    print(f"Time: {timeUtc}")
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    print(f"{tstr}:     Syncing RP clock to VN-200...\n")
    time.sleep(5)
    tstr = datetime.now(timezone.utc).strftime('%H%M%S%f')
    print(f"{tstr}:     RP clock synced to VN-200.\n")

    # # Sync the RP clock to the VN-200
    # if gnssFix != 'NoFix':
    #     t0 = time.time()
    #     while (time.time() - t0 < 5):
    #         cd = s.getNextMeasurement()
    #         if not cd: continue
    #         if timeUtc := cd.time.timeUtc:
    #             print(f"Time: {timeUtc}")
    #             print(f"Time: {timeUtc.name}")
    #             print(f"Time: {timeUtc}")

    s.disconnect()

def config_VN200(fname_log, gps_timeout):
    portName = '/dev/ttyUSB0'
    s = Sensor()                      # Create sensor object and connect to the VN-200 
    s.autoConnect(portName)             # at the baud rate of 115200 (115,200 bytes/s) 
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

        #### CONFIGURE ADOR AND AODF 
        asyncDataOutputType = Registers.AsyncOutputType()
        asyncDataOutputType.ador = Registers.AsyncOutputType.Ador.YPR
        asyncDataOutputType.serialPort = Registers.AsyncOutputType.SerialPort.Serial1
        s.writeRegister(asyncDataOutputType)
        log.write(f"{tstr}:     ADOR Configured\n")
        asyncDataOutputFreq= Registers.AsyncOutputFreq()
        asyncDataOutputFreq.adof = Registers.AsyncOutputFreq.Adof.Rate20Hz
        asyncDataOutputFreq.serialPort = Registers.AsyncOutputFreq.SerialPort.Serial1
        s.writeRegister(asyncDataOutputFreq)
        log.write(f"{tstr}:     ADOF Configured\n")

        #### CONFIGURE THE BINARY OUTPUT
        binaryOutput1Register = Registers.BinaryOutput1()
        binaryOutput1Register.rateDivisor = 100
        binaryOutput1Register.asyncMode.serial1 = 1
        binaryOutput1Register.asyncMode.serial2 = 0
        binaryOutput1Register.common.timeStartup = 1
        binaryOutput1Register.common.accel = 1
        binaryOutput1Register.common.angularRate = 1
        binaryOutput1Register.time.timeUtc = 1
        s.writeRegister(binaryOutput1Register)
        log.write(f"{tstr}:     Binary output message configured\n")

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

        # if ez.current_data.has_any_position:
        #     pos = ez.current_data.position_estimated_lla
        #     log.write(f"{tstr}:     GPS Position (LLA): ({pos.x}, {pos.y}, {pos.z})\n")
        #     posun = ez.current_data.any_position_uncertainty
        #     log.write(f"{tstr}:     Position uncertainty: ({posun.x}, {posun.y}, {posun.z})\n")
        #     posunes = ez.current_data.position_uncertainty_estimated
        #     log.write(f"{tstr}:     Position uncertainty estimated: {posunes}\n")
        # if ez.current_data.has_time_gps:
        #     vn_time = ez.current_data.time_utc
        #     log.write(f"{tstr}:     Time from VN-200: {vn_time}\n")
        # if ez.current_data.has_num_sats:
        #     num_sats = ez.current_data.num_sats
        #     log.write(f"{tstr}:     Number of satellites: {num_sats}\n")
        # gps_sol = s.read_gps_solution_lla()
        # log.write(f"{tstr}:     GPS Solution (LLA): ({gps_sol.lla.x}, {gps_sol.lla.y}, {gps_sol.lla.z})\n")
        # imu_out = s.read_imu_measurements() 
        # log.write(f"{tstr}:     Current Temperature: {imu_out.temp} and Pressure: {imu_out.pressure}\n\n")
    log.close()
    s.disconnect()