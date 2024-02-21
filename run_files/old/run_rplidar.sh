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
if [ $# -eq 0 ]; then
	run_time=10
else
    run_time=$1
fi

##################################

cd /home/pi/projects/lidar/run_files/

# Enable USB power
echo "--Enabling USB power" |& tee -a $fdir_log$fname_log
bash /home/pi/projects/scripts/shell/enable_usb.sh |& tee -a $fdir_log$fname_log
echo "--Initializing..." |& tee -a $fdir_log$fname_log
sleep 3

# mount flashdrive in usb port
sudo mount -a /mnt |& tee -a $fdir_log$fname_log
echo "--Mounted flashdrive to /mnt" |& tee -a $fdir_log$fname_log
sleep 3

# Output file names
fname_out=$(date +"%Y%m%d_%H%M%S.txt")
fname_log="LOG_"$(date +"%Y%m%d_%H%M%S.txt")

# Create directory for data file export, if necessary
fdir_out="/mnt/DATA/"
if [ ! -d "$fdir_out" ]; then
  sudo mkdir $fdir_out
  echo "--Created folder to write DATA files: " $fdir_out
fi

# Create directory for log file export, if necessary
fdir_log="/mnt/LOG/"
if [ ! -d "$fdir_log" ]; then
  sudo mkdir $fdir_log
  echo "--Created folder to write LOG files: " $fdir_log
fi



echo "" |& tee -a $fdir_log$fname_log
echo "++++++++++++++++++++++++++++++++++++++++++++++++++" |& tee -a $fdir_log$fname_log
echo "  Output folder:            " $fdir_out |& tee -a $fdir_log$fname_log
echo "  Output filename:          " $fname_out |& tee -a $fdir_log$fname_log
echo "  Data collection time (s): " $run_time |& tee -a $fdir_log$fname_log
echo "++++++++++++++++++++++++++++++++++++++++++++++++++" |& tee -a $fdir_log$fname_log
echo "" |& tee -a $fdir_log$fname_log

# Run record_measurments_timestamp script
# (the python script should run in the background)
python ../rplidar/examples/record_measurments_timestamp.py $fdir_out$fname_out &

# Get process ID of the background script we just launched
PID=$!
echo "Process:" $PID |& tee -a $fdir_log$fname_log

# Wait for some period of time...while we collect scans in the background
sleep $run_time |& tee -a $fdir_log$fname_log

# Kill the background process, which should cleanly end the python script and close the file
kill -INT $PID |& tee -a $fdir_log$fname_log
sleep 2
echo "--Scan complete!" |& tee -a $fdir_log$fname_log

# Show last 10 lines of the output file as a quick check
echo "LAST 10 LINES OF THE DATA FILE" |& tee -a $fdir_log$fname_log
tail $fdir_out$fname_out |& tee -a $fdir_log$fname_log
printf "\n" |& tee -a $fdir_log$fname_log
sleep 5

# unmount flashdrive in usb port
sudo umount /mnt |& tee -a $fdir_log$fname_log
sleep 5
echo "--Unmounted flashdrive from /mnt" |& tee -a $fdir_log$fname_log

# Disable USB power
echo "--Disabling USB power" |& tee -a $fdir_log$fname_log
bash /home/pi/projects/scripts/shell/disable_usb.sh |& tee -a $fdir_log$fname_log


