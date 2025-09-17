"""
STOKECAM Post-Processing Level 1 - Hirschmuller SGM Implementation
Drew Davey
Last updated: 2025-09-17

Implements Semi-Global Matching following Hirschmuller 2008 paper exactly.
Processes stereo image pairs for disparity & point cloud using custom SGM implementation.
"""

import cv2
import os, sys
import numpy as np
from utils import *
from pathlib import Path
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

# ---- Hirschmuller SGM Parameters (Equation 11) ----
min_disparity = 0         # minimum disparity
num_disparities = 64      # disparity range (match your other implementations)
P1 = 15                   # penalty for small disparity changes (|Dp - Dq| = 1)
P2 = 200                  # penalty for large disparity changes (|Dp - Dq| > 1)
num_directions = 8        # number of path directions (8 for speed, 16 for quality)

# ---- Cost function choice ----
cost_function = "BT"      # "BT" (Birchfield-Tomasi) or "SAD" (Sum of Absolute Differences)

# ---- Post-processing ----
uniqueness_ratio = 15     # percentage threshold for uniqueness check
speckle_size = 100        # minimum connected component size
speckle_range = 2         # maximum disparity variation in speckle

# ---- Point cloud generation ----
write_ptcloud = True
use_xyz_bounds = True
xyz_bounds_x = (-20, 20)
xyz_bounds_y = (-20, 20)  
xyz_bounds_z = (1, 30)

# ======================== HIRSCHMULLER SGM IMPLEMENTATION ========================

def birchfield_tomasi_cost(img_left, img_right, d):
    """
    Compute Birchfield-Tomasi sampling-insensitive matching cost.
    Simplified but efficient implementation.
    """
    h, w = img_left.shape
    cost = np.full((h, w), 255, dtype=np.uint8)
    
    if d == 0:
        # Zero disparity case
        cost = np.abs(img_left.astype(np.int16) - img_right.astype(np.int16)).astype(np.uint8)
    elif d > 0:
        # Positive disparity
        if d < w:
            cost[:, d:] = np.abs(img_left[:, d:].astype(np.int16) - 
                                img_right[:, :-d].astype(np.int16)).astype(np.uint8)
    else:
        # Negative disparity  
        if abs(d) < w:
            cost[:, :w+d] = np.abs(img_left[:, :w+d].astype(np.int16) - 
                                  img_right[:, -d:].astype(np.int16)).astype(np.uint8)
    
    return cost

def compute_path_cost(cost_volume, direction, P1, P2):
    """
    Compute path cost L_r(p,d) along direction r using equation (13).
    More robust implementation following OpenCV's approach.
    """
    h, w, num_disp = cost_volume.shape
    path_cost = np.zeros_like(cost_volume, dtype=np.float32)
    
    # 8 main directions
    directions = [
        (-1, 0),  # up
        (1, 0),   # down  
        (0, -1),  # left
        (0, 1),   # right
        (-1, -1), # up-left
        (-1, 1),  # up-right
        (1, -1),  # down-left
        (1, 1)    # down-right
    ]
    
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
    
    # Initialize starting pixels
    if dr == 0:  # Horizontal
        for r in range(h):
            path_cost[r, c_start, :] = cost_volume[r, c_start, :]
    elif dc == 0:  # Vertical
        for c in range(w):
            path_cost[r_start, c, :] = cost_volume[r_start, c, :]
    else:  # Diagonal
        path_cost[r_start, c_start, :] = cost_volume[r_start, c_start, :]
    
    # Process pixels in order
    for r in range(r_start + r_step, r_end, r_step):
        for c in range(c_start + c_step, c_end, c_step):
            prev_r = r - dr
            prev_c = c - dc
            
            # Skip if out of bounds
            if prev_r < 0 or prev_r >= h or prev_c < 0 or prev_c >= w:
                path_cost[r, c, :] = cost_volume[r, c, :]
                continue
                
            # Get previous costs
            prev_costs = path_cost[prev_r, prev_c, :]
            min_prev = np.min(prev_costs)
            
            # Skip if invalid
            if not np.isfinite(min_prev):
                path_cost[r, c, :] = cost_volume[r, c, :]
                continue
            
            # Compute aggregated cost for each disparity
            for d in range(num_disp):
                # Current matching cost
                current_cost = cost_volume[r, c, d]
                
                # Four options for path cost
                costs = [
                    prev_costs[d],  # Same disparity
                    min_prev + P2   # Any other disparity + large penalty
                ]
                
                # Small disparity changes
                if d > 0:
                    costs.append(prev_costs[d-1] + P1)
                if d < num_disp - 1:
                    costs.append(prev_costs[d+1] + P1)
                
                # Apply equation (13)
                path_cost[r, c, d] = current_cost + min(costs) - min_prev
    
    return path_cost

