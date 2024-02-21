#!/bin/bash
#
#This script runs the lidar scanner and logs the output to
#a file whose name is the start date/time of collection.
#The USB ports are enabled at the start of the script,
#and disabled after the data collection is complete.
#
#EXAMPLES
#--------
#Run for default duration (10 seconds)
# $ ./run_rplidar.sh
#
#Run for 3600 seconds
# $ ./run_rplidar.sh 3600
#

# Parse command line input
#if [ $# -eq 0 ]; then
#	run_time=10
#else
#    run_time=$1
#fi

##################################

cd /home/drew/stereo/run_files/

# Output file names
#fname_out=$(date +'%Y%m%d_%H%M%S.txt')
fname_log='LOG_'$(date +'%Y%m%d_%H%M%S.txt')

# Create directory for data file export, if necessary
fdir_out='/home/drew/stereo/output/'$(date +'%Y%m%d')'/'
fdir_cam0='/home/drew/stereo/output/'$(date +'%Y%m%d')'/cam0/'
fdir_cam1='/home/drew/stereo/output/'$(date +'%Y%m%d')'/cam1/'

if [ ! -d '$fdir_out' ]; then
  sudo mkdir $fdir_out
  echo '--Created output folder: ' $fdir_out
fi
if [ ! -d '$fdir_cam0' ]; then
  sudo mkdir $fdir_cam0
  echo '--Created cam0 folder: ' $fdir_cam0
fi
if [ ! -d '$fdir_cam1' ]; then
  sudo mkdir $fdir_cam1
  echo '--Created cam1 folder: ' $fdir_cam1
fi

# Create directory for log file export, if necessary
fdir_log='/home/drew/stereo/LOG/'$(date +'%Y%m%d')'/'
if [ ! -d '$fdir_log' ]; then
  sudo mkdir $fdir_log
  echo '--Created folder to write LOG files: ' $fdir_log
fi


echo '' |& tee -a $fdir_log$fname_log
echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_log$fname_log
echo '  Output folder:            ' $fdir_out |& tee -a $fdir_log$fname_log


echo '++++++++++++++++++++++++++++++++++++++++++++++++++' |& tee -a $fdir_log$fname_log
echo '' |& tee -a $fdir_log$fname_log


# Run image collection script
python3 /home/drew/stereo/run_files/cam_test1.py $fdir_out &
