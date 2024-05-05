#!/bin/bash

# Last updated: 2024-02-23
##################################
# This script calls burst.py to collect burst images when shutter is pressed
# Spaced by [dt] for [duration]
# Inputs: (1) dt (default = 0) (2) duration (default = 10)
# Example:
#   sudo ./run_burst.sh 1 60
##################################

# Parse command line input
if [ $# -eq 0 ]; then
	dt=0
  duration=10
elif [ $# -eq 1 ]; then
  dt=$1
  duration=10
else
  dt=$1
  duration=$2
fi

# Output log file name
fname_log='LOG_'$(date -u +'%H%M%S_burst.txt')''

# Create directory for data and log file export, if necessary
fdir_out='../../DATA/'$(date -u +'%Y%m%d')'/'$(date -u +'%H%M%S_burst')'/'
fdir_cam0=$fdir_out'cam0/'
fdir_cam1=$fdir_out'cam1/'

if [ ! -d '$fdir_out' ]; then
  mkdir -p $fdir_out
  echo '--Created output folder: ' $fdir_out
  mkdir -p $fdir_cam0
  echo '--Created cam0 folder: ' $fdir_cam0
  mkdir -p $fdir_cam1
  echo '--Created cam1 folder: ' $fdir_cam1
fi

echo 'Running burst.py' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log
echo '--------------- ENTERING BURST MODE --------------- '
echo '' |& tee -a $fdir_out$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_out$fname_log
echo '  Output folder:            ' $fdir_out |& tee -a $fdir_out$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log
echo 'Getting camera specs' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log

# Run image collection script
python3 burst.py $fdir_cam0 $fdir_cam1 $fdir_out$fname_log $dt $duration >> $fdir_out$fname_log 2>&1 &

# Check if the background job was successfully started
if [ $? -eq 0 ]; then
    # Get process ID of the background script
    PID=$!
    echo 'Started Process:' $PID |& tee -a $fdir_out$fname_log

    # Wait for the background process to finish
    # Wait 
    sleep $duration |& tee -a $fdir_out$fname_log

    # Kill the background process
    kill -INT $PID |& tee -a $fdir_out$fname_log 
    echo 'Completed Process:' $PID 
else
    echo 'Failed to start calib.py' |& tee -a $fdir_out$fname_log
fi