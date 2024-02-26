#!/bin/bash

# Last updated: 2024-02-23
##################################
# This script calls numFrames.py to collect a specified batch of images
# Inputs: (1) Number of frames to be collected (default = 5) (2) dt (default = 0)
# Example:
#   sudo ./run_numFrames.sh 10 1
##################################

# Parse command line input
if [ $# -eq 0 ]; then
  num_frames=5
  dt=0
elif [ $# -eq 1 ]; then
  num_frames=$1
  dt=0
else
  num_frames=$1
  dt=$2
fi

# Output log file name
fname_log='LOG_'$(date -u +'%H%M%S_numFrames.txt')''

# Create directory for data and log file export, if necessary
fdir_out='../../DATA/'$(date -u +'%Y%m%d')'/'$(date -u +'%H%M%S_numFrames')'/'
fdir_cam0=$fdir_out'cam0/'
fdir_cam1=$fdir_out'cam1/'
# fdir_log='../../LOG/'$(date -u +'%Y%m%d')'/'

if [ ! -d '$fdir_out' ]; then
  mkdir -p $fdir_out
  echo '--Created output folder: ' $fdir_out
  mkdir -p $fdir_cam0
  echo '--Created cam0 folder: ' $fdir_cam0
  mkdir -p $fdir_cam1
  echo '--Created cam1 folder: ' $fdir_cam1
fi

# if [ ! -d '$fdir_log' ]; then
#   mkdir -p $fdir_log
#   echo '--Created folder to write LOG files: ' $fdir_log
# fi 

echo 'Running numFrames.py [' $num_frames '] frames' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_out$fname_log
echo '  Output folder:            ' $fdir_out |& tee -a $fdir_out$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log
echo 'Getting camera specs' |& tee -a $fdir_out$fname_log
echo '' |& tee -a $fdir_out$fname_log

# Run image collection script
python3 numFrames.py $fdir_cam0 $fdir_cam1 $fdir_out$fname_log $num_frames $dt & 

#Get stop time
# tstop=$(date -u +"%Y%m%d%H%M%S")
# echo 'Stop Time: ' $tstop |& tee -a $fdir_log$fname_log

# Get process ID of the background script
# PID=$!
# echo 'Process:' $PID |& tee -a $fdir_log$fname_log

# Wait 
# sleep $run_time |& tee -a $fdir_log$fname_log

# Kill the background process
# kill -INT $PID |& tee -a $fdir_log$fname_log