import os
import cv2
import numpy as np
import torch
import scipy.io as sio
import sys

SUPERGLUE_PATH = "C:/Users/drew/OneDrive - UC San Diego/FSR/stereo_cam/SuperGluePretrainedNetwork"
sys.path.append(SUPERGLUE_PATH)

from models.matching import Matching
from models.utils import frame2tensor

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
    matched_keypointsL = keypointsL[valid_matches]
    matched_keypointsR = keypointsR[matches[valid_matches]]

    return matched_keypointsL, matched_keypointsR

def process_all_images(calib_path, features_path):
    """Process all stereo image pairs and store matches."""
    left_images_path = os.path.join(features_path, "../cam1")
    right_images_path = os.path.join(features_path, "../cam0")

    left_images = sorted([os.path.join(left_images_path, f) for f in os.listdir(left_images_path) if f.endswith(".jpg")])
    right_images = sorted([os.path.join(right_images_path, f) for f in os.listdir(right_images_path) if f.endswith(".jpg")])

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    for imgL_path, imgR_path in zip(left_images, right_images):
        imgL = cv2.imread(imgL_path, cv2.IMREAD_GRAYSCALE)
        imgR = cv2.imread(imgR_path, cv2.IMREAD_GRAYSCALE)

        keypointsL, keypointsR = extract_keypoints_and_match(imgL, imgR, device)

        # Save keypoints in MATLAB format
        mat_filename = os.path.basename(imgL_path).replace('.jpg', '.mat')
        mat_path = os.path.join(features_path, mat_filename)

        sio.savemat(mat_path, {'keypointsL': keypointsL, 'keypointsR': keypointsR})
        print(f"Saved: {mat_path}")

def process_stereo_matching():
    """Main function to process stereo matching using SuperGlue."""
    if len(sys.argv) < 3:
        print("Usage: python superGlue.py <calibration_path> <features_path>")
        sys.exit(1)

    calib_path = sys.argv[1]
    features_path = sys.argv[2]
    
    os.makedirs(features_path, exist_ok=True)
    
    process_all_images(calib_path, features_path)

if __name__ == "__main__":
    process_stereo_matching()
