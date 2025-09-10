"""
STOKECAM Post-Processing
Drew Davey
Last updated: 2025-08-21

Utilities for calibration and stereo rectification.
"""

# =================== PACKAGES ===============================
import os
import cv2
import glob
import math
import json
import numpy as np
from pyproj import CRS, Transformer

# ------------------------------ Utilities ------------------------------
def pick_file_gui(title="Select calib .npz", filetypes=(("NPZ files","*.npz"), ("All","*.*"))):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw()
        path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        root.update(); root.destroy()
        return path
    except Exception:
        return ""

def pick_dir_gui(title="Select wave/calib folder (contains cam0/ cam1/)"):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw()
        path = filedialog.askdirectory(title=title)
        root.update(); root.destroy()
        return path
    except Exception:
        return ""

def sorted_images(folder):
    exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff")
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(folder, e)))
    files.sort()
    return files

def load_pairs(calib_path):
    cam0 = sorted_images(os.path.join(calib_path, "cam0"))
    cam1 = sorted_images(os.path.join(calib_path, "cam1"))
    if len(cam0) == 0 or len(cam1) == 0:
        raise FileNotFoundError("No images found in cam0/ or cam1/ under: " + calib_path)
    n = min(len(cam0), len(cam1))
    return cam0[:n], cam1[:n]

def brighten(img, value=30):
    # Convert to int16 to avoid overflow/underflow
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int16)
    
    # Increase only V (value) channel
    hsv[..., 2] = np.clip(hsv[..., 2] + value, 0, 255)
    
    # Convert back
    hsv = hsv.astype(np.uint8)
    brightened = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return brightened

def detect_points_on_pair(img0, img1, pattern, use_sb=True):
    cols, rows = pattern
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
    gray0 = cv2.cvtColor(img0, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)

    if use_sb and hasattr(cv2, "findChessboardCornersSB"):
        f0, c0 = cv2.findChessboardCornersSB(gray0, (cols, rows), flags=cv2.CALIB_CB_EXHAUSTIVE)
        f1, c1 = cv2.findChessboardCornersSB(gray1, (cols, rows), flags=cv2.CALIB_CB_EXHAUSTIVE)
    else:
        f0, c0 = cv2.findChessboardCorners(gray0, (cols, rows), flags=flags)
        f1, c1 = cv2.findChessboardCorners(gray1, (cols, rows), flags=flags)
        if f0:
            c0 = cv2.cornerSubPix(gray0, c0, (11,11), (-1,-1),
                                  (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5))
        if f1:
            c1 = cv2.cornerSubPix(gray1, c1, (11,11), (-1,-1),
                                  (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5))

    return f0, c0, f1, c1, gray0.shape[::-1]  # (w,h)

def build_object_points(pattern, square_size_mm):
    cols, rows = pattern
    objp = np.zeros((rows*cols, 3), np.float32)
    # grid order matches OpenCV's default: x across cols, y down rows
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= float(square_size_mm)
    return objp

def theoretical_intrinsics_from_spec(img_size, focal_length_mm, pixel_pitch_um):
    """
    fx, fy in pixels = focal_length_mm / pixel_size_mm
    pixel_size_mm = pixel_pitch_um * 1e-3
    cx, cy = image center
    """
    w, h = img_size
    pixel_size_mm = pixel_pitch_um * 1e-3
    fx = focal_length_mm / pixel_size_mm
    fy = focal_length_mm / pixel_size_mm
    cx = w / 2.0
    cy = h / 2.0
    K = np.array([[fx, 0,  cx],
                  [0,  fy, cy],
                  [0,  0,  1]], dtype=np.float64)
    return K

def rotation_angle_from_R(R):
    # Angle of rotation in degrees
    theta = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R) - 1.0)/2.0))))
    return theta

def strip_leading_cam_prefix(name: str):
    """Remove leading '0_' or '1_' from basename."""
    base = os.path.basename(name)
    return base[2:] if base.startswith(("0_", "1_")) else base

def load_calibration(calib_path, choice="python"):
    if choice.lower() == "matlab":
        json_path = os.path.join(calib_path, "calib.json")
        with open(json_path, "r") as f:
            data = json.load(f)
        K0 = np.array(data["K0"])
        D0 = np.array(data["D0"])
        K1 = np.array(data["K1"])
        D1 = np.array(data["D1"])
        R  = np.array(data["R"])
        T  = np.array(data["T"])
        image_size = tuple(data["image_size"])
        err_m = data["err_m"]
    elif choice.lower() == "python":
        npz_path = os.path.join(calib_path, "calib.npz")
        data = np.load(npz_path)
        K0 = data["K0"]
        D0 = data["D0"]
        K1 = data["K1"]
        D1 = data["D1"]
        R  = data["R"]
        T  = data["T"]
        err_m = float(data.get("stereo_rms", -1.0))  # may not be present
        image_size = tuple(map(int, data["image_size"]))
    else:
        raise ValueError("choice must be 'matlab' or 'python'")

    return K0, D0, K1, D1, R, T, image_size, err_m

