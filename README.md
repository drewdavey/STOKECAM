# STereo imaging system for Overturning wave KinEmatiCs and dynAMics (STOKECAM)

**Last Updated:** 2025-09-16
**Author:** Drew Davey
**Email:** adavey@ucsd.edu

## Overview

STOKECAM is a stereo imaging system designed for capturing and analyzing overturning wave kinematics and dynamics. The system uses dual Raspberry Pi cameras with external triggering capabilities and integrates with VectorNav IMU sensors for precise motion tracking during wave measurement campaigns.

## Hardware Components

- Dual Raspberry Pi cameras (IMX296 sensors)
- VectorNav IMU system
- External trigger system
- Raspberry Pi processing unit

## Repository Structure

### Core Scripts
- **`run_cam/master.py`** - Main control script for camera operation and data acquisition
- **`run_cam/utils.py`** - Utility functions for camera configuration and data handling
- **`focus.sh`** - Camera focusing utility with live preview windows
- **`update.sh`** - Automated system update script

### Configuration Files
- **`STOKECAM.yaml`** - Camera pipeline configuration (libcamera settings)
- **`inputs.yaml`** - System parameters (framerate, exposure, GPS timeout, etc.)

### Post-Processing Pipeline
- **`post_processing/Python/`** - Python-based processing scripts
  - `A_Calibrate.py` - Camera calibration
  - `B_ProcessLevel1.py` - Initial data processing
  - `C_ProcessLevel2.py` - Advanced processing and analysis
  - `D_ViewPtClouds.py` - Point cloud visualization
- **`post_processing/MATLAB/`** - MATLAB-based processing alternatives
  - Equivalent functionality in MATLAB environment

### VectorNav Integration
- **`vectornav/`** - VectorNav SDK and utilities for IMU data collection

## Key Features

- **Synchronized Stereo Capture** - Dual camera system with external triggering
- **Multiple Exposure Modes** - Auto, bright, and dark shooting modes with configurable exposure times
- **IMU Integration** - VectorNav sensor integration for motion compensation
- **Real-time Processing** - Live camera preview and exposure monitoring
- **Automated Calibration** - Stereo camera calibration pipeline
- **3D Point Cloud Generation** - Complete stereo reconstruction workflow

## Usage

### System Setup
1. Configure camera parameters in `inputs.yaml`
2. Adjust pipeline settings in `STOKECAM.yaml` if needed
3. Ensure proper camera mounting and calibration

### Camera Operation
```bash
# Focus cameras (creates preview windows)
./focus.sh [width] [height]

# Run main data acquisition
cd run_cam/
python master.py
```

### Post-Processing
```bash
cd post_processing/Python/
python A_Calibrate.py      # Camera calibration
python B_ProcessLevel1.py  # Initial processing
python C_ProcessLevel2.py  # Advanced analysis
python D_ViewPtClouds.py   # Visualization
```

## Configuration Parameters

Key settings in `inputs.yaml`:
- **fps**: Capture framerate (max 40 fps)
- **exposure_us**: Exposure times for different lighting conditions
- **shooting_mode**: Auto, bright, or dark modes
- **gps_timeout**: GPS lock timeout during startup

## Dependencies

- Python 3.x
- OpenCV (cv2)
- picamera2
- VectorNav Python SDK
- numpy, matplotlib (for processing)
- MATLAB (optional, for MATLAB processing pipeline)
- libcamera (Raspberry Pi camera interface)

## System Requirements

- Raspberry Pi with dual camera support
- VectorNav IMU device
- Sufficient storage for high-framerate stereo video data
- Network connectivity for remote operation and data transfer

## Contact

**Drew Davey**
University of California, San Diego
Email: adavey@ucsd.edu
