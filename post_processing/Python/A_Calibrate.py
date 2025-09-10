"""
STOKECAM Post-Processing
Drew Davey
Last updated: 2025-08-15

Performs stereo camera calibration using checkerboard images.
"""
# =================== PACKAGES ===============================
import os
import numpy as np
import cv2
from utils import *

# ======================= DEFAULT INPUT PARAMETERS  =====================
INPUTS = {
    "calib_path"      : "C:\\Users\\drew\\OneDrive - UC San Diego\\FSR\\stereo_cam\\DATA\\calibrations\\calib8_SIO",       # Leave empty to get a GUI folder picker
    "square_size_mm"  : 45.0,     # Size of a checkerboard square (mm)
    "focal_length_mm" : 6.0,      # Lens focal length (mm)
    "pixel_pitch_um"  : 3.45,   # Sony IMX296 pixel pitch (micrometers)
    "baseline_mm"     : 120.0,    # Cam0 -> Cam1 baseline (mm)
    "save_vis"        : True,    # Save visualization images
    "checker_cols"    : 11,       # checkerboard (inner corners)
    "checker_rows"    : 8,        # checkerboard (inner corners)
    "use_sb"          : True      # use cv2 findChessboardCornersSB function
}
# ==========================================================================

def main():
    # GUI select
    calib_path = INPUTS["calib_path"]
    if calib_path == "":
        calib_path = pick_dir_gui("Select path to calibration session")
    if not calib_path:
        raise SystemExit("No calibration path selected/provided.")
    if not os.path.isdir(os.path.join(calib_path, "cam0")) or not os.path.isdir(os.path.join(calib_path, "cam1")):
        raise SystemExit("Expected cam0/ and cam1/ subfolders inside: " + calib_path)

    save_dir = calib_path  # write outputs in the calib folder

    cam0_files, cam1_files = load_pairs(calib_path)
    print(f"[INFO] Found {len(cam0_files)} image pairs.")

    use_sb = INPUTS["use_sb"]

    pattern = INPUTS["checker_cols"], INPUTS["checker_rows"]
    cols, rows = pattern
    print(f"[INFO] Checkerboard inner-corner pattern: {cols} x {rows}")

    # Collect detections
    objpoints = []  # 3D points in world (mm)
    imgpoints0 = [] # 2D points in cam0
    imgpoints1 = [] # 2D points in cam1
    used_idx = []

    objp = build_object_points(pattern, INPUTS["square_size_mm"])
    image_size = None
    n_pairs = len(cam0_files)

    for i in range(n_pairs):
        im0 = cv2.imread(cam0_files[i], cv2.IMREAD_COLOR)
        im1 = cv2.imread(cam1_files[i], cv2.IMREAD_COLOR)
        # im0 = brighten(im0, value=50)
        # im1 = brighten(im1, value=50)
        if im0 is None or im1 is None:
            continue
        f0, c0, f1, c1, sz = detect_points_on_pair(im0, im1, pattern, use_sb=use_sb)
        if f0 and f1:
            imgpoints0.append(c0)
            imgpoints1.append(c1)
            objpoints.append(objp.copy())
            used_idx.append(i)
            image_size = sz  # (w,h)
    print(f"[INFO] Usable stereo pairs with detected corners: {len(objpoints)} / {n_pairs}")
    if len(objpoints) < 3:
        raise SystemExit("Not enough valid pairs for stereo calibration. Need >= 3.")

    # Theoretical intrinsics (same for both cams)
    K_theory = theoretical_intrinsics_from_spec(
        image_size, INPUTS["focal_length_mm"], INPUTS["pixel_pitch_um"]
    )
    print("[INFO] Theoretical intrinsics (from focal length & pixel pitch):")
    print(K_theory)

    # Initial guesses for OpenCV
    K0_init = K_theory.copy()
    K1_init = K_theory.copy()
    D0 = np.zeros((5,1), dtype=np.float64)
    D1 = np.zeros((5,1), dtype=np.float64)

    # Calibrate each camera individually
    rms0, K0, D0, rvecs0, tvecs0 = cv2.calibrateCamera(
        objpoints, imgpoints0, image_size, K0_init, D0,
        flags=cv2.CALIB_USE_INTRINSIC_GUESS
    )
    rms1, K1, D1, rvecs1, tvecs1 = cv2.calibrateCamera(
        objpoints, imgpoints1, image_size, K1_init, D1,
        flags=cv2.CALIB_USE_INTRINSIC_GUESS
    )
    print(f"[INFO] Mono RMS reprojection error: cam0={rms0:.4f}, cam1={rms1:.4f}")

    # Stereo calibration 
    flags = cv2.CALIB_USE_INTRINSIC_GUESS
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 1e-10)
    stereo_rms, K0s, D0s, K1s, D1s, R, T, E, F = cv2.stereoCalibrate(
        objpoints, imgpoints0, imgpoints1, K0, D0, K1, D1, image_size,
        criteria=criteria, flags=flags
    )
    print(f"[INFO] Stereo RMS reprojection error: {stereo_rms:.6f}")

    # Stereo rectification
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        K0s, D0s, K1s, D1s, image_size, R, T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=0)

    # ----------------------- Theoretical extrinsics -----------------------
    # Camera-1 (cam1) pose w.r.t. camera-0 (cam0).
    # set cam1 translated +baseline on X in cam0 frame.
    R_theory = np.eye(3, dtype=np.float64)
    T_theory = np.array([[INPUTS["baseline_mm"]], [0.0], [0.0]], dtype=np.float64)  # mm

    # ----------------------- Optional visualizations ----------------------
    if INPUTS["save_vis"]:
        os.makedirs(os.path.join(save_dir, "vis"), exist_ok=True)
        # Draw detected corners for first few used pairs
        for k, idx in enumerate(used_idx[:5]):
            im0 = cv2.imread(cam0_files[idx], cv2.IMREAD_COLOR)
            im1 = cv2.imread(cam1_files[idx], cv2.IMREAD_COLOR)
            im0_draw = im0.copy()
            im1_draw = im1.copy()
            cv2.drawChessboardCorners(im0_draw, pattern, imgpoints0[k], True)
            cv2.drawChessboardCorners(im1_draw, pattern, imgpoints1[k], True)
            out0 = os.path.join(save_dir, "vis", f"corners_cam0_{idx:04d}.png")
            out1 = os.path.join(save_dir, "vis", f"corners_cam1_{idx:04d}.png")
            cv2.imwrite(out0, im0_draw)
            cv2.imwrite(out1, im1_draw)

        # Save a rectified preview of the first pair used
        idx0 = used_idx[0]
        im0 = cv2.imread(cam0_files[idx0], cv2.IMREAD_COLOR)
        im1 = cv2.imread(cam1_files[idx0], cv2.IMREAD_COLOR)
        map10, map11 = cv2.initUndistortRectifyMap(K0s, D0s, R1, P1, image_size, cv2.CV_32FC1)
        map20, map21 = cv2.initUndistortRectifyMap(K1s, D1s, R2, P2, image_size, cv2.CV_32FC1)
        rect0 = cv2.remap(im0, map10, map11, cv2.INTER_LINEAR)
        rect1 = cv2.remap(im1, map20, map21, cv2.INTER_LINEAR)
        # stack and draw horizontal guide lines
        hgap = 8
        canvas = np.hstack([rect0, np.full((rect0.shape[0], hgap, 3), 255, np.uint8), rect1])
        for y in range(0, canvas.shape[0], 40):
            cv2.line(canvas, (0, y), (canvas.shape[1]-1, y), (0, 255, 0), 1, cv2.LINE_AA)
        out_rect = os.path.join(save_dir, "vis", f"rectified_pair_{idx0:04d}.png")
        cv2.imwrite(out_rect, canvas)
        print(f"[INFO] Saved visualizations to {os.path.join(save_dir, 'vis')}")

    # ----------------------- Save calibration .npz ----------------------
    out_npz = os.path.join(save_dir, "calib.npz")
    np.savez(
        out_npz,
        image_size=np.array(image_size),
        pattern_cols=cols, pattern_rows=rows,
        square_size_mm=INPUTS["square_size_mm"],
        K0=K0s, D0=D0s, K1=K1s, D1=D1s, R=R, T=T, E=E, F=F,
        R1=R1, R2=R2, P1=P1, P2=P2, Q=Q,
        K_theory=K_theory, R_theory=R_theory, T_theory=T_theory,
        rms_stereo=stereo_rms, rms_cam0=rms0, rms_cam1=rms1,
        used_indices=np.array(used_idx, dtype=int)
    )
    print(f"[INFO] Wrote: {out_npz}")

    # ======================= MATLAB vs PYTHON vs THEORY CHECK =======================
    def _fx_fy_cx_cy_s(K):
        return float(K[0, 0]), float(K[1, 1]), float(K[0, 2]), float(K[1, 2]), float(K[0, 1])

    def _baseline_mm(T_vec):
        # T is [tx, ty, tz] or column; unit detection: treat as meters if it's clearly small
        Tv = np.array(T_vec).reshape(-1)
        b = float(np.linalg.norm(Tv))
        # Heuristic: if baseline looks like meters (< 2.0), convert to mm
        return b * 1000.0 if b < 2.0 else b

    def _rot_angle_deg(Rm):
        # Use your utils function if present, else compute here
        try:
            return float(rotation_angle_from_R(Rm))
        except NameError:
            # angle = arccos((trace(R)-1)/2) in degrees, numerically safe
            tr = np.trace(Rm)
            val = max(min((tr - 1.0) * 0.5, 1.0), -1.0)
            return float(np.degrees(np.arccos(val)))

    def _pct(a, b):
        return 0.0 if b == 0 else 100.0 * (a - b) / b

    # Load MATLAB and Python (saved) calibs using your helper
    has_matlab = os.path.exists(os.path.join(save_dir, "calib.json"))
    report_lines = []
    report_lines.append("STOKECAM Calibration Comparison")
    report_lines.append(f"Calib folder: {save_dir}")
    report_lines.append(f"Image size (w,h): {image_size[0]} x {image_size[1]}")
    report_lines.append("")
    report_lines.append(f"Found {len(cam0_files)} image pairs.")
    report_lines.append(f"Checkerboard inner-corner pattern: {cols} x {rows}")
    report_lines.append(f"Usable stereo pairs with detected corners: {len(objpoints)} / {n_pairs}")
    report_lines.append("")

    # Theory
    fx_t, fy_t, cx_t, cy_t, s_t = _fx_fy_cx_cy_s(K_theory)
    b_theory = float(np.linalg.norm(T_theory))
    report_lines.append("=== THEORETICAL ===")
    report_lines.append(f"fx={fx_t:.6f}, fy={fy_t:.6f}, cx={cx_t:.6f}, cy={cy_t:.6f}, skew={s_t:.6f}")
    report_lines.append(f"Baseline={b_theory:.6f} mm, Rotation angle=0.000000 deg")
    report_lines.append("")

    # Python 
    fx0_p, fy0_p, cx0_p, cy0_p, s0_p = _fx_fy_cx_cy_s(K0s)
    fx1_p, fy1_p, cx1_p, cy1_p, s1_p = _fx_fy_cx_cy_s(K1s)
    b_python = _baseline_mm(T)
    ang_python = _rot_angle_deg(R)

    report_lines.append("=== PYTHON (OpenCV stereoCalibrate) ===")
    report_lines.append(f"[cam0] fx={fx0_p:.6f} (Δ% vs th={_pct(fx0_p,fx_t):+.3f}%), "
                        f"fy={fy0_p:.6f} (Δ%={_pct(fy0_p,fy_t):+.3f}%), "
                        f"cx={cx0_p:.6f} (Δ%={_pct(cx0_p,cx_t):+.3f}%), "
                        f"cy={cy0_p:.6f} (Δ%={_pct(cy0_p,cy_t):+.3f}%), "
                        f"skew={s0_p:.6f}")
    report_lines.append(f"[cam1] fx={fx1_p:.6f} (Δ% vs th={_pct(fx1_p,fx_t):+.3f}%), "
                        f"fy={fy1_p:.6f} (Δ%={_pct(fy1_p,fy_t):+.3f}%), "
                        f"cx={cx1_p:.6f} (Δ%={_pct(cx1_p,cx_t):+.3f}%), "
                        f"cy={cy1_p:.6f} (Δ%={_pct(cy1_p,cy_t):+.3f}%), "
                        f"skew={s1_p:.6f}")
    report_lines.append(f"[extr] Baseline={b_python:.6f} mm (Δ vs th={b_python - b_theory:+.6f} mm), "
                        f"Rotation angle={ang_python:.9f} deg")
    report_lines.append(f"Mono RMS reprojection error: cam0={rms0:.4f}, cam1={rms1:.4f}")
    report_lines.append(f"Stereo RMS reprojection error: {stereo_rms:.9f}")
    report_lines.append("")

    # MATLAB
    if has_matlab:
        K0_m, D0_m, K1_m, D1_m, R_m, T_m, img_sz_m, err_m = load_calibration(save_dir, choice="matlab")
        fx0_m, fy0_m, cx0_m, cy0_m, s0_m = _fx_fy_cx_cy_s(K0_m)
        fx1_m, fy1_m, cx1_m, cy1_m, s1_m = _fx_fy_cx_cy_s(K1_m)

        b_matlab = _baseline_mm(T_m)
        ang_matlab = _rot_angle_deg(R_m)

        report_lines.append("=== MATLAB (calib.json) ===")
        report_lines.append(f"[cam0] fx={fx0_m:.6f} (Δ% vs th={_pct(fx0_m,fx_t):+.3f}%), "
                            f"fy={fy0_m:.6f} (Δ%={_pct(fy0_m,fy_t):+.3f}%), "
                            f"cx={cx0_m:.6f} (Δ%={_pct(cx0_m,cx_t):+.3f}%), "
                            f"cy={cy0_m:.6f} (Δ%={_pct(cy0_m,cy_t):+.3f}%), "
                            f"skew={s0_m:.6f}")
        report_lines.append(f"[cam1] fx={fx1_m:.6f} (Δ% vs th={_pct(fx1_m,fx_t):+.3f}%), "
                            f"fy={fy1_m:.6f} (Δ%={_pct(fy1_m,fy_t):+.3f}%), "
                            f"cx={cx1_m:.6f} (Δ%={_pct(cx1_m,cx_t):+.3f}%), "
                            f"cy={cy1_m:.6f} (Δ%={_pct(cy1_m,cy_t):+.3f}%), "
                            f"skew={s1_m:.6f}")
        report_lines.append(f"[extr] Baseline={b_matlab:.6f} mm (Δ vs th={b_matlab - b_theory:+.6f} mm), "
                            f"Rotation angle={ang_matlab:.9f} deg")
        report_lines.append(f"Stereo RMS reprojection error: {err_m:.9f}")
        report_lines.append("")

        # Direct PY vs MAT diffs
        report_lines.append("=== PYTHON - MATLAB deltas ===")
        report_lines.append(f"[cam0] Δfx={fx0_p - fx0_m:+.6f}, Δfy={fy0_p - fy0_m:+.6f}, "
                            f"Δcx={cx0_p - cx0_m:+.6f}, Δcy={cy0_p - cy0_m:+.6f}, "
                            f"Δskew={s0_p - s0_m:+.6f}")
        report_lines.append(f"[cam1] Δfx={fx1_p - fx1_m:+.6f}, Δfy={fy1_p - fy1_m:+.6f}, "
                            f"Δcx={cx1_p - cx1_m:+.6f}, Δcy={cy1_p - cy1_m:+.6f}, "
                            f"Δskew={s1_p - s1_m:+.6f}")
        report_lines.append(f"[extr] ΔBaseline={b_python - b_matlab:+.6f} mm, "
                            f"ΔRotation angle={ang_python - ang_matlab:+.9f} deg")
        report_lines.append(f"[stereo] ΔRMS error={stereo_rms - err_m:+.9f}")
        report_lines.append("")
    else:
        report_lines.append("MATLAB calib.json not found in this folder; skipped MATLAB comparison.")
        report_lines.append("")

    # Write text report
    txt_path = os.path.join(save_dir, "calib_comparison.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"[INFO] Wrote comparison report: {txt_path}")


if __name__ == "__main__":
    main()
