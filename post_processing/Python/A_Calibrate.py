"""
STOKECAM Camera Calibration
Drew Davey
Last updated: 2025-09-26

Simple stereo camera calibration using OpenCV with theoretical validation
from Brown (1971) distortion model and camera geometry papers.
"""

import os
import numpy as np
import cv2
import json
from utils import *

# ======================= DEFAULT INPUT PARAMETERS  =====================
INPUTS = {
    "calib_path"      : "C:\\Users\\drew\\OneDrive - UC San Diego\\FSR\\stereo_cam\\DATA\\calibrations\\calib12_SIO_f8",
    "square_size_mm"  : 45.0,     # Size of a checkerboard square (mm)
    "focal_length_mm" : 6.0,      # Lens focal length (mm)
    "pixel_pitch_um"  : 3.45,     # Sony IMX296 pixel pitch (micrometers)
    "baseline_mm"     : 120.0,    # Cam0 -> Cam1 baseline (mm)
    "save_vis"        : True,     # Save visualization images
    "checker_cols"    : 11,       # checkerboard (inner corners)
    "checker_rows"    : 8,        # checkerboard (inner corners)
    "use_sb"          : True      # use cv2 findChessboardCornersSB function
}
# ==========================================================================

def compute_theoretical_focal_length(f_mm, pixel_pitch_um):
    """
    Compute theoretical focal length in pixels from camera specifications.
    Based on pinhole camera model: f_pixels = f_mm / pixel_pitch_mm

    Reference: Hartley & Zisserman "Multiple View Geometry" Chapter 6
    """
    pixel_pitch_mm = pixel_pitch_um / 1000.0
    f_pixels = f_mm / pixel_pitch_mm
    return f_pixels

def compute_brown_distortion(r_norm, k1, k2, k3=0):
    """
    Compute Brown (1971) radial distortion factor.

    Brown's model: r_distorted = r_undistorted * (1 + k1*r^2 + k2*r^4 + k3*r^6)

    Reference: Brown, D.C. (1971). "Close-range camera calibration"
    """
    return 1 + k1 * r_norm**2 + k2 * r_norm**4 + k3 * r_norm**6

def compute_baseline_from_translation(T):
    """
    Compute baseline distance from translation vector.
    For stereo systems, baseline is typically the Euclidean norm of T.

    Reference: Szeliski "Computer Vision: Algorithms and Applications" Chapter 11
    """
    return float(np.linalg.norm(T))

def compute_rotation_angle(R):
    """
    Compute rotation angle from rotation matrix using Rodrigues formula.
    angle = arccos((trace(R) - 1) / 2)

    Reference: Ma, Soatto, Kosecka, Sastry "An Invitation to 3-D Vision" Chapter 2
    """
    trace = np.trace(R)
    # Clamp to avoid numerical issues
    cos_angle = np.clip((trace - 1.0) / 2.0, -1.0, 1.0)
    angle_rad = np.arccos(cos_angle)
    return np.degrees(angle_rad)

def compute_field_of_view(fx, fy, width, height):
    """
    Compute horizontal and vertical field of view from intrinsic parameters.
    FOV = 2 * arctan(sensor_size / (2 * focal_length))

    Reference: Hartley & Zisserman "Multiple View Geometry" Chapter 6
    """
    fov_h = 2 * np.degrees(np.arctan(width / (2 * fx)))
    fov_v = 2 * np.degrees(np.arctan(height / (2 * fy)))
    return fov_h, fov_v

def analyze_distortion_profile(K, D, image_size):
    """
    Analyze radial distortion profile following Brown (1971) model.
    Returns maximum distortion and distortion at image corners.
    """
    width, height = image_size

    # Calculate distortion at image corners
    corners = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype=np.float32)

    cx, cy = K[0, 2], K[1, 2]
    fx = K[0, 0]

    max_distortion = 0
    corner_distortions = []

    for corner in corners:
        x, y = corner
        r = np.sqrt((x - cx)**2 + (y - cy)**2)
        r_norm = r / fx  # Normalize by focal length

        k1, k2 = D[0], D[1]
        k3 = D[4] if len(D) > 4 else 0

        distortion_factor = compute_brown_distortion(r_norm, k1, k2, k3)
        distortion_pct = abs(distortion_factor - 1.0) * 100

        corner_distortions.append(distortion_pct)
        max_distortion = max(max_distortion, distortion_pct)

    return max_distortion, corner_distortions

