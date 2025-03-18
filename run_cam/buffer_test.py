import time
import numpy as np
import threading
import queue
from collections import deque
from datetime import datetime, timezone
from picamera2 import Picamera2

# Initialize Picamera2
picam2 = Picamera2()
config = picam2.create_still_configuration(buffer_count=4)  # Buffer up to 4 frames
picam2.configure(config)
picam2.start()

# Circular buffer and queue setup
buffer_size = 10  # Store last 10 images in memory
image_buffer = deque(maxlen=buffer_size)
timestamp_buffer = deque(maxlen=buffer_size)
write_queue = queue.Queue()

def capture_burst(num_images=10):
    """Capture images quickly into RAM."""
    for _ in range(num_images):
        timestamp = time.monotonic_ns()
        img = picam2.capture_array("main")  # Capture to RAM
        image_buffer.append(img)
        timestamp_buffer.append(timestamp)

def write_images_to_sd():
    """Background process to write images to SD card."""
    while True:
        try:
            img, timestamp = write_queue.get(timeout=2)  # Get from queue
            filename = f"/home/pi/capture_{timestamp}.npy"
            np.save(filename, img)  # Save as .npy to preserve raw data
            print(f"Saved {filename}")
        except queue.Empty:
            break

def process_and_store():
    """Queue images for writing after burst."""
    for i in range(len(image_buffer)):
        write_queue.put((image_buffer[i], timestamp_buffer[i]))
    thread = threading.Thread(target=write_images_to_sd)
    thread.start()

# Run test capture
if __name__ == "__main__":
    capture_burst(20)  # Capture 20 images quickly into RAM
    process_and_store()  # Write to SD card in the background
