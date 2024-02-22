#!/bin/bash

# Last updated: 2024-02-21
##################################
# This script calls calib.py to collect a specified batch of images
# Inputs: (1) Number of frames to be collected (default = 10)
# Example:
#   sudo ./run_calib.sh 10
##################################

# Parse command line input
if [ $# -eq 0 ]; then
	calib_frames=10
else
  calib_frames=$1
fi

# Output log file name
fname_log='LOG_'$(date -u +'%H%M%S_calib.txt')''

# Create directory for data and log file export, if necessary
fdir_out='../../DATA/'$(date -u +'%Y%m%d')'/'
fdir_cam0=$fdir_out'cam0/'
fdir_cam1=$fdir_out'cam1/'
fdir_log='../../LOG/'$(date -u +'%Y%m%d')'/'

if [ ! -d '$fdir_out' ]; then
  sudo mkdir -p $fdir_out
  echo '--Created output folder: ' $fdir_out
  sudo mkdir -p $fdir_cam0
  echo '--Created cam0 folder: ' $fdir_cam0
  sudo mkdir -p $fdir_cam1
  echo '--Created cam1 folder: ' $fdir_cam1
fi

if [ ! -d '$fdir_log' ]; then
  sudo mkdir -p $fdir_log
  echo '--Created folder to write LOG files: ' $fdir_log
fi 

echo 'Running calib.py [' $num_frames '] frames' |& tee -a $fdir_log$fname_log
echo '' |& tee -a $fdir_log$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_log$fname_log
echo '  Output folder:            ' $fdir_out |& tee -a $fdir_log$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_log$fname_log
echo '' |& tee -a $fdir_log$fname_log
echo 'Getting camera specs' |& tee -a $fdir_log$fname_log
echo '' |& tee -a $fdir_log$fname_log

# Run image collection script
python3 calib.py $fdir_cam0 $fdir_cam1 $fdir_log$fname_log $calib_frames & 

#Get stop time
# tstop=$(date -u +"%Y%m%d%H%M%S")
# echo 'Stop Time: ' $tstop |& tee -a $fdir_log$fname_log

# Get process ID of the background script we just launched
#PID=$!
#echo 'Process:' $PID |& tee -a $fdir_log$fname_log

# Wait 
#sleep $run_time |& tee -a $fdir_log$fname_log

# Kill the background process
#kill -INT $PID |& tee -a $fdir_log$fname_log
#sleep 2
#echo 'Done collecting images!' |& tee -a $fdir_log$fname_log