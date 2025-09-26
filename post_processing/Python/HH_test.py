"""
STOKECAM Post-Processing Level 1 - Enhanced with Multiple SGM Options
Drew Davey
Last updated: 2025-09-17

Processes stereo image pairs for disparity & point cloud with multiple SGM algorithm choices.
"""

import cv2
import os, sys
import numpy as np
from utils import *
from pathlib import Path
import cv2.ximgproc as xip
import time

# ======================= INPUTS ============================
calib   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/calibrations/calib12_SIO_f8"
wave = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/20250913/164253_session_bright/wave2"

# ---- Use Matlab or Python calib ----
calib_choice = "python"

# ---- Run behavior ----
crop_valid  = True       # use common valid ROI from stereoRectify
save_params = True       # write params.json to output folder

# ---- Preprocessing (CLAHE) ----
clahe_enabled = True
clahe_clip    = 2.0
clahe_tiles   = (5, 5)

# =================== SGM ALGORITHM SELECTION ===================
# Choose your SGM algorithm:
# "opencv_sgbm"     - OpenCV StereoSGBM (block-based, fastest)
# "opencv_sgm"      - OpenCV pixel-level SGM (if available in ximgproc)
# "hirschmuller"    - Custom Hirschmuller implementation (pixel-level, slower)
# "matlab_style"    - OpenCV with MATLAB-like parameters

sgm_algorithm = "hirschmuller"  # Change this to test different algorithms

# ---- Common Parameters ----
min_disparity = 0
num_disparities = 64     # multiple of 16
uniqueness_threshold = 15
speckle_window = 120
speckle_range = 2
disp12_maxdiff = 1
prefilter_cap = 31

# ---- OpenCV StereoSGBM Parameters ----
opencv_block_size = 7    # odd, >=3 (only for StereoSGBM)
opencv_mode = "HH"       # "SGBM", "SGBM_3WAY", "HH", "HH4"

# ---- SGM Penalty Parameters ----
# Use different P1/P2 based on algorithm choice
if sgm_algorithm == "matlab_style":
    # MATLAB-style parameters with small block size
    sgm_P1 = 15
    sgm_P2 = 200
    opencv_block_size = 3    # Smallest block size
elif sgm_algorithm == "opencv_sgbm":
    # Standard OpenCV scaling
    sgm_P1 = 8 * 3 * (opencv_block_size ** 2)
    sgm_P2 = 32 * 3 * (opencv_block_size ** 2)
else:
    # Hirschmuller original values for pixel-level algorithms
    sgm_P1 = 15
    sgm_P2 = 200

# ---- Hirschmuller Implementation Parameters ----
hirschmuller_directions = 8    # 5, 8, or 16
hirschmuller_cost_function = "BT"  # "BT" or "SAD"

# ---- Post-masking / refinement ----
use_texture_mask = True    # gradient-based low-texture suppression
use_sky_suppress = True    # HSV low-S/high-V sky suppression

# ---- WLS filtering (ximgproc) ----
use_wls = True
wls_lambda = 2000.0        # 2000–12000 typical
wls_sigma = 0.8           # 0.8–1.5 typical

# ---- Outputs ----
write_ptcloud = True
use_xyz_bounds = True
xyz_bounds_x = (-20, 20)   # keep xmin <= X <= xmax
xyz_bounds_y = (-20, 20)   # keep ymin <= Y <= ymax
xyz_bounds_z = (1, 30)     # keep zmin <= Z <= zmax

# ======================== SGM IMPLEMENTATIONS ========================

