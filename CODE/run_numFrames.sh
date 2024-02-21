#!/bin/bash

# Last updated:b

##################################

# Parse command line input
if [ $# -eq 0 ]; then
	num_frames=5
else
  num_frames=$1
fi

# Output log name
fname_log='LOG_'$(date +'%Y%m%d_%H%M%S.txt')''

# Create directory for data and log file export, if necessary
fdir_out='../../DATA/'$(date +'%Y%m%d')'/'
fdir_cam0='../../DATA/'$(date +'%Y%m%d')'/cam0/'
fdir_cam1='../../DATA/'$(date +'%Y%m%d')'/cam1/'
fdir_log='../../LOG/'$(date +'%Y%m%d')'/'

if [ ! -d '$fdir_out' ]; then
  sudo mkdir -p $fdir_out
  echo '--Created output folder: ' $fdir_out
#fi
#if [ ! -d '$fdir_cam0' ]; then
  sudo mkdir -p $fdir_cam0
  echo '--Created cam0 folder: ' $fdir_cam0
#fi
#if [ ! -d '$fdir_cam1' ]; then
  sudo mkdir -p $fdir_cam1
  echo '--Created cam1 folder: ' $fdir_cam1
fi

if [ ! -d '$fdir_log' ]; then
  sudo mkdir -p $fdir_log
  echo '--Created folder to write LOG files: ' $fdir_log
fi 

echo '' |& tee -a $fdir_log$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_log$fname_log
echo '  Output folder:            ' $fdir_out |& tee -a $fdir_log$fname_log

echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_log$fname_log
echo '' |& tee -a $fdir_log$fname_log


# Run image collection script
python3 numFrames.py $fdir_cam0 $fdir_cam1 $fdir_log $num_frames & 

# Get process ID of the background script we just launched
#PID=$!
#echo 'Process:' $PID |& tee -a $fdir_log$fname_log

# Wait 
#sleep $run_time |& tee -a $fdir_log$fname_log

# Kill the background process
#kill -INT $PID |& tee -a $fdir_log$fname_log
#sleep 2
#echo 'Done collecting images!' |& tee -a $fdir_log$fname_log