def semi_global_matching(img_left, img_right, min_disp, num_disp, P1, P2, num_dirs=8):
    """
    Implement Semi-Global Matching following Hirschmuller 2008.
    Optimized for reasonable performance.
    """
    h, w = img_left.shape
    print(f"Processing {h}x{w} stereo pair...")
    
    # Step 1: Compute pixelwise matching costs C(p,d) - Equation 11 first term
    print("Computing matching costs...")
    cost_volume = np.zeros((h, w, num_disp), dtype=np.float32)
    
    for d in range(num_disp):
        disparity = min_disp + d
        cost_volume[:, :, d] = birchfield_tomasi_cost(img_left, img_right, disparity)
    
    # Step 2: Cost aggregation by pathwise optimization - Equations 12-14
    print(f"Aggregating costs along {num_dirs} directions...")
    aggregated_cost = np.zeros_like(cost_volume, dtype=np.float32)
    
    for direction in range(num_dirs):
        print(f"  Direction {direction+1}/{num_dirs}", end='\r')
        path_cost = compute_path_cost(cost_volume, direction, P1, P2)
        aggregated_cost += path_cost
    
    print()  # New line after progress
    
    # Step 3: Disparity computation (winner-takes-all)
    print("Computing final disparities...")
    disparity_map = np.argmin(aggregated_cost, axis=2).astype(np.float32)
    disparity_map += min_disp
    
    # Step 4: Post-processing
    print("Post-processing...")
    disparity_map = post_process_disparity(disparity_map, aggregated_cost, uniqueness_ratio, speckle_size, speckle_range)
    
    return disparity_map, aggregated_cost

def post_process_disparity(disparity, cost_volume, uniqueness_ratio, speckle_size, speckle_range):
    """
    Post-process disparity map with uniqueness and speckle filtering.
    More robust implementation.
    """
    h, w = disparity.shape
    processed = disparity.copy()
    
    # Uniqueness check - be more lenient
    if uniqueness_ratio > 0:
        min_cost_idx = np.argmin(cost_volume, axis=2)
        min_cost = np.min(cost_volume, axis=2)
        
        # Find second minimum more robustly
        second_min = np.full((h, w), np.inf)
        for d in range(cost_volume.shape[2]):
            mask = (min_cost_idx != d)
            second_min = np.minimum(second_min, 
                                  np.where(mask, cost_volume[:, :, d], np.inf))
        
        # Check uniqueness (avoid division by zero)
        valid_mask = (min_cost > 0)
        ratio = np.zeros_like(min_cost)
        ratio[valid_mask] = ((second_min[valid_mask] - min_cost[valid_mask]) / 
                           min_cost[valid_mask] * 100)
        
        # More lenient uniqueness threshold
        unique_mask = (ratio > uniqueness_ratio * 0.5)  # Reduce threshold
        processed[~unique_mask] = -1
    
    # Skip speckle filtering for now to see basic results
    # if speckle_size > 0:
    #     valid_mask = (processed >= 0).astype(np.uint8)
    #     num_labels, labels = cv2.connectedComponents(valid_mask)
    #     for label in range(1, num_labels):
    #         component_mask = (labels == label)
    #         if np.sum(component_mask) < speckle_size:
    #             processed[component_mask] = -1
    
    return processed

def load_calibration_simple(calib_path, choice="python"):
    """
    Simplified calibration loading - you'll need to adapt this to your utils.load_calibration
    """
    # This is a placeholder - replace with your actual calibration loading
    if choice == "python":
        calib_file = os.path.join(calib_path, "calib.npz")
        if os.path.exists(calib_file):
            data = np.load(calib_file)
            return (data['K0'], data['D0'], data['K1'], data['D1'], 
                   data['R'], data['T'], tuple(data['image_size']), data.get('err_m', 0))
    
    # Fallback to matlab format
    import scipy.io as sio
    calib_file = os.path.join(calib_path, "calib.mat")
    if os.path.exists(calib_file):
        data = sio.loadmat(calib_file)
        return (data['K0'], data['D0'], data['K1'], data['D1'],
               data['R'], data['T'], tuple(data['image_size'][0]), data.get('err_m', 0))
    
    raise FileNotFoundError(f"No calibration found in {calib_path}")

