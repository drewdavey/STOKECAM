#!/bin/bash

# Last updated: 2024-04-08
##################################
# This script calls calib.py to collect a specified batch of images
# Inputs: (1) Number of frames for calibration (default = 10) (2) dt (default = 0)
# Example:
#   sudo ./run_calib.sh 50 1
##################################

# Parse command line input
if [ $# -eq 0 ]; then
  calib_frames=15
  dt=1
elif [ $# -eq 1 ]; then
  calib_frames=$1
  dt=1
else
  calib_frames=$1
  dt=$2
fi

# Output log file name
fname_log='LOG_'$(date -u +'%H%M%S_calib.txt')''

# Create directory for data and log file export, if necessary
fdir_out='../../DATA/'$(date -u +'%Y%m%d')'/'$(date -u +'%H%M%S_calib')'/'
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

echo 'Running calib.py [' $calib_frames '] frames' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_out$fname_log
echo '  Output folder:            ' $fdir_out |& tee -a $fdir_out$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log
echo 'Getting camera specs' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log

# # Run image collection script
# python3 calib.py $fdir_cam0 $fdir_cam1 $fdir_out$fname_log $calib_frames $dt & 

# Run image collection script
python3 calib.py $fdir_cam0 $fdir_cam1 $fdir_out$fname_log $calib_frames $dt >> $fdir_out$fname_log 2>&1 &

# Check if the background job was successfully started
if [ $? -eq 0 ]; then
    # Get process ID of the background script
    PID=$!
    echo 'Started Process:' $PID |& tee -a $fdir_out$fname_log

    # Wait for the background process to finish
    wait $PID 
    echo 'Completed Process:' $PID 
else
    echo 'Failed to start calib.py' |& tee -a $fdir_out$fname_log
fi
