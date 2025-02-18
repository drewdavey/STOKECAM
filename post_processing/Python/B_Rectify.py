import cv2
import numpy as np
import os
import yaml
import scipy.io
from tkinter import filedialog, Tk

start_location = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/DATA"

def select_directory(prompt_message):
    """Prompt the user to select a directory."""
    print(prompt_message)
    root = Tk()
    root.withdraw()
    directory = filedialog.askdirectory(initialdir=start_location)
    root.destroy()
    return directory

def load_calibration_params(calib_dir):
    """Load calibration parameters from YAML file."""
    yaml_path = os.path.join(calib_dir, "calib_params.yaml")
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"No calibration file found in {calib_dir}")
    with open(yaml_path, 'r') as yaml_file:
        calib_params = yaml.safe_load(yaml_file)
    return calib_params

def tune_disparity_params(left_img_path, right_img_path):
    """Interactive disparity tuning with trackbars."""
    imgL = cv2.imread(left_img_path)
    imgR = cv2.imread(right_img_path)
    
    def update(val):
        blockSize = max(5, cv2.getTrackbarPos('BlockSize', 'Stereo Tuner') | 1)  # Must be odd and at least 5
        numDisparities = max(16, cv2.getTrackbarPos('NumDisparities', 'Stereo Tuner') - cv2.getTrackbarPos('NumDisparities', 'Stereo Tuner') % 16)  # Multiple of 16
        uniquenessRatio = cv2.getTrackbarPos('UniquenessRatio', 'Stereo Tuner')
        speckleWindowSize = cv2.getTrackbarPos('SpeckleWindowSize', 'Stereo Tuner')
        speckleRange = cv2.getTrackbarPos('SpeckleRange', 'Stereo Tuner')

        stereo = cv2.StereoSGBM_create(
            minDisparity=0, numDisparities=numDisparities, blockSize=blockSize,
            P1=8 * 3 * blockSize**2, P2=32 * 3 * blockSize**2, disp12MaxDiff=1,
            uniquenessRatio=uniquenessRatio, speckleWindowSize=speckleWindowSize,
            speckleRange=speckleRange, preFilterCap=63, mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY)
        
        disparity = stereo.compute(cv2.cvtColor(imgL, cv2.COLOR_BGR2GRAY), cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY))
        norm_disparity = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        color_disparity = cv2.applyColorMap(np.uint8(norm_disparity), cv2.COLORMAP_JET)
        cv2.imshow('Disparity Map', color_disparity)
    
    cv2.namedWindow('Stereo Tuner')
    cv2.createTrackbar('BlockSize', 'Stereo Tuner', 9, 50, update)
    cv2.createTrackbar('NumDisparities', 'Stereo Tuner', 64, 128, update)
    cv2.createTrackbar('UniquenessRatio', 'Stereo Tuner', 15, 50, update)
    cv2.createTrackbar('SpeckleWindowSize', 'Stereo Tuner', 50, 200, update)
    cv2.createTrackbar('SpeckleRange', 'Stereo Tuner', 2, 10, update)
    
    update(0)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def rectify_and_reconstruct(recon_dir, calib_params):
    """Perform full stereo rectification and 3D reconstruction."""
    left_images_path = os.path.join(recon_dir, "cam1")
    right_images_path = os.path.join(recon_dir, "cam0")
    rectified_images_dir = os.path.join(recon_dir, "Rectified_Images2")
    mats_dir = os.path.join(recon_dir, "mats2")
    os.makedirs(rectified_images_dir, exist_ok=True)
    os.makedirs(mats_dir, exist_ok=True)
    
    left_img_path = sorted(os.listdir(left_images_path))[0]
    right_img_path = sorted(os.listdir(right_images_path))[0]
    tune_disparity_params(os.path.join(left_images_path, left_img_path), os.path.join(right_images_path, right_img_path))

    mtx_left = np.array(calib_params['mtx_left'])
    dist_left = np.array(calib_params['dist_left'])
    mtx_right = np.array(calib_params['mtx_right'])
    dist_right = np.array(calib_params['dist_right'])
    R = np.array(calib_params['R'])
    T = np.array(calib_params['T'])

    sample_img = cv2.imread(os.path.join(left_images_path, left_img_path))
    image_size = sample_img.shape[1::-1]

    R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(mtx_left, dist_left, mtx_right, dist_right, image_size, R, T, alpha=1)
    map_left1, map_left2 = cv2.initUndistortRectifyMap(mtx_left, dist_left, R1, P1, image_size, cv2.CV_16SC2)
    map_right1, map_right2 = cv2.initUndistortRectifyMap(mtx_right, dist_right, R2, P2, image_size, cv2.CV_16SC2)

    left_images = sorted([os.path.join(left_images_path, f) for f in os.listdir(left_images_path) if f.endswith(".jpg")])
    right_images = sorted([os.path.join(right_images_path, f) for f in os.listdir(right_images_path) if f.endswith(".jpg")])

    stereo = cv2.StereoSGBM_create(minDisparity=0, numDisparities=64, blockSize=9,
                                   P1=8 * 3 * 9**2, P2=32 * 3 * 9**2, disp12MaxDiff=1,
                                   uniquenessRatio=15, speckleWindowSize=50, speckleRange=2,
                                   preFilterCap=63, mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY)

    for idx, (left_img_path, right_img_path) in enumerate(zip(left_images, right_images)):
        imgL = cv2.imread(left_img_path)
        imgR = cv2.imread(right_img_path)
        rectified_left = cv2.remap(imgL, map_left1, map_left2, cv2.INTER_LINEAR)
        rectified_right = cv2.remap(imgR, map_right1, map_right2, cv2.INTER_LINEAR)
        cv2.imwrite(os.path.join(rectified_images_dir, f"rectified_left_{idx+1:03}.png"), rectified_left)
        cv2.imwrite(os.path.join(rectified_images_dir, f"rectified_right_{idx+1:03}.png"), rectified_right)

        disparity = stereo.compute(cv2.cvtColor(rectified_left, cv2.COLOR_BGR2GRAY), cv2.cvtColor(rectified_right, cv2.COLOR_BGR2GRAY))
        points_3D = cv2.reprojectImageTo3D(disparity, Q)
        scipy.io.savemat(os.path.join(mats_dir, f"points3D_{idx+1:03}.mat"), {"points3D": points_3D})


if __name__ == "__main__":
    calib_dir = select_directory("Select the calibration session directory containing the calibration file.")
    calib_params = load_calibration_params(calib_dir)

    recon_dir = select_directory("Select the reconstruction session directory containing cam0 and cam1.")
    rectify_and_reconstruct(recon_dir, calib_params)