def stereo_rectify_maps(K0, D0, K1, D1, R, T, image_size, crop_valid=True):
    # alpha=0 for valid region (like MATLAB OutputView='valid')
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        K0, D0, K1, D1, image_size, R, T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=0)
    map10, map11 = cv2.initUndistortRectifyMap(K0, D0, R1, P1, image_size, cv2.CV_32FC1)
    map20, map21 = cv2.initUndistortRectifyMap(K1, D1, R2, P2, image_size, cv2.CV_32FC1)

    crop = None
    if crop_valid:
        # Compute intersection of valid ROIs
        x1,y1,w1,h1 = roi1
        x2,y2,w2,h2 = roi2
        xA = max(x1,x2); yA = max(y1,y2)
        xB = min(x1+w1, x2+w2); yB = min(y1+h1, y2+h2)
        if xB>xA and yB>yA:
            crop = (xA, yA, xB-xA, yB-yA)

    return (map10, map11, map20, map21), (R1,R2,P1,P2,Q), (roi1,roi2), crop

def build_sgbm(cfg):
    min_d = int(cfg["min_disparity"])  # inclusive
    num_disp = int(cfg["num_disparities"])  # exclusive upper bound

    block = int(cfg["block_size"])
    if block % 2 == 0:
        block += 1
    block = max(block, 3)

    # allow P1/P2 override; otherwise defaults
    P1 = int(cfg.get("P1", 8 * 3 * (block ** 2)))
    P2 = int(cfg.get("P2", 32 * 3 * (block ** 2)))

    mode_map = {
        "SGBM": cv2.STEREO_SGBM_MODE_SGBM,
        "SGBM_3WAY": cv2.STEREO_SGBM_MODE_SGBM_3WAY,
        "HH": cv2.STEREO_SGBM_MODE_HH,
        "HH4": cv2.STEREO_SGBM_MODE_HH4,
    }
    mode = mode_map.get(cfg.get("mode","SGBM_3WAY"), cv2.STEREO_SGBM_MODE_SGBM_3WAY)

    matcher = cv2.StereoSGBM_create(
        minDisparity=min_d,
        numDisparities=num_disp,
        blockSize=block,
        P1=P1, P2=P2,
        disp12MaxDiff=int(cfg["disp12_max_diff"]),
        preFilterCap=int(cfg["pre_filter_cap"]),
        uniquenessRatio=int(cfg["uniqueness_ratio"]),
        speckleWindowSize=int(cfg["speckle_window_size"]),
        speckleRange=int(cfg["speckle_range"]),
        mode=mode,
    )
    return matcher, min_d, num_disp

def colorize_disparity(disp):
    # disp = disp16.astype(np.float32) / 16.0   # already do this in main
    valid = disp > 0
    if np.any(valid):
        dmin = np.percentile(disp[valid], 1.0)
        dmax = np.percentile(disp[valid], 99.0)
        if dmax <= dmin:
            dmax = dmin + 1.0
        disp_norm = (np.clip(disp, dmin, dmax) - dmin) / (dmax - dmin)
    else:
        disp_norm = np.zeros_like(disp)
    disp_u8 = (disp_norm * 255.0).astype(np.uint8)
    return cv2.applyColorMap(disp_u8, cv2.COLORMAP_JET)

