import cv2
import numpy as np

# Paths to your images
# imgL_path = '../../../FSR/stereo_cam/DATA/waves/wave_1C/cam1/1_030011508_03417.jpg'
# imgR_path = '../../../FSR/stereo_cam/DATA/waves/wave_1C/cam0/0_030011508_03417.jpg'

imgL_path = '1_030011508_03417.jpg'
imgR_path = '0_030011508_03417.jpg'

# Load images
imgL = cv2.imread(imgL_path)
imgR = cv2.imread(imgR_path)

# Debug information
if imgL is None:
    print(f"Failed to load image at {imgL_path}")
if imgR is None:
    print(f"Failed to load image at {imgR_path}")

# Ensure images are loaded before processing
if imgL is not None and imgR is not None:
    stereo = cv2.StereoBM_create(numDisparities=16, blockSize=15)
    disp = stereo.compute(imgL, imgR).astype(np.float32)
    # Continue with your processing
else:
    print("One or both images are not loaded. Exiting.")