def compute_disparity_opencv_sgbm(img_left, img_right):
    """Standard OpenCV StereoSGBM implementation."""
    sgbm_cfg = {
        "min_disparity": min_disparity,
        "num_disparities": num_disparities,
        "block_size": opencv_block_size,
        "uniqueness_ratio": uniqueness_threshold,
        "speckle_window_size": speckle_window,
        "speckle_range": speckle_range,
        "disp12_max_diff": disp12_maxdiff,
        "pre_filter_cap": prefilter_cap,
        "mode": opencv_mode,
        "P1": sgm_P1,
        "P2": sgm_P2,
    }
    
    matcher, min_d, num_disp = build_sgbm(sgbm_cfg)
    disparity_16 = matcher.compute(img_left, img_right)
    
    # Convert to float32 and scale
    disparity = disparity_16.astype(np.float32) / 16.0
    disparity[disparity <= min_d] = -1  # Mark invalid disparities
    
    return disparity

def compute_disparity_opencv_sgm(img_left, img_right):
    """OpenCV pixel-level SGM using ximgproc (if available)."""
    try:
        # Try OpenCV's pixel-level SGM
        disparity = cv2.ximgproc.disparitySGM(
            img_left, img_right,
            vis=False,
            P1=sgm_P1,
            P2=sgm_P2,
            uniquenessThreshold=uniqueness_threshold
        )
        
        # Handle the output format
        if disparity.dtype == np.int16:
            disparity = disparity.astype(np.float32) / 16.0
        
        disparity[disparity <= min_disparity] = -1
        return disparity
        
    except AttributeError:
        print("[ERROR] OpenCV SGM not available. Falling back to StereoSGBM.")
        return compute_disparity_opencv_sgbm(img_left, img_right)

