import os
import cv2
import sys
import numpy as np
import torch
import yaml
import scipy.io as sio
import matplotlib.pyplot as plt
SUPERGLUE_PATH = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/SuperGluePretrainedNetwork"
sys.path.append(SUPERGLUE_PATH)
from tkinter import filedialog, Tk
from models.matching import Matching
from models.utils import frame2tensor

def select_directory(prompt_message):
    """Prompt the user to select a directory."""
    print(prompt_message)
    root = Tk()
    root.withdraw()
    directory = filedialog.askdirectory()
    root.destroy()
    return directory

def load_calibration_params(calib_dir):
    """Load calibration parameters from YAML file."""
    yaml_path = os.path.join(calib_dir, "calib_params.yaml")
    with open(yaml_path, 'r') as yaml_file:
        return yaml.safe_load(yaml_file)

def extract_keypoints_and_match(imgL, imgR, device):
    """Extract keypoints using SuperPoint and match using SuperGlue."""
    matching = Matching({'superpoint': {}, 'superglue': {}}).eval().to(device)
    tensorL = frame2tensor(imgL, device)
    tensorR = frame2tensor(imgR, device)
    pred = matching({'image0': tensorL, 'image1': tensorR})
    keypointsL = pred['keypoints0'][0].cpu().numpy()
    keypointsR = pred['keypoints1'][0].cpu().numpy()
    matches = pred['matches0'][0].cpu().numpy()
    valid_matches = matches > -1
    return keypointsL[valid_matches], keypointsR[matches[valid_matches]]

def rectify_and_compute_disparity(session_path, calib_params):
    """Rectify images, compute disparity map, and reproject to 3D."""
    features_path = os.path.join(session_path, "features")
    ptclouds_path = os.path.join(session_path, "ptClouds")
    os.makedirs(features_path, exist_ok=True)
    os.makedirs(ptclouds_path, exist_ok=True)
    
    left_images_path = os.path.join(session_path, "cam1")
    right_images_path = os.path.join(session_path, "cam0")
    left_images = sorted([os.path.join(left_images_path, f) for f in os.listdir(left_images_path) if f.endswith(".jpg")])
    right_images = sorted([os.path.join(right_images_path, f) for f in os.listdir(right_images_path) if f.endswith(".jpg")])
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    mtx_left = np.array(calib_params['mtx_left'])
    dist_left = np.array(calib_params['dist_left'])
    mtx_right = np.array(calib_params['mtx_right'])
    dist_right = np.array(calib_params['dist_right'])
    R = np.array(calib_params['R'])
    T = np.array(calib_params['T'])
    
    img_sample = cv2.imread(left_images[0])
    image_size = img_sample.shape[1::-1]
    R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(mtx_left, dist_left, mtx_right, dist_right, image_size, R, T, alpha=0)
    map_left1, map_left2 = cv2.initUndistortRectifyMap(mtx_left, dist_left, R1, P1, image_size, cv2.CV_16SC2)
    map_right1, map_right2 = cv2.initUndistortRectifyMap(mtx_right, dist_right, R2, P2, image_size, cv2.CV_16SC2)
    
    for imgL_path, imgR_path in zip(left_images, right_images):
        imgL = cv2.imread(imgL_path, cv2.IMREAD_GRAYSCALE)
        imgR = cv2.imread(imgR_path, cv2.IMREAD_GRAYSCALE)
        keypointsL, keypointsR = extract_keypoints_and_match(imgL, imgR, device)
        rectifiedL = cv2.remap(imgL, map_left1, map_left2, cv2.INTER_LINEAR)
        rectifiedR = cv2.remap(imgR, map_right1, map_right2, cv2.INTER_LINEAR)
        stereo = cv2.StereoSGBM_create(minDisparity=0, numDisparities=64, blockSize=15)
        disparity_map = stereo.compute(rectifiedL, rectifiedR).astype(np.float32) / 16.0
        points_3D = cv2.reprojectImageTo3D(disparity_map, Q)
        mat_filename = os.path.basename(imgL_path).replace('.jpg', '.mat')
        sio.savemat(os.path.join(ptclouds_path, mat_filename), {'points3D': points_3D})
        plt.imshow(disparity_map, cmap='jet')
        plt.colorbar()
        plt.title('Disparity Map')
        plt.show()
    print("Processing complete. Point clouds saved to", ptclouds_path)

if __name__ == "__main__":
    session_path = select_directory("Select the session directory containing cam0 and cam1.")
    calib_path = select_directory("Select the calibration session directory containing calib_params.yaml.")
    calib_params = load_calibration_params(calib_path)
    rectify_and_compute_disparity(session_path, calib_params)