def main():
    # Get calibration path
    calib_path = INPUTS["calib_path"]
    if calib_path == "":
        calib_path = pick_dir_gui("Select path to calibration session")
    if not calib_path:
        raise SystemExit("No calibration path selected/provided.")
    if not os.path.isdir(os.path.join(calib_path, "cam0")) or not os.path.isdir(os.path.join(calib_path, "cam1")):
        raise SystemExit("Expected cam0/ and cam1/ subfolders inside: " + calib_path)

    save_dir = calib_path

    # Load image pairs
    cam0_files, cam1_files = load_pairs(calib_path)
    print(f"[INFO] Found {len(cam0_files)} image pairs.")

    pattern = INPUTS["checker_cols"], INPUTS["checker_rows"]
    cols, rows = pattern
    print(f"[INFO] Checkerboard pattern: {cols} x {rows} inner corners")

    # Detect corners in all image pairs
    objpoints = []
    imgpoints0 = []
    imgpoints1 = []
    used_idx = []

    objp = build_object_points(pattern, INPUTS["square_size_mm"])
    image_size = None
    n_pairs = len(cam0_files)

    print("[INFO] Detecting checkerboard corners...")
    for i in range(n_pairs):
        im0 = cv2.imread(cam0_files[i], cv2.IMREAD_COLOR)
        im1 = cv2.imread(cam1_files[i], cv2.IMREAD_COLOR)

        if im0 is None or im1 is None:
            continue

        f0, c0, f1, c1, sz = detect_points_on_pair(im0, im1, pattern, use_sb=INPUTS["use_sb"])
        if f0 and f1:
            imgpoints0.append(c0)
            imgpoints1.append(c1)
            objpoints.append(objp.copy())
            used_idx.append(i)
            image_size = sz  # (w,h)
            print(f"  Pair {i+1}: ✓")
        else:
            print(f"  Pair {i+1}: ✗")

    print(f"[INFO] Valid pairs: {len(objpoints)} / {n_pairs}")
    if len(objpoints) < 3:
        raise SystemExit("Not enough valid pairs for stereo calibration. Need >= 3.")

    # ===================== THEORETICAL CALCULATIONS =====================

    # Compute theoretical intrinsics from hardware specs
    K_theory = theoretical_intrinsics_from_spec(
        image_size, INPUTS["focal_length_mm"], INPUTS["pixel_pitch_um"]
    )

    # Theoretical focal length calculation (paper equation)
    f_theory = compute_theoretical_focal_length(INPUTS["focal_length_mm"], INPUTS["pixel_pitch_um"])

    # Theoretical field of view
    fov_h_theory, fov_v_theory = compute_field_of_view(
        K_theory[0,0], K_theory[1,1], image_size[0], image_size[1]
    )

    print("\n=== THEORETICAL PARAMETERS (from hardware specs) ===")
    print(f"Focal length: {INPUTS['focal_length_mm']} mm")
    print(f"Pixel pitch: {INPUTS['pixel_pitch_um']} μm")
    print(f"Computed f_pixels = f_mm / pixel_pitch_mm = {f_theory:.2f} pixels")
    print(f"Theoretical K matrix:")
    print(K_theory)
    print(f"Field of view: {fov_h_theory:.1f}° H × {fov_v_theory:.1f}° V")
    print(f"Baseline: {INPUTS['baseline_mm']} mm")

    # ===================== OPENCV CALIBRATION =====================

    # Initial guesses
    K0_init = K_theory.copy()
    K1_init = K_theory.copy()
    D0 = np.zeros((5,1), dtype=np.float64)
    D1 = np.zeros((5,1), dtype=np.float64)

    # Individual camera calibrations
    print("\n=== INDIVIDUAL CAMERA CALIBRATION ===")
    rms0, K0, D0, rvecs0, tvecs0 = cv2.calibrateCamera(
        objpoints, imgpoints0, image_size, K0_init, D0,
        flags=cv2.CALIB_USE_INTRINSIC_GUESS
    )
    rms1, K1, D1, rvecs1, tvecs1 = cv2.calibrateCamera(
        objpoints, imgpoints1, image_size, K1_init, D1,
        flags=cv2.CALIB_USE_INTRINSIC_GUESS
    )
    print(f"Camera 0 RMS error: {rms0:.4f} pixels")
    print(f"Camera 1 RMS error: {rms1:.4f} pixels")

    # Stereo calibration
    print("\n=== STEREO CALIBRATION ===")
    flags = cv2.CALIB_USE_INTRINSIC_GUESS
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 1e-10)
    stereo_rms, K0s, D0s, K1s, D1s, R, T, E, F = cv2.stereoCalibrate(
        objpoints, imgpoints0, imgpoints1, K0, D0, K1, D1, image_size,
        criteria=criteria, flags=flags
    )
    print(f"Stereo RMS error: {stereo_rms:.6f} pixels")

    # Stereo rectification
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        K0s, D0s, K1s, D1s, image_size, R, T,
        flags=cv2.CALIB_ZERO_DISPARITY, alpha=0
    )

    # ===================== THEORETICAL ANALYSIS =====================

    # Compute derived parameters using paper equations
    baseline_measured = compute_baseline_from_translation(T)
    rotation_angle = compute_rotation_angle(R)

    # Field of view from measured parameters
    fov_h_measured0, fov_v_measured0 = compute_field_of_view(
        K0s[0,0], K0s[1,1], image_size[0], image_size[1]
    )
    fov_h_measured1, fov_v_measured1 = compute_field_of_view(
        K1s[0,0], K1s[1,1], image_size[0], image_size[1]
    )

    # Distortion analysis using Brown model
    max_dist0, corner_dist0 = analyze_distortion_profile(K0s, D0s, image_size)
    max_dist1, corner_dist1 = analyze_distortion_profile(K1s, D1s, image_size)

    print("\n=== MEASURED vs THEORETICAL COMPARISON ===")
    print(f"Baseline: {baseline_measured:.4f} mm (theory: {INPUTS['baseline_mm']:.1f} mm, Δ: {baseline_measured - INPUTS['baseline_mm']:+.4f} mm)")
    print(f"Rotation angle: {rotation_angle:.6f}° (theory: 0°)")

    def pct_error(measured, theoretical):
        return 100 * (measured - theoretical) / theoretical if theoretical != 0 else 0

    print(f"\nCamera 0 intrinsics vs theory:")
    print(f"  fx: {K0s[0,0]:.2f} (theory: {f_theory:.2f}, error: {pct_error(K0s[0,0], f_theory):+.2f}%)")
    print(f"  fy: {K0s[1,1]:.2f} (theory: {f_theory:.2f}, error: {pct_error(K0s[1,1], f_theory):+.2f}%)")
    print(f"  FOV: {fov_h_measured0:.1f}°×{fov_v_measured0:.1f}° (theory: {fov_h_theory:.1f}°×{fov_v_theory:.1f}°)")

    print(f"\nCamera 1 intrinsics vs theory:")
    print(f"  fx: {K1s[0,0]:.2f} (theory: {f_theory:.2f}, error: {pct_error(K1s[0,0], f_theory):+.2f}%)")
    print(f"  fy: {K1s[1,1]:.2f} (theory: {f_theory:.2f}, error: {pct_error(K1s[1,1], f_theory):+.2f}%)")
    print(f"  FOV: {fov_h_measured1:.1f}°×{fov_v_measured1:.1f}° (theory: {fov_h_theory:.1f}°×{fov_v_theory:.1f}°)")

    print(f"\nDistortion analysis (Brown 1971 model):")
    print(f"  Camera 0: k1={D0s[0]:.6f}, k2={D0s[1]:.6f}, max distortion: {max_dist0:.3f}%")
    print(f"  Camera 1: k1={D1s[0]:.6f}, k2={D1s[1]:.6f}, max distortion: {max_dist1:.3f}%")

    # ===================== SAVE RESULTS =====================

    # Save calibration data
    out_npz = os.path.join(save_dir, "calib.npz")
    np.savez(
        out_npz,
        image_size=np.array(image_size),
        pattern_cols=cols, pattern_rows=rows,
        square_size_mm=INPUTS["square_size_mm"],
        K0=K0s, D0=D0s, K1=K1s, D1=D1s, R=R, T=T, E=E, F=F,
        R1=R1, R2=R2, P1=P1, P2=P2, Q=Q,
        K_theory=K_theory,
        R_theory=np.eye(3),
        T_theory=np.array([[INPUTS["baseline_mm"]], [0.0], [0.0]]),
        rms_stereo=stereo_rms, rms_cam0=rms0, rms_cam1=rms1,
        used_indices=np.array(used_idx, dtype=int),
        focal_length_mm=INPUTS["focal_length_mm"],
        pixel_pitch_um=INPUTS["pixel_pitch_um"],
        baseline_mm=INPUTS["baseline_mm"]
    )
    print(f"\n[INFO] Saved: {out_npz}")

    # ===================== GENERATE COMPARISON REPORT =====================

    # Load MATLAB calibration if available
    has_matlab = os.path.exists(os.path.join(save_dir, "calib.json"))

    report_lines = []
    report_lines.append("STOKECAM Camera Calibration Report")
    report_lines.append("=" * 50)
    report_lines.append(f"Calibration folder: {save_dir}")
    report_lines.append(f"Image pairs: {len(objpoints)}/{n_pairs} usable")
    report_lines.append(f"Pattern: {cols}×{rows} corners, {INPUTS['square_size_mm']}mm squares")
    report_lines.append("")

    # Theoretical section
    report_lines.append("THEORETICAL PARAMETERS")
    report_lines.append("-" * 30)
    report_lines.append(f"Hardware specs:")
    report_lines.append(f"  Focal length: {INPUTS['focal_length_mm']} mm")
    report_lines.append(f"  Pixel pitch: {INPUTS['pixel_pitch_um']} μm")
    report_lines.append(f"  Baseline: {INPUTS['baseline_mm']} mm")
    report_lines.append(f"Computed from pinhole model (f_pixels = f_mm / pixel_pitch_mm):")
    report_lines.append(f"  f_pixels: {f_theory:.2f}")
    report_lines.append(f"  Field of view: {fov_h_theory:.1f}° × {fov_v_theory:.1f}°")
    report_lines.append("")

    # Python results
    report_lines.append("PYTHON OPENCV CALIBRATION")
    report_lines.append("-" * 30)
    report_lines.append(f"Camera 0:")
    report_lines.append(f"  fx={K0s[0,0]:.4f} (Δ: {pct_error(K0s[0,0], f_theory):+.2f}%)")
    report_lines.append(f"  fy={K0s[1,1]:.4f} (Δ: {pct_error(K0s[1,1], f_theory):+.2f}%)")
    report_lines.append(f"  cx={K0s[0,2]:.4f}, cy={K0s[1,2]:.4f}")
    report_lines.append(f"  k1={D0s[0]:.6f}, k2={D0s[1]:.6f}")
    report_lines.append(f"  RMS error: {rms0:.4f} pixels")
    report_lines.append(f"  Max distortion: {max_dist0:.3f}%")
    report_lines.append("")
    report_lines.append(f"Camera 1:")
    report_lines.append(f"  fx={K1s[0,0]:.4f} (Δ: {pct_error(K1s[0,0], f_theory):+.2f}%)")
    report_lines.append(f"  fy={K1s[1,1]:.4f} (Δ: {pct_error(K1s[1,1], f_theory):+.2f}%)")
    report_lines.append(f"  cx={K1s[0,2]:.4f}, cy={K1s[1,2]:.4f}")
    report_lines.append(f"  k1={D1s[0]:.6f}, k2={D1s[1]:.6f}")
    report_lines.append(f"  RMS error: {rms1:.4f} pixels")
    report_lines.append(f"  Max distortion: {max_dist1:.3f}%")
    report_lines.append("")
    report_lines.append(f"Stereo geometry:")
    report_lines.append(f"  Baseline: {baseline_measured:.4f} mm (Δ: {baseline_measured - INPUTS['baseline_mm']:+.4f} mm)")
    report_lines.append(f"  Rotation: {rotation_angle:.6f}°")
    report_lines.append(f"  Stereo RMS: {stereo_rms:.6f} pixels")
    report_lines.append("")

    # MATLAB comparison if available
    if has_matlab:
        try:
            K0_m, D0_m, K1_m, D1_m, R_m, T_m, img_sz_m, err_m = load_calibration(save_dir, choice="matlab")
            baseline_matlab = compute_baseline_from_translation(T_m)
            rotation_matlab = compute_rotation_angle(R_m)

            report_lines.append("MATLAB CALIBRATION COMPARISON")
            report_lines.append("-" * 30)
            report_lines.append(f"Baseline: Python={baseline_measured:.4f} mm, MATLAB={baseline_matlab:.4f} mm")
            report_lines.append(f"          Difference: {baseline_measured - baseline_matlab:+.6f} mm")
            report_lines.append(f"Rotation: Python={rotation_angle:.6f}°, MATLAB={rotation_matlab:.6f}°")
            report_lines.append(f"          Difference: {rotation_angle - rotation_matlab:+.6f}°")
            report_lines.append(f"RMS Error: Python={stereo_rms:.6f}, MATLAB={err_m:.6f}")
            report_lines.append(f"           Difference: {stereo_rms - err_m:+.6f} pixels")
            report_lines.append("")
        except Exception as e:
            report_lines.append("MATLAB calibration file found but could not be loaded.")
            report_lines.append("")
    else:
        report_lines.append("MATLAB CALIBRATION")
        report_lines.append("-" * 30)
        report_lines.append("No MATLAB calibration file (calib.json) found.")
        report_lines.append("Run MATLAB calibration first for comparison.")
        report_lines.append("")

    # Theory validation
    report_lines.append("THEORETICAL VALIDATION")
    report_lines.append("-" * 30)
    report_lines.append("Calibration follows:")
    report_lines.append("• Brown (1971) radial distortion model")
    report_lines.append("• Pinhole camera projection model")
    report_lines.append("• Zhang (2000) calibration methodology")
    report_lines.append("")

    # Quality assessment
    if stereo_rms < 0.5:
        quality = "Excellent"
    elif stereo_rms < 1.0:
        quality = "Good"
    elif stereo_rms < 2.0:
        quality = "Fair"
    else:
        quality = "Poor"

    report_lines.append(f"Quality Assessment: {quality}")
    report_lines.append(f"Stereo RMS < 0.5 pixels: Excellent")
    report_lines.append(f"Stereo RMS < 1.0 pixels: Good")
    report_lines.append(f"Stereo RMS < 2.0 pixels: Fair")

    # Save report
    report_path = os.path.join(save_dir, "calibration_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"[INFO] Report saved: {report_path}")

    # ===================== VISUALIZATIONS =====================

    if INPUTS["save_vis"]:
        os.makedirs(os.path.join(save_dir, "vis"), exist_ok=True)

        # Save corner detection for first few pairs
        for k, idx in enumerate(used_idx[:5]):
            im0 = cv2.imread(cam0_files[idx], cv2.IMREAD_COLOR)
            im1 = cv2.imread(cam1_files[idx], cv2.IMREAD_COLOR)

            im0_draw = im0.copy()
            im1_draw = im1.copy()
            cv2.drawChessboardCorners(im0_draw, pattern, imgpoints0[k], True)
            cv2.drawChessboardCorners(im1_draw, pattern, imgpoints1[k], True)

            cv2.imwrite(os.path.join(save_dir, "vis", f"corners_cam0_{idx:04d}.png"), im0_draw)
            cv2.imwrite(os.path.join(save_dir, "vis", f"corners_cam1_{idx:04d}.png"), im1_draw)

        # Save rectified example
        if used_idx:
            idx0 = used_idx[0]
            im0 = cv2.imread(cam0_files[idx0], cv2.IMREAD_COLOR)
            im1 = cv2.imread(cam1_files[idx0], cv2.IMREAD_COLOR)

            map10, map11 = cv2.initUndistortRectifyMap(K0s, D0s, R1, P1, image_size, cv2.CV_32FC1)
            map20, map21 = cv2.initUndistortRectifyMap(K1s, D1s, R2, P2, image_size, cv2.CV_32FC1)

            rect0 = cv2.remap(im0, map10, map11, cv2.INTER_LINEAR)
            rect1 = cv2.remap(im1, map20, map21, cv2.INTER_LINEAR)

            # Create side-by-side with epipolar lines
            canvas = np.hstack([rect0, np.full((rect0.shape[0], 8, 3), 255, np.uint8), rect1])
            for y in range(0, canvas.shape[0], 40):
                cv2.line(canvas, (0, y), (canvas.shape[1]-1, y), (0, 255, 0), 1)

            cv2.imwrite(os.path.join(save_dir, "vis", f"rectified_{idx0:04d}.png"), canvas)

        print(f"[INFO] Visualizations saved to: {os.path.join(save_dir, 'vis')}")

    print(f"\n[SUCCESS] Calibration completed!")
    print(f"Results: {save_dir}")

if __name__ == "__main__":
    main()