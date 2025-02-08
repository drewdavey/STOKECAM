import cv2
import numpy as np
import os
from datetime import datetime
from picamera2 import Picamera2

# Load intrinsic parameters and stereo calibration results
def load_camera_params():
    # Replace these with paths to your calibration files
    calib_data = np.load('stereo_calibration_data.npz')
    camera_matrix_left = calib_data['camera_matrix_left']
    camera_matrix_right = calib_data['camera_matrix_right']
    dist_coeffs_left = calib_data['dist_coeffs_left']
    dist_coeffs_right = calib_data['dist_coeffs_right']
    R = calib_data['R']
    T = calib_data['T']
    return camera_matrix_left, dist_coeffs_left, camera_matrix_right, dist_coeffs_right, R, T

# Configure cameras
def initialize_cameras():
    cam0 = Picamera2(0)
    cam1 = Picamera2(1)
    cam0.configure(cam0.create_preview_configuration())
    cam1.configure(cam1.create_preview_configuration())
    cam0.start()
    cam1.start()
    return cam0, cam1

# Capture stereo images
def capture_stereo_images(cam0, cam1, save_path):
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S%f")
    img_left_path = os.path.join(save_path, f"left_{time_str}.jpg")
    img_right_path = os.path.join(save_path, f"right_{time_str}.jpg")
    cam0.capture_file(img_left_path)
    cam1.capture_file(img_right_path)
    return img_left_path, img_right_path

# Compute disparity and 3D points
def compute_3d_points(img_left, img_right, Q):
    # Convert to grayscale
    gray_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)

    # Stereo matching
    stereo = cv2.StereoBM_create(numDisparities=16, blockSize=15)
    disparity = stereo.compute(gray_left, gray_right)

    # Reproject to 3D
    points_3D = cv2.reprojectImageTo3D(disparity, Q)
    return points_3D, disparity

# Main script
def main():
    # Paths
    save_path = "captured_stereo_images"
    os.makedirs(save_path, exist_ok=True)

    # Load stereo calibration data
    cam_mtx_left, dist_left, cam_mtx_right, dist_right, R, T = load_camera_params()

    # Compute rectification and Q matrix
    img_size = (1920, 1080)  # Replace with actual resolution
    R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(cam_mtx_left, dist_left, cam_mtx_right, dist_right, img_size, R, T)

    # Initialize cameras
    cam0, cam1 = initialize_cameras()

    try:
        while True:
            # Capture images
            left_img_path, right_img_path = capture_stereo_images(cam0, cam1, save_path)
            img_left = cv2.imread(left_img_path)
            img_right = cv2.imread(right_img_path)

            # Process and compute 3D points
            points_3D, disparity = compute_3d_points(img_left, img_right, Q)

            # Visualize disparity
            norm_disparity = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
            norm_disparity = np.uint8(norm_disparity)
            cv2.imshow("Disparity", norm_disparity)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cam0.stop()
        cam1.stop()
        cam0.close()
        cam1.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
