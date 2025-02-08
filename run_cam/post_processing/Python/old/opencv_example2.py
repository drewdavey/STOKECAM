import cv2
import numpy as np
import os
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
    left_images_path = os.path.join(calib_dir, "cam1")
    right_images_path = os.path.join(calib_dir, "cam0")
    left_images = sorted([os.path.join(left_images_path, f) for f in os.listdir(left_images_path) if f.endswith(".jpg")])
    right_images = sorted([os.path.join(right_images_path, f) for f in os.listdir(right_images_path) if f.endswith(".jpg")])

    # Termination criteria for corner sub-pixel refinement
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Checkerboard size (inner corners, 9 rows and 12 columns)
    checkerboard_size = (12, 9)  # Number of internal corners along rows and columns

    # Prepare 3D points for the checkerboard (square size is 45 mm)
    square_size = 45  # millimeters
    objp = np.zeros((checkerboard_size[0] * checkerboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:checkerboard_size[0], 0:checkerboard_size[1]].T.reshape(-1, 2)
    objp *= square_size / 1000.0  # Convert square size to meters (OpenCV expects meters)

    # Arrays to store object points and image points
    objpoints = []  # 3D points
    imgpoints_left = []  # 2D points for left camera
    imgpoints_right = []  # 2D points for right camera

    for left_img_path, right_img_path in zip(left_images, right_images):
        img_left = cv2.imread(left_img_path, cv2.IMREAD_GRAYSCALE)
        img_right = cv2.imread(right_img_path, cv2.IMREAD_GRAYSCALE)
        ret_left, corners_left = cv2.findChessboardCorners(img_left, checkerboard_size, None)
        ret_right, corners_right = cv2.findChessboardCorners(img_right, checkerboard_size, None)

        if ret_left and ret_right:
            objpoints.append(objp)
            corners2_left = cv2.cornerSubPix(img_left, corners_left, (11, 11), (-1, -1), criteria)
            corners2_right = cv2.cornerSubPix(img_right, corners_right, (11, 11), (-1, -1), criteria)
            imgpoints_left.append(corners2_left)
            imgpoints_right.append(corners2_right)

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

    return mtx_left, dist_left, mtx_right, dist_right, R, T


def rectify_and_compute_disparity(recon_dir, mtx_left, dist_left, mtx_right, dist_right, R, T):
    """Rectify stereo images and compute disparity."""
    print("Starting rectification and disparity computation...")
    left_images_path = os.path.join(recon_dir, "cam0")
    right_images_path = os.path.join(recon_dir, "cam1")
    output_dir = os.path.join(recon_dir, "Rectified_Images2")
    os.makedirs(output_dir, exist_ok=True)

    # Get image size and compute rectification transforms
    img = cv2.imread(sorted(os.listdir(left_images_path))[0])
    image_size = img.shape[1::-1]
    R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(
        mtx_left, dist_left, mtx_right, dist_right, image_size, R, T, alpha=0
    )

    map_left1, map_left2 = cv2.initUndistortRectifyMap(mtx_left, dist_left, R1, P1, image_size, cv2.CV_16SC2)
    map_right1, map_right2 = cv2.initUndistortRectifyMap(mtx_right, dist_right, R2, P2, image_size, cv2.CV_16SC2)

    # Rectify images and compute disparity
    left_images = sorted([os.path.join(left_images_path, f) for f in os.listdir(left_images_path) if f.endswith(".jpg")])
    right_images = sorted([os.path.join(right_images_path, f) for f in os.listdir(right_images_path) if f.endswith(".jpg")])

    for idx, (left_img_path, right_img_path) in enumerate(zip(left_images, right_images)):
        img_left = cv2.imread(left_img_path)
        img_right = cv2.imread(right_img_path)

        rectified_left = cv2.remap(img_left, map_left1, map_left2, cv2.INTER_LINEAR)
        rectified_right = cv2.remap(img_right, map_right1, map_right2, cv2.INTER_LINEAR)

        stereo = cv2.StereoBM_create(numDisparities=16, blockSize=15)
        disparity = stereo.compute(cv2.cvtColor(rectified_left, cv2.COLOR_BGR2GRAY), 
                                    cv2.cvtColor(rectified_right, cv2.COLOR_BGR2GRAY))

        norm_disparity = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        norm_disparity = np.uint8(norm_disparity)

        # Save results
        cv2.imwrite(os.path.join(output_dir, f"rectified_left_{idx+1:03}.png"), rectified_left)
        cv2.imwrite(os.path.join(output_dir, f"rectified_right_{idx+1:03}.png"), rectified_right)
        cv2.imwrite(os.path.join(output_dir, f"disparity_{idx+1:03}.png"), norm_disparity)

    print("Disparity computation complete.")

if __name__ == "__main__":
    # Calibration step
    calib_dir = select_directory("Select the calibration session directory containing cam0 and cam1.")
    mtx_left, dist_left, mtx_right, dist_right, R, T = calibrate_camera(calib_dir)

    # Reconstruction step
    recon_dir = select_directory("Select the reconstruction session directory containing cam0 and cam1.")
    rectify_and_compute_disparity(recon_dir, mtx_left, dist_left, mtx_right, dist_right, R, T)
