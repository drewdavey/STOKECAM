#!/bin/bash

# Last updated: 2024-04-10
##################################
# This script creates two preview windows to focus the cameras
# Inputs: (1) Width in pixels (default = 1440) (2) Height in pixels (default = 1080)
# Example:
#  ./focus.sh 1440 1080
##################################
 
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

# Two windows live stream
libcamera-hello --width $width --height $height -p 0,0,$width,$height --camera 0 -t 0 & libcamera-hello --width $width --height $height -p 0,0,$width,$height --camera 1 -t 0
