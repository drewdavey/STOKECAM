"""
STOKECAM Post-Processing Level 1
Drew Davey
Last updated: 2025-08-21

Processes stereo image pairs for disparity & point cloud using Hirschmuller SGM.
"""

import cv2
import os, sys
import laspy
import numpy as np
import time as t
from utils import *
from pathlib import Path

# ======================= INPUTS ============================
# calib   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/calibrations/calib12_SIO_f8"
# calib   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/calibrations/calib8_SIO_f1.8"
calib   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/calibrations/calib4_SIO"

# wave = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/20250913/164253_session_bright/wave2"
# wave = "C:/Users/drew/OneDrive - UC San Diego/FSR/paper1/data/wave3"
wave = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/20250429/003014_session_auto/wave6_rotated"

# ---- Use Matlab or Python calib ----
# calib_choice = "matlab"
calib_choice = "python"

# ---- Run behavior ----
crop_valid  = True       # use common valid ROI from stereoRectify
save_params = True       # write params.json to output folder

# ---- Preprocessing (CLAHE) ----
clahe_enabled = False    # Disabled by default
clahe_clip    = 2.0
clahe_tiles   = (5, 5)

# ---- SGM Parameters (Hirschmuller) ----
max_disparity = 64       # maximum disparity for the stereo pair
P1 = 10                  # penalty for disparity difference = 1
P2 = 120                 # penalty for disparity difference > 1
csize = (5, 5)           # size of the kernel for the census transform
bsize = (3, 3)           # size of the kernel for blurring the images and median filtering

# ---- Post-masking / refinement ----
use_texture_mask = False  # gradient-based low-texture suppression (disabled)
use_sky_suppress = False  # HSV low-S/high-V sky suppression (disabled)

# ---- Outputs ----
write_ptcloud   = True

use_xyz_bounds  = True
xyz_bounds_x    = (-20, 20)   # keep xmin <= X <= xmax
xyz_bounds_y    = (-20, 20)   # keep ymin <= Y <= ymax
xyz_bounds_z    = (1, 30)     # keep zmin <= Z <= zmax

# ========================= SGM FUNCTIONS =========================

def compute_census(left, right, csize, height, width):
    """
    Calculate census bit strings for each pixel in the left and right images.
    Arguments:
        - left: left grayscale image.
        - right: right grayscale image.
        - csize: kernel size for the census transform.
        - height: number of rows of the image.
        - width: number of columns of the image.

    Return: Left and right images with pixel intensities replaced with census bit strings.
    """
    cheight = csize[0]
    cwidth = csize[1]
    y_offset = int(cheight / 2)
    x_offset = int(cwidth / 2)

    left_census_values = np.zeros(shape=(height, width), dtype=np.uint64)
    right_census_values = np.zeros(shape=(height, width), dtype=np.uint64)

    print('\tComputing left and right census...', end='')
    sys.stdout.flush()
    dawn = t.time()
    # offset is used since pixels on the border will have no census values
    for y in range(y_offset, height - y_offset):
        for x in range(x_offset, width - x_offset):
            # left
            center_pixel = left[y, x]
            reference = np.full(shape=(cheight, cwidth), fill_value=center_pixel, dtype=np.int32)
            image = left[(y - y_offset):(y + y_offset + 1), (x - x_offset):(x + x_offset + 1)]
            comparison = image - reference
            # If value is less than center value assign 1 otherwise assign 0
            left_census_pixel_array = np.where(comparison < 0, 1, 0).flatten()
            # Convert census array to an integer by using bit shift operator
            left_census_pixel = np.int32(left_census_pixel_array.dot(1 << np.arange(cheight * cwidth)[::-1]))
            left_census_values[y, x] = left_census_pixel

            # right
            center_pixel = right[y, x]
            reference = np.full(shape=(cheight, cwidth), fill_value=center_pixel, dtype=np.int32)
            image = right[(y - y_offset):(y + y_offset + 1), (x - x_offset):(x + x_offset + 1)]
            comparison = image - reference
            # If value is less than center value assign 1 otherwise assign 0
            right_census_pixel_array = np.where(comparison < 0, 1, 0).flatten()
            # Convert census array to an integer by using bit shift operator
            right_census_pixel = np.int32(right_census_pixel_array.dot(1 << np.arange(cheight * cwidth)[::-1]))
            right_census_values[y, x] = right_census_pixel

    dusk = t.time()
    print('\t(done in {:.2f}s)'.format(dusk - dawn))

    return left_census_values, right_census_values


