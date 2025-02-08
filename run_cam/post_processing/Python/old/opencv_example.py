import cv2
import numpy as np
import os
from datetime import datetime

# Function to load stereo images
def load_stereo_images(left_dir, right_dir):
    left_images = []
    right_images = []
    
    for filename in sorted(os.listdir(left_dir)):
        left_img_path = os.path.join(left_dir, filename)
        left_img = cv2.imread(left_img_path, cv2.IMREAD_GRAYSCALE)
        if left_img is not None:
            left_images.append(left_img)
    for filename in sorted(os.listdir(right_dir)):
        right_img_path = os.path.join(right_dir, filename)
        right_img = cv2.imread(right_img_path, cv2.IMREAD_GRAYSCALE)
        if right_img is not None:
            right_images.append(right_img)
    return np.array(left_images), np.array(right_images)

# Compute disparity and 3D points
def compute_3d_points(img_left, img_right, Q):
    # # Convert to grayscale
    # gray_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
    # gray_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)

    # Stereo matching
    # stereo = cv2.StereoBM_create(numDisparities=16, blockSize=15)
    stereo = cv2.StereoSGBM_create(minDisparity=0, numDisparities=16, blockSize=15)
    disparity = stereo.compute(img_left, img_right)

    # Reproject to 3D
    points_3D = cv2.reprojectImageTo3D(disparity, Q)
    return points_3D, disparity

#######################################################
left_dir = 'cam1'
right_dir = 'cam0'
left_images, right_images = load_stereo_images(left_dir, right_dir)
# Define the Q matrix
Q = np.array([
    [1, 0, 0, -766.6506353704514],  # Replace -320 with your cx value
    [0, 1, 0, -498.8387477698295],  # Replace -240 with your cy value
    [0, 0, 0, 1734.357399585855],   # Replace 500 with your focal length f
    [0, 0, 0.008235875262367, 0] # Replace -1/Tx with your baseline Tx and the last element with (cx - cx')/Tx
])

# Output directory for rectified images and disparity maps
output_dir = os.path.join('.', 'Rectified_images')
os.makedirs(output_dir, exist_ok=True)

#######################################################
# Process each pair of images
for i, (img_left, img_right) in enumerate(zip(left_images, right_images)):
    # Process and compute 3D points
    points_3D, disparity = compute_3d_points(img_left, img_right, Q)

    # Visualize disparity
    norm_disparity = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    norm_disparity = np.uint8(norm_disparity)
    cv2.imshow("Disparity", norm_disparity)
    cv2.waitKey(2000)  # Show each for 2 seconds

    # Save normalized disparity map
    disparity_filename = os.path.join(output_dir, f"disparity_{i+1:03}.png")
    cv2.imwrite(disparity_filename, norm_disparity)
cv2.destroyAllWindows()