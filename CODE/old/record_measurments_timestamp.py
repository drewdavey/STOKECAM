#!/usr/bin/env python
'''Records measurements to a given file. Usage example:

$ ./record_measurments_timestamp.py out.txt'''
import sys
from rplidar import RPLidar
import datetime
import signal


# DEFINE PARAMETERS
PORT_NAME = '/dev/ttyUSB0'




def run(path):
    '''Main function'''    
    lidar = RPLidar(PORT_NAME)
    outfile = open(path, 'w')
    
    def quit_gracefully(*argv):
        print '--Quitting gracefully'
        
        t_stop = datetime.datetime.utcnow()
        t_stop_str = t_stop.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        outfile.write(t_stop_str)
        print('STOPPED: ' + t_stop_str)
        
        lidar.stop()
        lidar.disconnect()
        outfile.close()
        
        exit(0);
        
    signal.signal(signal.SIGINT, quit_gracefully)
    
    t_start = datetime.datetime.utcnow()
    t_start_str = t_start.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    outfile.write(t_start_str + '\n')
    print('STARTED: ' + t_start_str)
    print('Recording measurements... Press Ctrl+C to stop.')
    #print('Recording measurements...')
    
    for measurment in lidar.iter_measurments():
        line = '\t'.join(str(v) for v in measurment)
        outfile.write(line + '\n')
   
    

if __name__ == '__main__':
    run(sys.argv[1])