def compute_disparity_hirschmuller(img_left, img_right):
    """Custom Hirschmuller SGM implementation."""
    
    def birchfield_tomasi_cost(img_left, img_right, d):
        """Simplified Birchfield-Tomasi cost."""
        h, w = img_left.shape
        cost = np.full((h, w), 255, dtype=np.uint8)
        
        if d == 0:
            cost = np.abs(img_left.astype(np.int16) - img_right.astype(np.int16)).astype(np.uint8)
        elif d > 0 and d < w:
            cost[:, d:] = np.abs(img_left[:, d:].astype(np.int16) - 
                                img_right[:, :-d].astype(np.int16)).astype(np.uint8)
        elif d < 0 and abs(d) < w:
            cost[:, :w+d] = np.abs(img_left[:, :w+d].astype(np.int16) - 
                                  img_right[:, -d:].astype(np.int16)).astype(np.uint8)
        
        return cost

    def compute_path_cost(cost_volume, direction, P1, P2):
        """Compute path costs along one direction."""
        h, w, num_disp = cost_volume.shape
        path_cost = np.zeros_like(cost_volume, dtype=np.float32)
        
        # 8 directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        dr, dc = directions[direction % len(directions)]
        
        # Determine processing order
        if dr >= 0:
            r_start, r_end, r_step = h - 1, -1, -1
        else:
            r_start, r_end, r_step = 0, h, 1
            
        if dc >= 0:
            c_start, c_end, c_step = w - 1, -1, -1
        else:
            c_start, c_end, c_step = 0, w, 1
        
        # Initialize border
        if dr == 0:  # Horizontal
            for r in range(h):
                path_cost[r, c_start, :] = cost_volume[r, c_start, :]
        elif dc == 0:  # Vertical
            for c in range(w):
                path_cost[r_start, c, :] = cost_volume[r_start, c, :]
        else:  # Diagonal
            path_cost[r_start, c_start, :] = cost_volume[r_start, c_start, :]
        
        # Process pixels
        for r in range(r_start + r_step, r_end, r_step):
            for c in range(c_start + c_step, c_end, c_step):
                prev_r, prev_c = r - dr, c - dc
                
                if prev_r < 0 or prev_r >= h or prev_c < 0 or prev_c >= w:
                    path_cost[r, c, :] = cost_volume[r, c, :]
                    continue
                
                prev_costs = path_cost[prev_r, prev_c, :]
                min_prev = np.min(prev_costs)
                
                if not np.isfinite(min_prev):
                    path_cost[r, c, :] = cost_volume[r, c, :]
                    continue
                
                # Equation (13) implementation
                for d in range(num_disp):
                    current_cost = cost_volume[r, c, d]
                    
                    costs = [
                        prev_costs[d],          # Same disparity
                        min_prev + P2           # Any other disparity + large penalty
                    ]
                    
                    # Small disparity changes
                    if d > 0:
                        costs.append(prev_costs[d-1] + P1)
                    if d < num_disp - 1:
                        costs.append(prev_costs[d+1] + P1)
                    
                    path_cost[r, c, d] = current_cost + min(costs) - min_prev
        
        return path_cost

    # Main Hirschmuller SGM algorithm
    h, w = img_left.shape
    print(f"  Running Hirschmuller SGM on {h}x{w} image...")
    
    # Step 1: Compute matching costs
    print(f"  Computing matching costs...")
    cost_volume = np.zeros((h, w, num_disparities), dtype=np.float32)
    
    for d in range(num_disparities):
        disparity = min_disparity + d
        if hirschmuller_cost_function == "BT":
            cost_volume[:, :, d] = birchfield_tomasi_cost(img_left, img_right, disparity)
        else:  # SAD
            if disparity == 0:
                cost_volume[:, :, d] = np.abs(img_left.astype(np.int16) - img_right.astype(np.int16))
            elif disparity > 0 and disparity < w:
                cost_volume[:, :disparity, d] = 255
                cost_volume[:, disparity:, d] = np.abs(
                    img_left[:, disparity:].astype(np.int16) - 
                    img_right[:, :-disparity].astype(np.int16)
                )
    
    # Step 2: Aggregate costs along paths
    print(f"  Aggregating costs along {hirschmuller_directions} directions...")
    aggregated_cost = np.zeros_like(cost_volume, dtype=np.float32)
    
    for direction in range(hirschmuller_directions):
        print(f"    Direction {direction+1}/{hirschmuller_directions}", end='\r')
        path_cost = compute_path_cost(cost_volume, direction, sgm_P1, sgm_P2)
        aggregated_cost += path_cost
    
    print()  # New line
    
    # Step 3: Winner-takes-all
    print(f"  Computing final disparities...")
    disparity_map = np.argmin(aggregated_cost, axis=2).astype(np.float32)
    disparity_map += min_disparity
    
    # Simple post-processing
    min_cost = np.min(aggregated_cost, axis=2)
    second_min = np.full((h, w), np.inf)
    
    for d in range(num_disparities):
        min_cost_idx = np.argmin(aggregated_cost, axis=2)
        mask = (min_cost_idx != d)
        second_min = np.minimum(second_min, 
                              np.where(mask, aggregated_cost[:, :, d], np.inf))
    
    # Uniqueness check
    valid_mask = (min_cost > 0)
    ratio = np.zeros_like(min_cost)
    ratio[valid_mask] = ((second_min[valid_mask] - min_cost[valid_mask]) / 
                       min_cost[valid_mask] * 100)
    
    unique_mask = (ratio > uniqueness_threshold * 0.5)
    disparity_map[~unique_mask] = -1
    
    return disparity_map

def compute_disparity_matlab_style(img_left, img_right):
    """OpenCV StereoSGBM with MATLAB-like parameters."""
    print("  Using MATLAB-style parameters with OpenCV StereoSGBM")
    return compute_disparity_opencv_sgbm(img_left, img_right)

# Algorithm dispatcher
DISPARITY_ALGORITHMS = {
    "opencv_sgbm": compute_disparity_opencv_sgbm,
    "opencv_sgm": compute_disparity_opencv_sgm,
    "hirschmuller": compute_disparity_hirschmuller,
    "matlab_style": compute_disparity_matlab_style
}

def compute_disparity(img_left, img_right, algorithm="opencv_sgbm"):
    """Compute disparity using selected algorithm."""
    if algorithm not in DISPARITY_ALGORITHMS:
        print(f"[WARN] Unknown algorithm '{algorithm}'. Using 'opencv_sgbm'.")
        algorithm = "opencv_sgbm"
    
    print(f"Computing disparity using: {algorithm}")
    print(f"  Parameters: P1={sgm_P1}, P2={sgm_P2}")
    if algorithm in ["opencv_sgbm", "matlab_style"]:
        print(f"  Block size: {opencv_block_size}, Mode: {opencv_mode}")
    
    start_time = time.time()
    disparity = DISPARITY_ALGORITHMS[algorithm](img_left, img_right)
    elapsed = time.time() - start_time
    
    print(f"  Completed in {elapsed:.1f}s")
    return disparity