def compute_costs(left_census_values, right_census_values, max_disparity, csize, height, width):
    """
    Create cost volume for all potential disparities.
    Cost volumes for both left and right images are calculated.
    Hamming distance is used to calculate the matching cost between
    two pixels census values.
    Arguments:
        - left_census_values: left image containing census bit strings for each pixel (in integer form).
        - right_census_values: right image containing census bit strings for each pixel (in integer form).
        - max_disparity: maximum disparity to measure.
        - csize: kernel size for the census transform.
        - height: number of rows of the image.
        - width: number of columns of the image.

    Return: Left and right cost volumes with dimensions H x W x D.
    """
    cwidth = csize[1]
    x_offset = int(cwidth / 2)

    print('\tComputing cost volumes...', end='')
    sys.stdout.flush()
    dawn = t.time()
    left_cost_volume = np.zeros(shape=(height, width, max_disparity), dtype=np.uint32)
    right_cost_volume = np.zeros(shape=(height, width, max_disparity), dtype=np.uint32)
    lcensus = np.zeros(shape=(height, width), dtype=np.int32)
    rcensus = np.zeros(shape=(height, width), dtype=np.int32)

    for d in range(0, max_disparity):
        # The right image is shifted d pixels accross
        rcensus[:, (x_offset + d):(width - x_offset)] = right_census_values[:, x_offset:(width - d - x_offset)]
        # 1 is assigned when the bits differ and 0 when they are the same
        left_xor = np.int32(np.bitwise_xor(np.int32(left_census_values), rcensus))
        # All the 1's are summed up to give us the number of different pixels (the cost)
        left_distance = np.zeros(shape=(height, width), dtype=np.uint32)
        while not np.all(left_xor == 0):
            tmp = left_xor - 1
            mask = left_xor != 0
            left_xor[mask] = np.bitwise_and(left_xor[mask], tmp[mask])
            left_distance[mask] = left_distance[mask] + 1
        # All the costs for that disparity are added to the cost volume
        left_cost_volume[:, :, d] = left_distance

        # The left image is shifted d pixels accross
        lcensus[:, x_offset:(width - d - x_offset)] = left_census_values[:, (x_offset + d):(width - x_offset)]
        # 1 is assigned when the bits differ and 0 when they are the same
        right_xor = np.int32(np.bitwise_xor(np.int32(right_census_values), lcensus))
        # All the 1's are summed up to give us the number of different pixels (the cost)
        right_distance = np.zeros(shape=(height, width), dtype=np.uint32)
        while not np.all(right_xor == 0):
            tmp = right_xor - 1
            mask = right_xor != 0
            right_xor[mask] = np.bitwise_and(right_xor[mask], tmp[mask])
            right_distance[mask] = right_distance[mask] + 1
        # All the costs for that disparity are added to the cost volume
        right_cost_volume[:, :, d] = right_distance

    dusk = t.time()
    print('\t(done in {:.2f}s)'.format(dusk - dawn))

    return left_cost_volume, right_cost_volume


def get_penalties(max_disparity, P2, P1):
    """
    Creates a matrix of all the potential penalties for matching
    a current disparity (represented by the column index), with
    a previous disparity (represented by the row index).
    Arguments:
        - max_disparity: Maximum disparity of the array.
        - P2: Penalty for disparity difference > 1
        - P1: Penalty for disparity difference = 1

    Return: Matrix containing all the penalties when disparity d1 from a column
            is matched with a previous disparity d2 from the row.
    """
    p2 = np.full(shape=(max_disparity, max_disparity), fill_value=P2, dtype=np.uint32)
    p1 = np.full(shape=(max_disparity, max_disparity), fill_value=P1 - P2, dtype=np.uint32)
    p1 = np.tril(p1, k=1) # keep values lower than k'th diagonal
    p1 = np.triu(p1, k=-1) # keep values higher than k'th diagonal
    no_penalty = np.identity(max_disparity, dtype=np.uint32) * -P1 # create diagonal matrix with values -p1
    penalties = p1 + p2 + no_penalty
    return penalties