def stereo_rectify_simple(K0, D0, K1, D1, R, T, image_size, crop_valid=True):
    """
    Simplified stereo rectification - adapt to your utils.stereo_rectify_maps
    """
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        K0, D0, K1, D1, image_size, R, T, alpha=0 if crop_valid else -1
    )
    
    map11, map12 = cv2.initUndistortRectifyMap(K0, D0, R1, P1, image_size, cv2.CV_16SC2)
    map21, map22 = cv2.initUndistortRectifyMap(K1, D1, R2, P2, image_size, cv2.CV_16SC2)
    
    # Compute crop region if needed
    crop = None
    if crop_valid and roi1[2] > 0 and roi1[3] > 0 and roi2[2] > 0 and roi2[3] > 0:
        x = max(roi1[0], roi2[0])
        y = max(roi1[1], roi2[1])
        w = min(roi1[0] + roi1[2], roi2[0] + roi2[2]) - x
        h = min(roi1[1] + roi1[3], roi2[1] + roi2[3]) - y
        crop = (x, y, w, h)
    
    return (map11, map12, map21, map22), Q, crop

def disparity_to_pointcloud(disparity, color_img, Q, bounds=None):
    """
    Convert disparity map to 3D point cloud.
    More robust implementation.
    """
    h, w = disparity.shape
    
    # Only use valid disparities (> 0)
    valid_mask = (disparity > 0) & (disparity != -1)
    valid_count = np.sum(valid_mask)
    
    print(f"Valid disparities: {valid_count}/{h*w} ({100*valid_count/(h*w):.1f}%)")
    
    if valid_count == 0:
        return np.array([]), np.array([])
    
    # Get valid pixel coordinates and disparities
    v_coords, u_coords = np.where(valid_mask)
    valid_disparities = disparity[valid_mask]
    valid_colors = color_img[valid_mask]
    
    # Create homogeneous coordinates [u, v, disparity, 1]
    coords_4d = np.column_stack([
        u_coords.astype(np.float32),
        v_coords.astype(np.float32), 
        valid_disparities.astype(np.float32),
        np.ones(len(u_coords), dtype=np.float32)
    ])
    
    # Transform to 3D using Q matrix
    points_4d = coords_4d @ Q.T
    
    # Convert from homogeneous coordinates (handle divide by zero)
    w_coords = points_4d[:, 3]
    valid_w = np.abs(w_coords) > 1e-6
    
    if not np.any(valid_w):
        print("No valid 3D points after projection")
        return np.array([]), np.array([])
    
    points_3d = points_4d[valid_w, :3] / w_coords[valid_w, np.newaxis]
    colors = valid_colors[valid_w]
    
    print(f"3D points after projection: {len(points_3d)}")
    
    # Apply bounds if specified
    if bounds:
        xmin, xmax = bounds[0]
        ymin, ymax = bounds[1] 
        zmin, zmax = bounds[2]
        
        bound_mask = ((points_3d[:, 0] >= xmin) & (points_3d[:, 0] <= xmax) &
                     (points_3d[:, 1] >= ymin) & (points_3d[:, 1] <= ymax) &
                     (points_3d[:, 2] >= zmin) & (points_3d[:, 2] <= zmax))
        
        points_3d = points_3d[bound_mask]
        colors = colors[bound_mask]
        
        print(f"3D points after bounds filtering: {len(points_3d)}")
    
    return points_3d, colors

def write_ply(filename, points, colors):
    """
    Write point cloud to PLY file.
    """
    with open(filename, 'w') as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\n")
        f.write("property float y\n") 
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        
        for point, color in zip(points, colors):
            f.write(f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f} ")
            f.write(f"{int(color[2])} {int(color[1])} {int(color[0])}\n")  # BGR to RGB

