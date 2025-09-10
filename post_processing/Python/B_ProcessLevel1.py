"""
STOKECAM Post-Processing Level 1
Drew Davey
Last updated: 2025-08-21

Processes stereo image pairs for disparity & point cloud.
"""
# =================== PACKAGES ===============================
import cv2
import os, sys
import numpy as np
from utils import *
from pathlib import Path
import cv2.ximgproc as xip

# ======================= INPUTS ============================
calib   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/calibrations/calib4_SIO"
# wave    = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/20250814/141908_session_bright/wave1"
wave   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/20250429/003014_session_auto/wave6"
# wave   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/testing/static/staticStairs/wave1"
# wave   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/20250814/141908_session_bright/wave6"
# wave   = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA/20250813/222744_session_auto/wave1"
# wave   = "C:/Users/drew/OneDrive - UC San Diego/FSR/pres_reports/paper1/data/wave5"

# ---- Use Matlab or Python calib ----
# calib_choice = "matlab"
calib_choice = "python"

# ---- Run behavior ----
crop_valid  = True       # use common valid ROI from stereoRectify
save_params = True       # write params.json to output folder

# ---- Preprocessing (CLAHE) ----
clahe_enabled = True
clahe_clip    = 2.0
clahe_tiles   = (5, 5)

# ---- Disparity (StereoSGBM) ----
sgbm_min_disparity   = 0      # inclusive
sgbm_num_disparities = 64    # multiple of 16
sgbm_block_size      = 3      # odd, >=3
sgbm_uniqueness      = 15
sgbm_speckle_window  = 120
sgbm_speckle_range   = 2
sgbm_disp12_maxdiff  = 1
sgbm_prefilter_cap   = 31
sgbm_mode            = "HH"  # "SGBM", "SGBM_3WAY", "HH", "HH4"
sgbm_P1              = 8 * 3 * (5 ** 2)  # OpenCV format
sgbm_P2              = 48 * 3 * (5 ** 2)
# sgbm_P1              = 15  # Copying MATLAB
# sgbm_P2              = 200 # Copying MATLAB

# ---- Post-masking / refinement ----
use_texture_mask = True    # gradient-based low-texture suppression
use_sky_suppress = True    # HSV low-S/high-V sky suppression

# ---- WLS filtering (ximgproc) ----
use_wls    = False
wls_lambda = 2000.0        # 2000–12000 typical
wls_sigma  = 0.8           # 0.8–1.5 typical

# ---- Outputs ----
write_ptcloud   = True
use_xyz_bounds  = True
xyz_bounds_x    = (-20, 20)   # keep xmin <= X <= xmax
xyz_bounds_y    = (-20, 20)   # keep ymin <= Y <= ymax
xyz_bounds_z    = (1, 30)     # keep zmin <= Z <= zmax