def main():
    # ---------- Inputs ----------
    calib_path = calib or pick_file_gui()
    wave_path = wave or pick_dir_gui()

    if not calib_path or not wave_path:
        sys.exit("Missing calib or wave (empty and GUI canceled).")
    if not os.path.exists(calib_path):
        sys.exit(f"Calibration file not found: {calib_path}")
    if not (os.path.isdir(os.path.join(wave_path, "cam0")) and os.path.isdir(os.path.join(wave_path, "cam1"))):
        sys.exit("wave must contain cam0/ and cam1/ subfolders.")

    print(f"=== STOKECAM ProcessLevel1 - {sgm_algorithm.upper()} ===")
    
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

    print(f"Found {n} image pairs to process")

    # ---------- Rectification maps ----------
    (map10, map11, map20, map21), (_, _, _, _, Q), (roi1, roi2), crop = stereo_rectify_maps(
        K0, D0, K1, D1, R, T, image_size, crop_valid=crop_valid)
    crop_tuple = tuple(map(int, crop)) if (crop is not None) else None

    # ---------- Output dirs ----------
    l1_dir = os.path.join(wave_path, f"L1_{sgm_algorithm}")
    out_dir = os.path.join(wave_path, "figs", f"disparityMaps_{sgm_algorithm}")
    os.makedirs(l1_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # # ---------- Setup WLS filtering ----------
    # right_matcher = None
    # wls_filter = None
    
    # if use_wls and sgm_algorithm == "opencv_sgbm" and xip is not None:
    #     # WLS only works with OpenCV StereoSGBM
    #     sgbm_cfg = {
    #         "min_disparity": min_disparity,
    #         "num_disparities": num_disparities,
    #         "block_size": opencv_block_size,
    #         "uniqueness_ratio": uniqueness_threshold,
    #         "speckle_window_size": speckle_window,
    #         "speckle_range": speckle_range,
    #         "disp12_max_diff": disp12_maxdiff,
    #         "pre_filter_cap": prefilter_cap,
    #         "mode": opencv_mode,
    #         "P1": sgm_P1,
    #         "P2": sgm_P2,
    #     }
    #     matcher, _, _ = build_sgbm(sgbm_cfg)
        
    #     try:
    #         right_matcher = xip.createRightMatcher(matcher)
    #         wls_filter = xip.createDisparityWLSFilter(matcher_left=matcher)
    #         wls_filter.setLambda(float(wls_lambda))
    #         wls_filter.setSigmaColor(float(wls_sigma))
    #         print("WLS filtering enabled")
    #     except Exception as e:
    #         print(f"[WARN] WLS setup failed: {e}")
    #         use_wls = False

    # ---------- Precompute CLAHE if used ----------
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_tiles) if clahe_enabled else None

    # ---------- Process frames ----------
    total_time = 0
    
    for i in range(n):
        print(f"\n=== Processing pair {i+1}/{n} ===")
        
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
            gL = clahe.apply(gL)
            gR = clahe.apply(gR)

        # ---------- Disparity ----------
        start_time = time.time()
        
        if use_wls and sgm_algorithm == "opencv_sgbm" and wls_filter is not None:
            # Use WLS-filtered OpenCV SGBM
            sgbm_cfg = {
                "min_disparity": min_disparity,
                "num_disparities": num_disparities,
                "block_size": opencv_block_size,
                "uniqueness_ratio": uniqueness_threshold,
                "speckle_window_size": speckle_window,
                "speckle_range": speckle_range,
                "disp12_max_diff": disp12_maxdiff,
                "pre_filter_cap": prefilter_cap,
                "mode": opencv_mode,
                "P1": sgm_P1,
                "P2": sgm_P2,
            }
            matcher, _, _ = build_sgbm(sgbm_cfg)
            
            dispL_16 = matcher.compute(gL, gR)
            dispR_16 = right_matcher.compute(gR, gL)
            
            try:
                disp_16 = wls_filter.filter(dispL_16, rL, disparity_map_right=dispR_16, right_view=rR)
                disp = disp_16.astype(np.float32) / 16.0
                print(f"Applied WLS filtering")
            except Exception as e:
                print(f"[WARN] WLS failed ({e}); using raw disparity.")
                disp = dispL_16.astype(np.float32) / 16.0
        else:
            # Use selected algorithm
            disp = compute_disparity(gL, gR, sgm_algorithm)
        
        elapsed = time.time() - start_time
        total_time += elapsed

        # ---------- Save disparity visualization ----------
        stem = os.path.splitext(os.path.basename(fL))[0]
        
        # Colorize disparity map
        disp_colored = colorize_disparity(disp)
        disp_path = os.path.join(out_dir, f"{stem}_disparity.png")
        cv2.imwrite(disp_path, disp_colored)

        # ---------- Generate point cloud ----------
        if write_ptcloud:
            # Reconstruct 3D points
            points3D = cv2.reprojectImageTo3D(disp, Q)
            points3D = points3D / 1000.0  # Convert to meters

            # Get colors
            colors = cv2.cvtColor(rL, cv2.COLOR_BGR2RGB)

            # Reshape for filtering
            points3D_flat = points3D.reshape(-1, 3)
            colors_flat = colors.reshape(-1, 3)

            # Filter valid points
            valid = np.isfinite(points3D_flat).all(axis=1) & (disp.flatten() > 0)
            
            if use_xyz_bounds:
                X, Y, Z = points3D_flat[valid].T
                in_bounds = ((X >= xyz_bounds_x[0]) & (X <= xyz_bounds_x[1]) &
                           (Y >= xyz_bounds_y[0]) & (Y <= xyz_bounds_y[1]) &
                           (Z >= xyz_bounds_z[0]) & (Z <= xyz_bounds_z[1]))
                
                points3D_final = points3D_flat[valid][in_bounds]
                colors_final = colors_flat[valid][in_bounds]
            else:
                points3D_final = points3D_flat[valid]
                colors_final = colors_flat[valid]

            # Manual polygon selection (using your existing function)
            if len(points3D_final) > 0:
                points3D_final, colors_final, _ = select_points_via_polygon(
                    img_bgr=rL, 
                    points3D=points3D_final.reshape(points3D.shape), 
                    colors=colors_final.reshape(colors.shape), 
                    base_mask=None
                )

                # Save PLY file
                ply_path = os.path.join(l1_dir, f"{stem}.ply")
                with open(ply_path, 'w') as ply:
                    ply.write("ply\nformat ascii 1.0\n")
                    ply.write(f"element vertex {len(points3D_final)}\n")
                    ply.write("property float x\nproperty float y\nproperty float z\n")
                    ply.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
                    ply.write("end_header\n")
                    for p, c in zip(points3D_final, colors_final):
                        ply.write(f"{p[0]} {p[1]} {p[2]} {int(c[0])} {int(c[1])} {int(c[2])}\n")

                print(f"Saved {len(points3D_final)} points to {ply_path}")
            else:
                print("No valid points generated")

        print(f"Processed in {elapsed:.1f}s")

    # ---------- Summary ----------
    avg_time = total_time / n if n > 0 else 0
    print(f"\n=== Processing Complete ===")
    print(f"Algorithm: {sgm_algorithm}")
    print(f"Average time per pair: {avg_time:.1f}s")
    print(f"Total processing time: {total_time:.1f}s")
    print(f"Output directories:")
    print(f"  Point clouds: {l1_dir}")
    print(f"  Disparity maps: {out_dir}")

if __name__ == "__main__":
    main()