def get_path_cost(slice, offset, penalties, other_dim, disparity_dim):
    """
    Calculates the minimum costs for all potential disparities of
    the pixels along a single path direction.
    Arguments:
        - slice: Array containing costs for all disparities, D,
            along a direction, M, with dimension M x D
        - offset: Number of pixels on the border to ignore.
        - penalties: Matrix containing the penalties to assign to the
            previous disparities costs. For previous disparities that differ
            from current disparities.
        - other_dim: Number of pixels in the current paths direction.
        - disparity_dim: Number of disparities to calculate minimum costs.

    Returns: The pixels minimum costs for all disparities, D,
        along path direction, M, with shape M x D.
    """
    minimum_cost_path = np.zeros(shape=(other_dim, disparity_dim), dtype=np.uint32)
    minimum_cost_path[offset - 1, :] = slice[offset - 1, :]

    for pixel_index in range(offset, other_dim):
        # Get all the minimum disparities costs from the previous pixel in the path
        previous_cost = minimum_cost_path[pixel_index - 1, :]
        # Get all the disparities costs (from the cost volume) for the current pixel
        current_cost = slice[pixel_index, :]
        costs = np.repeat(previous_cost, repeats=disparity_dim, axis=0).reshape(disparity_dim, disparity_dim)
        # Add penalties to the previous pixels disparities that differ from current pixels disparities
        costs = costs + penalties
        # Find minimum costs for the current pixels disparities using the previous disparities costs + penalties
        costs = np.amin(costs, axis=0)
        # Current pixels disparities costs + minimum previous pixel disparities costs (with penalty) -
        # (constant term) minimum previous cost from all disparities
        pixel_direction_costs = current_cost + costs - np.amin(previous_cost)
        minimum_cost_path[pixel_index, :] = pixel_direction_costs

    return minimum_cost_path


def aggregate_costs(cost_volume, P2, P1, height, width, disparities):
    """
    Calculates the pixels costs for all disparities along all paths (4 in this case).

    Arguments:
        - cost_volume: Array containing the matching cost for each pixel at each disparity.
        - P2: Penalty for disparity difference > 1
        - P1: Penalty for disparity difference = 1
        - height: Number of rows of the image.
        - width: Number of columns of the image.
        - disparities: Number of disparities to calculate minimum matching costs.

    Returns: Array containing the pixels matching costs for all disparities along
        all directions, with dimension H x W x D X 4.
    """
    sys.stdout.flush()
    dawn = t.time()

    penalties = get_penalties(disparities, P2, P1)

    print("\tProcessing North and South aggregation...")
    south_aggregation = np.zeros(shape=(height, width, disparities), dtype=np.uint32)
    north_aggregation = np.copy(south_aggregation)

    for x in range(0, width):
        # Takes all the rows and disparities for a single column
        south = cost_volume[:, x, :]
        # Invert the rows to get the opposite direction
        north = np.flip(south, axis=0)
        south_aggregation[:, x, :] = get_path_cost(south, 1, penalties, height, disparities)
        north_aggregation[:, x, :] = np.flip(get_path_cost(north, 1, penalties, height, disparities), axis=0)


    print("\tProcessing East and West aggregation...", end='')
    east_aggregation = np.copy(south_aggregation)
    west_aggregation = np.copy(south_aggregation)
    for y in range(0, height):
        # Takes all the column and disparities for a single row
        east = cost_volume[y, :, :]
        # Invert the columns to get the opposite direction
        west = np.flip(east, axis=0)
        east_aggregation[y, :, :] = get_path_cost(east, 1, penalties, width, disparities)
        west_aggregation[y, :, :] = np.flip(get_path_cost(west, 1, penalties, width, disparities), axis=0)

    # Combine the costs from all paths into a single aggregation volume
    aggregation_volume = np.concatenate((south_aggregation[..., None], north_aggregation[..., None], east_aggregation[..., None], west_aggregation[..., None]), axis=3)

    dusk = t.time()
    print('\t(done in {:.2f}s)'.format(dusk - dawn))

    return aggregation_volume