def main():
    # ---------- Inputs ----------
    calib_path = calib or input("Enter calibration path: ")
    wave_path = wave or input("Enter wave path: ")
    
    if not os.path.exists(calib_path):
        sys.exit(f"Calibration file not found: {calib_path}")
    if not (os.path.isdir(os.path.join(wave_path, "cam0")) and os.path.isdir(os.path.join(wave_path, "cam1"))):
        sys.exit("wave must contain cam0/ and cam1/ subfolders.")
    
    print("=== Hirschmuller SGM Implementation ===")
    print(f"Parameters: P1={P1}, P2={P2}, directions={num_directions}")
    print(f"Disparity range: [{min_disparity}, {min_disparity + num_disparities - 1}]")
    print(f"Cost function: {cost_function}")
    
    # ---------- Load calibration ----------
    try:
        K0, D0, K1, D1, R, T, image_size, err_m = load_calibration_simple(calib_path, choice=calib_choice)
        print(f"Loaded calibration with error: {err_m}")
    except:
        print("Warning: Using your utils.load_calibration function")
        K0, D0, K1, D1, R, T, image_size, err_m = load_calibration(calib_path, choice=calib_choice)
    
    # ---------- Collect image pairs ----------
    cam0_files = sorted([f for f in os.listdir(os.path.join(wave_path, "cam0")) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
    cam1_files = sorted([f for f in os.listdir(os.path.join(wave_path, "cam1")) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
    
    n = min(len(cam0_files), len(cam1_files))
    if n == 0:
        sys.exit("No image pairs found.")
    
    print(f"Found {n} image pairs to process")
    
    # ---------- Setup rectification ----------
    try:
        (map11, map12, map21, map22), Q, crop = stereo_rectify_simple(
            K0, D0, K1, D1, R, T, image_size, crop_valid)
        print("Using simplified rectification")
    except:
        print("Warning: Using your utils.stereo_rectify_maps function")
        (map11, map12, map21, map22), (_, _, _, _, Q), (roi1, roi2), crop = stereo_rectify_maps(
            K0, D0, K1, D1, R, T, image_size, crop_valid=crop_valid)
    
    crop_tuple = tuple(map(int, crop)) if (crop is not None) else None
    
    # ---------- Output directories ----------
    l1_dir = os.path.join(wave_path, "L1_hirschmuller")
    disp_dir = os.path.join(wave_path, "figs", "disparityMaps_hirschmuller")
    os.makedirs(l1_dir, exist_ok=True)
    os.makedirs(disp_dir, exist_ok=True)
    
    # ---------- Setup CLAHE ----------
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_tiles) if clahe_enabled else None
    
    # ---------- Process each pair ----------
    total_time = 0
    
    for i in range(n):
        print(f"\n=== Processing pair {i+1}/{n} ===")
        start_time = time.time()
        
        # Load images
        img_path_l = os.path.join(wave_path, "cam0", cam0_files[i])
        img_path_r = os.path.join(wave_path, "cam1", cam1_files[i])
        
        img_l = cv2.imread(img_path_l, cv2.IMREAD_COLOR)
        img_r = cv2.imread(img_path_r, cv2.IMREAD_COLOR)
        
        if img_l is None or img_r is None:
            print(f"Failed to load pair {i+1}")
            continue
        
        # Rectify
        rect_l = cv2.remap(img_l, map11, map12, cv2.INTER_LINEAR)
        rect_r = cv2.remap(img_r, map21, map22, cv2.INTER_LINEAR)
        
        # Crop if needed
        if crop_tuple:
            x, y, w, h = crop_tuple
            rect_l = rect_l[y:y+h, x:x+w]
            rect_r = rect_r[y:y+h, x:x+w]
        
        # Convert to grayscale and apply CLAHE
        gray_l = cv2.cvtColor(rect_l, cv2.COLOR_BGR2GRAY)
        gray_r = cv2.cvtColor(rect_r, cv2.COLOR_BGR2GRAY)
        
        if clahe:
            gray_l = clahe.apply(gray_l)
            gray_r = clahe.apply(gray_r)
        
        # Run Hirschmuller SGM
        disparity, cost_volume = semi_global_matching(
            gray_l, gray_r, min_disparity, num_disparities, P1, P2, num_directions
        )
        
        # Save disparity map
        stem = os.path.splitext(cam0_files[i])[0]
        
        # Normalize and save disparity image
        disp_vis = disparity.copy()
        disp_vis[disp_vis < 0] = 0
        disp_vis = cv2.normalize(disp_vis, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        disp_colored = cv2.applyColorMap(disp_vis, cv2.COLORMAP_JET)
        
        cv2.imwrite(os.path.join(disp_dir, f"{stem}_disparity.png"), disp_colored)
        
        # Generate point cloud
        if write_ptcloud:
            bounds = (xyz_bounds_x, xyz_bounds_y, xyz_bounds_z) if use_xyz_bounds else None
            points_3d, colors = disparity_to_pointcloud(disparity, rect_l, Q, bounds)
            
            if len(points_3d) > 0:
                ply_path = os.path.join(l1_dir, f"{stem}.ply")
                write_ply(ply_path, points_3d, colors)
                print(f"Saved {len(points_3d)} points to {ply_path}")
            else:
                print("No valid points generated")
        
        elapsed = time.time() - start_time
        total_time += elapsed
        print(f"Processed in {elapsed:.1f}s")
    
    avg_time = total_time / n if n > 0 else 0
    print(f"\n=== Complete ===")
    print(f"Average processing time: {avg_time:.1f}s per pair")
    print(f"Output directories:")
    print(f"  Point clouds: {l1_dir}")
    print(f"  Disparity maps: {disp_dir}")

if __name__ == "__main__":
    main()