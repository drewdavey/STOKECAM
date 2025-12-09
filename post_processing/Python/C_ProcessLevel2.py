"""
STOKECAM Post-Processing Level 2
Drew Davey
Last updated: 2025-09-09

Loads Level 1 point clouds and IMU data for georectifcation.
"""

import os
import scipy.io
import pygeodesy
import numpy as np
import laspy
from utils import *

# ======================= INPUTS ============================
# ---- Wave/session folder ----
# wave = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/20250913/164253_session_bright/wave2"
# wave = "C:/Users/drew/OneDrive - UC San Diego/FSR/paper1/data/wave3"
wave = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/testing/static/staticStairsv2/wave2"


# ---- Geoid file (EGM2008 1' grid) ----
geoid_file = "C:/ProgramData/GeographicLib/geoids/egm2008-1.pgm"

# ---- Origin presets [lat, lon] ----
# origin = None               # Uses local mean if None
origin = [32.866277163888888, -117.2542791472222] # SIO
# origin = [33.219778, -117.406497] # DMJs
# origin = [32.836786, -117.281222] # Marine St.
# origin = [33.588303, -117.879581] # Wedge

# ---- Run behavior ----
save_params = True       # write params.json to output folder
write_ptcloud = True     # save transformed point clouds
denoise = False          # apply denoising to point clouds
downsample = False       # downsample point clouds
brighten = False         # brighten colors
brightenFactor = 1.2     # multiplier if brighten is True

# --------------------------------------------------------------------------
def main(origin=None):
    # ---- Directories ----
    l1_dir = os.path.join(wave, "L1")
    l2_dir = os.path.join(wave, "L2")
    os.makedirs(l2_dir, exist_ok=True)

    # ---- Load IMU ----
    imu = scipy.io.loadmat(os.path.join(wave, "imu.mat"), squeeze_me=True, struct_as_record=False)['imu']

    def _as_vector(name, data):
        """Return data as a 1D numpy array; raise if empty."""
        arr = np.asarray(data).reshape(-1)
        if arr.size == 0:
            raise ValueError(f"IMU field '{name}' is empty")
        return arr

    lat = _as_vector('lat', imu.lat)
    lon = _as_vector('lon', imu.lon)
    alt = _as_vector('alt', imu.alt)
    quatX = _as_vector('quatX', imu.quatX)
    quatY = _as_vector('quatY', imu.quatY)
    quatZ = _as_vector('quatZ', imu.quatZ)
    quatW = _as_vector('quatW', imu.quatW)
    t0 = _as_vector('t0', imu.t0)

    numFrames = len(quatX)
    for name, arr in [('lat', lat), ('lon', lon), ('alt', alt),
                      ('quatY', quatY), ('quatZ', quatZ), ('quatW', quatW), ('t0', t0)]:
        if len(arr) != numFrames:
            raise ValueError(f"IMU field '{name}' has length {len(arr)} but expected {numFrames}")

    # ---- Origin ----
    if origin is None:
        origin = [np.mean(lat), np.mean(lon)]  # Default to local origin
        print(f"[INFO] No origin specified, using local mean: {origin}")
    else:
        print(f"[INFO] Using user-specified origin: {origin}")

    # ---- Geoid height at origin using pygeodesy ----
    ginterpolator = pygeodesy.GeoidKarney(geoid_file)
    geoidHeight = ginterpolator.height(origin[0], origin[1])
    print(f"[INFO] Geoid height at origin (EGM2008 1'): {geoidHeight:.3f} m")
    lla0 = [origin[0], origin[1], geoidHeight]

    # ---- LLA to NED ----
    lla = np.stack([lat, lon, alt], axis=1)
    NED = lla2ned(lla, lla0)
    N, E, D = NED[:,0], NED[:,1], NED[:,2]

    # ---- Rotation matrices ----
    rotationMatrices = np.zeros((numFrames, 3, 3))
    for i in range(numFrames):
        q = [quatW[i], quatX[i], quatY[i], quatZ[i]]
        rotationMatrices[i] = quat2rotm(q)

    # ---- Process each L1 point cloud ----
    las_files = sorted([f for f in os.listdir(l1_dir) if f.endswith('.las')])
    for i, las_file in enumerate(las_files):
        las_path = os.path.join(l1_dir, las_file)
        
        # Read LAS file
        las = laspy.read(las_path)
        xyz_cam = np.column_stack([las.x, las.y, las.z])
        colors = np.column_stack([las.red, las.green, las.blue]) / 257  # Scale 16-bit to 8-bit

        # Camera to IMU coords
        xyz_imu = (np.array([[0,0,1],[1,0,0],[0,1,0]]) @ xyz_cam.T).T

        # Rotate to NED
        R = rotationMatrices[i]
        xyz_NED = (R @ xyz_imu.T).T

        # Translate to world
        cam_origin = np.array([N[i], E[i], D[i]])
        xyz_world = xyz_NED + cam_origin

        # Convert NED to ENU: East, North, Up
        xyz_ENU = np.column_stack([xyz_world[:, 1], xyz_world[:, 0], -xyz_world[:, 2]])

        # ---- Save as LAS ----
        output_path = os.path.join(l2_dir, las_file)
        
        # Create new LAS file with transformed coordinates
        header = laspy.LasHeader(point_format=3, version="1.2")
        las_out = laspy.LasData(header)
        
        las_out.x = xyz_ENU[:, 0]  # Easting
        las_out.y = xyz_ENU[:, 1]  # Northing
        las_out.z = xyz_ENU[:, 2]  # Up
        las_out.red = (colors[:, 0] * 257).astype(np.uint16)    # Scale back to 16-bit
        las_out.green = (colors[:, 1] * 257).astype(np.uint16)
        las_out.blue = (colors[:, 2] * 257).astype(np.uint16)
        
        las_out.write(output_path)
        print(f"Processed and saved: {output_path}")
        
    # ---- Generate L3 concatenated ptCloud from all L2 ptClouds ----
    genL3ptCloud(wave)

if __name__ == "__main__":
    main(origin)
    # main()  # No argument uses local mean origin