# ------------------------------- Main ----------------------------------
def main():
    # ---------- Inputs ----------
    calib_path = calib or pick_file_gui()
    wave_path  = wave  or pick_dir_gui()

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

    # ---------- Build SGBM once ----------
    sgbm_cfg = {
        "min_disparity": sgbm_min_disparity,
        "num_disparities": sgbm_num_disparities,
        "block_size": sgbm_block_size,
        "uniqueness_ratio": sgbm_uniqueness,
        "speckle_window_size": sgbm_speckle_window,
        "speckle_range": sgbm_speckle_range,
        "disp12_max_diff": sgbm_disp12_maxdiff,
        "pre_filter_cap": sgbm_prefilter_cap,
        "mode": sgbm_mode,
        "P1": sgbm_P1,
        "P2": sgbm_P2,
    }
    matcher, min_d, num_disp = build_sgbm(sgbm_cfg)
    max_d = min_d + num_disp - 1

    # Prepare right matcher & WLS (if available & requested)
    right_matcher = xip.createRightMatcher(matcher) if (use_wls and xip is not None) else None
    wls_filter = None
    if use_wls and xip is not None:
        try:
            wls_filter = xip.createDisparityWLSFilter(matcher_left=matcher)
        except Exception:
            wls_filter = xip.createDisparityWLSFilterGeneric(False)
        wls_filter.setLambda(float(wls_lambda))
        wls_filter.setSigmaColor(float(wls_sigma))

    # ---------- Precompute CLAHE if used ----------
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_tiles) if clahe_enabled else None

    # ---------- Process frames ----------
    for i in range(n):
    # for i in range(3, 5):
    # for i in range(38, 41):
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

        # ---------- Disparity ----------
        dispL_16 = matcher.compute(gL, gR)

        if wls_filter is not None and right_matcher is not None:
            dispR_16 = right_matcher.compute(gR, gL)
            try:
                disp_16 = wls_filter.filter(dispL_16, rL, disparity_map_right=dispR_16, right_view=rR)
            except Exception as e:
                print(f"[WARN] WLS failed ({e}); falling back to raw SGBM.")
                disp_16 = dispL_16
        else:
            disp_16 = dispL_16

        # Convert to float disparity in px
        disp_px = disp_16.astype(np.float32) / 16.0

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

        # set masked to just-below min_d so colorizer maps to low end
        disp_color = np.where(keep_mask, disp_px, min_d - 1.0)

        # ---------- Save disparity (color) ----------
        stem = strip_leading_cam_prefix(Path(fL).stem)
        out_dispc = os.path.join(out_dir, f"{stem}_color.png")
        cv2.imwrite(out_dispc, colorize_disparity(disp_color))

        # ---------- Optional point cloud ----------
        if write_ptcloud:
            # Disparity in pixels
            disp = disp_px

            # Reproject to 3D (XYZ in rectified left camera frame)
            points3D = cv2.reprojectImageTo3D(disp, Q)
            points3D = points3D / 1000.0 # convert mm to meters
            colors = cv2.cvtColor(rL, cv2.COLOR_BGR2RGB)

            # Keep finite and plausible disparities
            valid = np.isfinite(disp) & (disp > 0)
            valid &= np.isfinite(points3D).all(axis=2)

            # Crop to XYZ bounds if requested
            if use_xyz_bounds:
                xmin, xmax = xyz_bounds_x
                ymin, ymax = xyz_bounds_y
                zmin, zmax = xyz_bounds_z
                X = points3D[..., 0]
                Y = points3D[..., 1]
                Z = points3D[..., 2]
                in_x = (X >= xmin) & (X <= xmax)
                in_y = (Y >= ymin) & (Y <= ymax)
                in_z = (Z >= zmin) & (Z <= zmax)
                valid &= (in_x & in_y & in_z)

            # Manual crop to polygon
            points3D, colors, _ = select_points_via_polygon(
                img_bgr=rL, points3D=points3D, colors=colors, base_mask=valid)

            ply_path = os.path.join(l1_dir, f"{stem}.ply")
            with open(ply_path, 'w') as ply:
                ply.write("ply\nformat ascii 1.0\n")
                ply.write(f"element vertex {len(points3D)}\n")
                ply.write("property float x\nproperty float y\nproperty float z\n")
                ply.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
                ply.write("end_header\n")
                for p, c in zip(points3D, colors):
                    ply.write(f"{p[0]} {p[1]} {p[2]} {int(c[0])} {int(c[1])} {int(c[2])}\n")

        print(f"Processed {i+1}/{n}")

    print(f"Done. Outputs in: {out_dir}\n")

    #  # ---------- Save run params ----------
    # if save_params:
    #     params_out = {
    #         "calib": str(Path(calib_path).resolve()),
    #         "wave": str(Path(wave_path).resolve()),
    #         "image_size": image_size,
    #         "roi1": tuple(map(int, roi1)),
    #         "roi2": tuple(map(int, roi2)),
    #         "crop": crop_tuple,
    #         "crop_valid": crop_valid,
    #         "clahe": {"enabled": clahe_enabled, "clip_limit": clahe_clip, "tile_grid_size": clahe_tiles},
    #         "sgbm": {
    #             "min_disparity": sgbm_min_disparity,
    #             "num_disparities": sgbm_num_disparities,
    #             "block_size": sgbm_block_size,
    #             "uniqueness_ratio": sgbm_uniqueness,
    #             "speckle_window_size": sgbm_speckle_window,
    #             "speckle_range": sgbm_speckle_range,
    #             "disp12_max_diff": sgbm_disp12_maxdiff,
    #             "pre_filter_cap": sgbm_prefilter_cap,
    #             "mode": sgbm_mode,
    #             "P1": sgbm_P1,
    #             "P2": sgbm_P2,
    #         },
    #         "use_texture_mask": use_texture_mask,
    #         "use_sky_suppress": use_sky_suppress,
    #         "use_wls": use_wls,
    #         "wls_lambda": wls_lambda,
    #         "wls_sigma": wls_sigma,
    #         "write_ptCloud": write_ptcloud,
    #         "use_xyz_bounds": use_xyz_bounds,
    #         "xyz_bounds": {"x": xyz_bounds_x, "y": xyz_bounds_y, "z": xyz_bounds_z},
    #     }
    #     with open(os.path.join(out_dir, "params.json"), "w") as f:
    #         json.dump(params_out, f, indent=2)


if __name__ == "__main__":
    main()
