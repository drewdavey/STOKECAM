import cv2
import numpy as np
import os
import yaml
from tkinter import filedialog, Tk

def select_directory(prompt_message):
    """Prompt the user to select a directory."""
    print(prompt_message)
    root = Tk()
    root.withdraw()  # Hide the root window
    directory = filedialog.askdirectory()
    root.destroy()
    return directory

def calibrate_camera(calib_dir):
    """Perform stereo camera calibration."""
    print("Starting calibration...")
    
    # Get paths for calibration images
    left_images_path = os.path.join(calib_dir, "cam1") # THESE ARE FLIPPED
    right_images_path = os.path.join(calib_dir, "cam0") # THESE ARE FLIPPED
    left_images = sorted([os.path.join(left_images_path, f) for f in os.listdir(left_images_path) if f.endswith(".jpg")])
    right_images = sorted([os.path.join(right_images_path, f) for f in os.listdir(right_images_path) if f.endswith(".jpg")])

    # Termination criteria for corner sub-pixel refinement
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Checkerboard configuration (12 columns, 9 rows, 45 mm square size)
    checkerboard_size = (11, 8)
    square_size = 45  # in millimeters
    objp = np.zeros((checkerboard_size[0] * checkerboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:checkerboard_size[0], 0:checkerboard_size[1]].T.reshape(-1, 2)
    objp *= square_size / 1000.0  # Convert square size to meters

    objpoints = []  # 3D points
    imgpoints_left = []  # 2D points for left camera
    imgpoints_right = []  # 2D points for right camera

    for i, (left_img_path, right_img_path) in enumerate(zip(left_images, right_images)):
        img_left = cv2.imread(left_img_path, cv2.IMREAD_GRAYSCALE)
        img_right = cv2.imread(right_img_path, cv2.IMREAD_GRAYSCALE)

        if img_left is None or img_right is None:
            print(f"Image pair {i + 1}: Could not load one or both images.")
            continue

        ret_left, corners_left = cv2.findChessboardCorners(img_left, checkerboard_size, None)
        ret_right, corners_right = cv2.findChessboardCorners(img_right, checkerboard_size, None)

        if ret_left and ret_right:
            print(f"Image pair {i + 1}: Checkerboard corners detected.")
            objpoints.append(objp)
            corners2_left = cv2.cornerSubPix(img_left, corners_left, (11, 11), (-1, -1), criteria)
            corners2_right = cv2.cornerSubPix(img_right, corners_right, (11, 11), (-1, -1), criteria)
            imgpoints_left.append(corners2_left)
            imgpoints_right.append(corners2_right)
        else:
            print(f"Image pair {i + 1}: Checkerboard corners NOT detected.")


    # Calibrate individual cameras
    print("Calibrating left camera...")
    _, mtx_left, dist_left, _, _ = cv2.calibrateCamera(objpoints, imgpoints_left, img_left.shape[::-1], None, None)
    print("Calibrating right camera...")
    _, mtx_right, dist_right, _, _ = cv2.calibrateCamera(objpoints, imgpoints_right, img_right.shape[::-1], None, None)

    # Stereo calibration
    print("Performing stereo calibration...")
    _, _, _, _, _, R, T, _, _ = cv2.stereoCalibrate(
        objpoints, imgpoints_left, imgpoints_right, mtx_left, dist_left, mtx_right, dist_right,
        img_left.shape[::-1], criteria=criteria, flags=cv2.CALIB_FIX_INTRINSIC
    )

    # Save calibration parameters to YAML
    calib_params = {
        'mtx_left': mtx_left.tolist(),
        'dist_left': dist_left.tolist(),
        'mtx_right': mtx_right.tolist(),
        'dist_right': dist_right.tolist(),
        'R': R.tolist(),
        'T': T.tolist()
    }
    yaml_path = os.path.join(calib_dir, "calib_params.yaml")
    with open(yaml_path, 'w') as yaml_file:
        yaml.dump(calib_params, yaml_file)
    print(f"Calibration parameters saved to {yaml_path}")

if __name__ == "__main__":
    calib_dir = select_directory("Select the calibration session directory containing cam0 and cam1.")
    calibrate_camera(calib_dir)
