
import os
import cv2
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
import matplotlib.pyplot as plt

# Function to load stereo images
def load_stereo_images(left_dir, right_dir):
    left_images = []
    right_images = []
    
    for filename in sorted(os.listdir(left_dir)):
        left_img_path = os.path.join(left_dir, filename)
        right_img_path = os.path.join(right_dir, filename)
        
        left_img = cv2.imread(left_img_path, cv2.IMREAD_GRAYSCALE)
        right_img = cv2.imread(right_img_path, cv2.IMREAD_GRAYSCALE)

        if left_img is not None and right_img is not None:
            left_images.append(left_img)
            right_images.append(right_img)

    return np.array(left_images), np.array(right_images)

# Function to preprocess images
def preprocess_images(left_images, right_images):
    left_images = left_images / 255.0  # Normalize
    right_images = right_images / 255.0
    return left_images, right_images

# Define a simple CNN model for stereo matching
def create_stereo_matching_cnn(input_shape):
    model = Sequential()
    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=input_shape))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
    model.add(Flatten())
    model.add(Dense(1, activation='linear'))  # Output disparity map
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# Function to compute the disparity map
def compute_disparity_map(left_image, right_image, model):
    left_image = np.expand_dims(left_image, axis=(0, -1))
    right_image = np.expand_dims(right_image, axis=(0, -1))
    disparity = model.predict([left_image, right_image])
    return disparity[0]


# Paths to your images
# left_dir = '../../../FSR/stereo_cam/DATA/waves/wave_1C/cam1/'
# right_dir = '../../../FSR/stereo_cam/DATA/waves/wave_1C/cam0/'

left_dir = 'cam1'
right_dir = 'cam0'

left_images, right_images = load_stereo_images(left_dir, right_dir)

# Preprocess images
left_images, right_images = preprocess_images(left_images, right_images)

# Create and train CNN model (for simplicity, using first image shape)
input_shape = (left_images.shape[1], left_images.shape[2], 1)
model = create_stereo_matching_cnn(input_shape)

# For demonstration, let's assume using dummy data for training
# Train the model with some dummy data or your own dataset
model.fit(left_images, right_images, epochs=10, batch_size=8)

# Compute disparity map for the first image pair
disparity_map = compute_disparity_map(left_images[0], right_images[0], model)

# Display the disparity map
plt.imshow(disparity_map, cmap='gray')
plt.title('Disparity Map')
plt.show()