#!/bin/bash

# Last updated: 2024-02-21
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

echo 'Running burst.py' |& tee -a $fdir_log$fname_log
echo '' |& tee -a $fdir_log$fname_log
echo '--------------- ENTERING BURST MODE --------------- '
echo '' |& tee -a $fdir_log$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_log$fname_log
echo '  Output folder:            ' $fdir_out |& tee -a $fdir_log$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_log$fname_log
echo '' |& tee -a $fdir_log$fname_log
echo 'Getting camera specs' |& tee -a $fdir_log$fname_log
echo '' |& tee -a $fdir_log$fname_log

# Run image collection script
python3 burst.py $fdir_cam0 $fdir_cam1 $fdir_log$fname_log $dt $duration & 

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