def select_points_via_polygon(
    img_bgr,
    points3D,          # shape (H, W, 3)
    colors,            # shape (H, W, 3)  (your cvtColor(..., BGR2RGB) is fine)
    base_mask=None,     # shape (H, W) bool; e.g. disp_float > min_d
    window_name="Draw ROI (L-click to add, Z=undo, C=clear, Enter/Space=finish, Esc=cancel)"
):
    img = img_bgr.copy()
    h, w = img.shape[:2]
    points = []

    if base_mask is None:
        base_mask = np.ones((h, w), dtype=bool)
    else:
        base_mask = base_mask.astype(bool)

    preview_color = (0, 255, 255)
    dot_color = (0, 255, 0)
    line_color = (0, 200, 255)

    def redraw(preview_pt=None):
        vis = img.copy()
        # draw existing vertices
        for p in points:
            cv2.circle(vis, p, 3, dot_color, -1, lineType=cv2.LINE_AA)
        # draw poly lines
        if len(points) > 1:
            cv2.polylines(vis, [np.array(points, dtype=np.int32)], False, line_color, 2, cv2.LINE_AA)
        # draw preview line to mouse
        if preview_pt is not None and len(points) > 0:
            cv2.line(vis, points[-1], preview_pt, preview_color, 1, cv2.LINE_AA)
        cv2.imshow(window_name, vis)
    preview_pt = None

    def on_mouse(event, x, y, flags, param):
        nonlocal preview_pt
        if event == cv2.EVENT_LBUTTONDOWN:
            # clamp to image bounds
            x = int(np.clip(x, 0, w - 1))
            y = int(np.clip(y, 0, h - 1))
            points.append((x, y))
        elif event == cv2.EVENT_MOUSEMOVE:
            preview_pt = (x, y)
        redraw(preview_pt)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, on_mouse)
    redraw()
    # Event loop
    while True:
        key = cv2.waitKey(20) & 0xFF
        if key in (13, 32):  # Enter or Space -> finish
            break
        elif key in (27,):   # Esc -> cancel
            points = []
            break
        elif key in (ord('z'), ord('Z')):  # undo last vertex
            if points:
                points.pop()
            redraw(preview_pt)
        elif key in (ord('c'), ord('C')):  # clear all
            points = []
            redraw(preview_pt)
    cv2.destroyWindow(window_name)

    if len(points) < 3:
        # No valid polygon; return empty selections
        empty = np.empty((0, 3), dtype=points3D.dtype)
        return empty, empty.astype(colors.dtype), np.zeros((h, w), dtype=bool)
    poly = np.array(points, dtype=np.int32)
    roi_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(roi_mask, [poly], 1)
    roi_mask = roi_mask.astype(bool)
    final_mask = base_mask & roi_mask
    sel_points = points3D[final_mask]
    sel_colors = colors[final_mask]

    return sel_points, sel_colors, final_mask

def load_disparity_map(path):
    """Load a colorized disparity map as grayscale float."""
    disp_color = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if disp_color is None:
        raise FileNotFoundError(f"Disparity map not found: {path}")
    # If color, convert to grayscale
    if disp_color.ndim == 3:
        disp_gray = cv2.cvtColor(disp_color, cv2.COLOR_BGR2GRAY)
    else:
        disp_gray = disp_color
    return disp_gray.astype(np.float32)

def load_point_cloud_ply(ply_path):
    """Load a PLY point cloud using Open3D."""
    pcd = o3d.io.read_point_cloud(str(ply_path))
    return pcd

def quat2rotm(q):
    """Convert quaternion [w, x, y, z] to 3x3 rotation matrix."""
    w, x, y, z = q
    return np.array([
        [1-2*(y**2+z**2), 2*(x*y-z*w),   2*(x*z+y*w)],
        [2*(x*y+z*w),     1-2*(x**2+z**2), 2*(y*z-x*w)],
        [2*(x*z-y*w),     2*(y*z+x*w),   1-2*(x**2+y**2)]
    ])

def lla2ned(lla, lla0):
    """
    Convert LLA to NED coordinates relative to lla0.
    lla, lla0: [lat, lon, alt] in degrees/meters
    Returns NED in meters.
    """
    # WGS84
    crs_geodetic = CRS.from_epsg(4979)  # WGS84 3D
    crs_ecef = CRS.from_epsg(4978)
    transformer = Transformer.from_crs(crs_geodetic, crs_ecef, always_xy=True)
    # Convert to ECEF
    x, y, z = transformer.transform(lla[:,1], lla[:,0], lla[:,2])
    x0, y0, z0 = transformer.transform(lla0[1], lla0[0], lla0[2])
    # Compute delta
    dx = x - x0
    dy = y - y0
    dz = z - z0
    # Reference lat/lon in radians
    phi = np.deg2rad(lla0[0])
    lam = np.deg2rad(lla0[1])
    # Rotation matrix ECEF to NED
    R = np.array([
        [-np.sin(phi)*np.cos(lam), -np.sin(phi)*np.sin(lam),  np.cos(phi)],
        [-np.sin(lam),              np.cos(lam),             0],
        [-np.cos(phi)*np.cos(lam), -np.cos(phi)*np.sin(lam), -np.sin(phi)]
    ])
    ned = np.dot(np.stack([dx, dy, dz], axis=1), R.T)
    return ned