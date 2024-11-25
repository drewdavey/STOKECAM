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

def load_calibration_params(calib_dir):
    """Load calibration parameters from YAML file."""
    yaml_path = os.path.join(calib_dir, "calib_params.yaml")
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"No calibration file found in {calib_dir}")
    with open(yaml_path, 'r') as yaml_file:
        calib_params = yaml.safe_load(yaml_file)
    return calib_params

def rectify_and_compute_disparity(recon_dir, calib_params):
    """Rectify stereo images and compute disparity."""
    print("Starting rectification and disparity computation...")
    left_images_path = os.path.join(recon_dir, "cam1")
    right_images_path = os.path.join(recon_dir, "cam0")
    output_dir = os.path.join(recon_dir, "Rectified_Images2")
    os.makedirs(output_dir, exist_ok=True)

    mtx_left = np.array(calib_params['mtx_left'])
    dist_left = np.array(calib_params['dist_left'])
    mtx_right = np.array(calib_params['mtx_right'])
    dist_right = np.array(calib_params['dist_right'])
    R = np.array(calib_params['R'])
    T = np.array(calib_params['T'])

    img = cv2.imread(sorted(os.listdir(left_images_path))[0])
    image_size = img.shape[1::-1]
    R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(
        mtx_left, dist_left, mtx_right, dist_right, image_size, R, T, alpha=0
    )

    map_left1, map_left2 = cv2.initUndistortRectifyMap(mtx_left, dist_left, R1, P1, image_size, cv2.CV_16SC2)
    map_right1, map_right2 = cv2.initUndistortRectifyMap(mtx_right, dist_right, R2, P2, image_size, cv2.CV_16SC2)

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

        cv2.imwrite(os.path.join(output_dir, f"rectified_left_{idx+1:03}.png"), rectified_left)
        cv2.imwrite(os.path.join(output_dir, f"rectified_right_{idx+1:03}.png"), rectified_right)
        cv2.imwrite(os.path.join(output_dir, f"disparity_{idx+1:03}.png"), norm_disparity)

    print("Disparity computation complete.")

if __name__ == "__main__":
    calib_dir = select_directory("Select the calibration session directory containing the calibration file.")
    calib_params = load_calibration_params(calib_dir)

    recon_dir = select_directory("Select the reconstruction session directory containing cam0 and cam1.")
    rectify_and_compute_disparity(recon_dir, calib_params)
