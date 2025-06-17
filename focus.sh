#!/bin/bash

# # Last updated: 2024-06-17
# ##################################
# # This script creates two preview windows to focus the cameras
# # Inputs: (1) Width in pixels (default = 1440) (2) Height in pixels (default = 1080)
# # Example:
# #  ./focus.sh 1440 1080
# ##################################

# Parse command line input
if [ $# -eq 0 ]; then
  width=1440
  height=1080
elif [ $# -eq 1 ]; then
  width=$1
  height=1080
else
  width=$1
  height=$2
fi

# Function to get exposure time from a camera
get_exposure() {
  cam=$1
  libcamera-still --camera $cam --metadata -n --width 320 --height 240 -t 1 2>&1 | \
    grep "Exposure time" | head -n 1 | awk '{print $NF}'
}

# Background loop to print exposure times every 0.5 seconds
print_exposures() {
  while true; do
    exp0=$(get_exposure 0)
    exp1=$(get_exposure 1)
    echo -ne "cam0: ${exp0} µs, cam1: ${exp1} µs\r"
    sleep 0.5
  done
}

# Start the exposure monitor in the background
print_exposures &
exposure_pid=$!

# Start camera previews
libcamera-hello --width $width --height $height -p 0,0,$width,$height --camera 0 -t 0 &
pid0=$!
libcamera-hello --width $width --height $height -p 0,0,$width,$height --camera 1 -t 0 &
pid1=$!

# Wait for previews to be closed
wait $pid0
kill $pid1 2>/dev/null
kill $exposure_pid 2>/dev/null
echo -e "\nPreview ended. Exposure monitoring stopped."





# #!/bin/bash

# # Last updated: 2024-04-10
# ##################################
# # This script creates two preview windows to focus the cameras
# # Inputs: (1) Width in pixels (default = 1440) (2) Height in pixels (default = 1080)
# # Example:
# #  ./focus.sh 1440 1080
# ##################################
 
# # Parse command line input
# if [ $# -eq 0 ]; then
#   width=1440
#   height=1080
# elif [ $# -eq 1 ]; then
#   width=$1
#   height=1080
# else
#   width=$1
#   height=$2
# fi

# # Two windows live stream
# libcamera-hello --width $width --height $height -p 0,0,$width,$height --camera 0 -t 0 & libcamera-hello --width $width --height $height -p 0,0,$width,$height --camera 1 -t 0