def select_disparity(aggregation_volume):
    """
    Converts the aggregation volume into a disparity map using
    the winner takes all strategy.
    Cost volume is first calculated by taking the sum of the costs over all paths.
    Then the disparities are determined by finding the
    disparity index with the lowest cost for the pixel.

    Arguments:
        - aggregation_volume: Array containing the matching costs for
            all pixels at all disparities and paths, with dimension H x W x D x N

    Returns: Disparity map with dimensions H x W.
    """
    # sum up costs for all directions
    volume = np.sum(aggregation_volume, axis=3)
    # returns the disparity index with the minimum cost associated with each h x w pixel
    disparity_map = np.argmin(volume, axis=2)
    return disparity_map


def normalize_disparity(disp, max_disparity):
    """
    Normalizes the disparity map, then
    quantizes it so that it can be displayed.
    Arguments:
        - disp: disparity map with dimensions H x W.
        - max_disparity: maximum disparity of the array.

    Return: normalized then quantized array, ready for visualization.
    """
    return 255.0 * disp / max_disparity


# ------------------------------- Main ----------------------------------
def main():
    # ---------- Inputs ----------
    calib_path = calib or pick_file_gui()
    wave_path  = wave or pick_dir_gui()

    if not calib_path or not wave_path:
        sys.exit("Missing calib or wave (empty and GUI canceled).")
    if not os.path.exists(calib_path):
        sys.exit(f"Calibration file not found: {calib_path}")
    if not (os.path.isdir(os.path.join(wave_path, "cam0")) and os.path.isdir(os.path.join(wave_path, "cam1"))):
        sys.exit("wave must contain cam0/ and cam1/ subfolders.")

    # ---------- Load calibration ----------
    K0, D0, K1, D1, R, T, image_size, err_m = load_calibration(calib_path, choice=calib_choice)

    # ---------- Collect pairs ----------
    cam0_list = sorted_images(os.path.join(wave_path, "cam0"))
    cam1_list = sorted_images(os.path.join(wave_path, "cam1"))
    n = min(len(cam0_list), len(cam1_list))
    if n == 0:
        sys.exit("No image pairs found.")

    # Infer image_size from first image if needed
    if image_size is None:
        tmp = cv2.imread(cam0_list[0], cv2.IMREAD_GRAYSCALE)
        if tmp is None:
            sys.exit("Failed to read first image to infer size.")
        image_size = (tmp.shape[1], tmp.shape[0])  # (w, h)

    # ---------- Rectification maps ----------
    (map10, map11, map20, map21), (_, _, _, _, Q), (roi1, roi2), crop = stereo_rectify_maps(
        K0, D0, K1, D1, R, T, image_size, crop_valid=crop_valid)
    crop_tuple = tuple(map(int, crop)) if (crop is not None) else None

    # ---------- Output dirs ----------
    l1_dir  = os.path.join(wave_path, "L1")
    out_dir = os.path.join(wave_path, "figs", "disparityMaps")
    os.makedirs(l1_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # ---------- Precompute CLAHE if used ----------
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_tiles) if clahe_enabled else None

    # ---------- Process frames ----------
    for i in range(n):
        fL = cam0_list[i]
        fR = cam1_list[i]

        imL = cv2.imread(fL, cv2.IMREAD_COLOR)
        imR = cv2.imread(fR, cv2.IMREAD_COLOR)
        if imL is None or imR is None:
            print(f"[WARN] Failed to read pair index {i}")
            continue

        # Rectify (color)
        rL = cv2.remap(imL, map10, map11, cv2.INTER_LINEAR)
        rR = cv2.remap(imR, map20, map21, cv2.INTER_LINEAR)

        # Optional crop to valid common ROI
        if crop_tuple is not None:
            x, y, w, h = crop_tuple
            rL = rL[y:y+h, x:x+w]
            rR = rR[y:y+h, x:x+w]

        # Grayscale for matching (+ optional CLAHE)
        gL = cv2.cvtColor(rL, cv2.COLOR_BGR2GRAY)
        gR = cv2.cvtColor(rR, cv2.COLOR_BGR2GRAY)
        if clahe is not None:
            gL = clahe.apply(gL); gR = clahe.apply(gR)

        # Apply Gaussian blur for smoothing
        gL = cv2.GaussianBlur(gL, bsize, 0, 0)
        gR = cv2.GaussianBlur(gR, bsize, 0, 0)

        height, width = gL.shape
        print(f"Processing frame {i+1}/{n} with size: {width}x{height}")

        # ---------- SGM Processing ----------
        # Compute census transform
        left_census, right_census = compute_census(gL, gR, csize, height, width)

        # Compute cost volumes
        left_cost_volume, right_cost_volume = compute_costs(left_census, right_census, max_disparity, csize, height, width)

        # Cost aggregation (SGM)
        print('\tStarting left aggregation computation...')
        left_aggregation_volume = aggregate_costs(left_cost_volume, P2, P1, height, width, max_disparity)

        # Select disparity map
        left_disparity_map = select_disparity(left_aggregation_volume)

        # Normalize and convert to uint8
        disp_px = left_disparity_map.astype(np.float32)
        left_disparity_map_uint8 = np.uint8(normalize_disparity(left_disparity_map, max_disparity))

        # Apply median filtering for smoothing
        left_disparity_map_smoothed = cv2.medianBlur(left_disparity_map_uint8, bsize[0])

        # ---------- Optional texture / sky suppression ----------
        if use_texture_mask:
            gx = cv2.Sobel(gL, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(gL, cv2.CV_32F, 0, 1, ksize=3)
            mag = cv2.magnitude(gx, gy)
            thr = max(10.0, float(np.percentile(mag, 75)))  # robust vs scenes
            texture_mask = (mag > thr)
        else:
            texture_mask = np.ones_like(gL, dtype=bool)
        if use_sky_suppress:
            hsv = cv2.cvtColor(rL, cv2.COLOR_BGR2HSV)       # use color, not gray->HSV
            low_tex_sky = (hsv[...,1] < 38) & (hsv[...,2] > 153)  # S<~0.15, V>~0.6 (0–255 scale)
        else:
            low_tex_sky = np.zeros_like(gL, dtype=bool)
        keep_mask = texture_mask & (~low_tex_sky)

        # Apply mask to disparity
        disp_color = np.where(keep_mask, left_disparity_map_smoothed, 0.0)

        # ---------- Save disparity (color) ----------
        stem = strip_leading_cam_prefix(Path(fL).stem)
        out_dispc = os.path.join(out_dir, f"{stem}_color.png")
        cv2.imwrite(out_dispc, colorize_disparity(disp_color))

        # ---------- Optional point cloud ----------
        if write_ptcloud:
            # Convert disparity back to float for 3D reprojection
            disparity_for_3d = left_disparity_map_smoothed.astype(np.float32)

            # Reproject to 3D (XYZ in rectified left camera frame)
            points3D = cv2.reprojectImageTo3D(disparity_for_3d, Q)
            colors = cv2.cvtColor(rL, cv2.COLOR_BGR2RGB)

            # Keep finite and plausible disparities
            valid = (disparity_for_3d > 0) & np.isfinite(points3D).all(axis=2)

            # Extract valid points and colors
            valid_points = points3D[valid]
            valid_colors = colors[valid]

            # Crop to XYZ bounds if requested
            if use_xyz_bounds:
                xmin, xmax = xyz_bounds_x
                ymin, ymax = xyz_bounds_y
                zmin, zmax = xyz_bounds_z

                crop_mask = (
                    (valid_points[:, 0] >= xmin) & (valid_points[:, 0] <= xmax) &
                    (valid_points[:, 1] >= ymin) & (valid_points[:, 1] <= ymax) &
                    (valid_points[:, 2] >= zmin) & (valid_points[:, 2] <= zmax)
                )

                cropped_points = valid_points[crop_mask]
                cropped_colors = valid_colors[crop_mask]
            else:
                cropped_points = valid_points
                cropped_colors = valid_colors

            print(f"\tGenerated {len(cropped_points)} points after cropping")

            # Create LAS file
            las_path = os.path.join(l1_dir, f"{stem}.las")
            header = laspy.LasHeader(point_format=3, version="1.4")  # Format 3 includes RGB

            las = laspy.LasData(header)
            las.x = cropped_points[:, 0] # Northing
            las.y = cropped_points[:, 1] # Easting
            las.z = cropped_points[:, 2] # Elevation
            las.red = cropped_colors[:, 0] * 257    # Scale 0-255 to 0-65535 (LAS uses 16-bit RGB)
            las.green = cropped_colors[:, 1] * 257
            las.blue = cropped_colors[:, 2] * 257

            las.write(las_path)

        print(f"Processed {i+1}/{n}")

    print(f"Done. Outputs in: {out_dir}\n")

if __name__ == "__main__":
    main()
