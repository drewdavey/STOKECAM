import time
import sys
from picamera2 import Picamera2
from gpiozero import Button

# GPIO pin definitions
right_button = Button(18)  # Replace with your GPIO pin number
# left_button = Button(17)  # Replace with your GPIO pin number

def burst_mode(cam0, cam1, log_file, duration, interval):
    with open(log_file, 'a') as log:
        log.write(f"Starting burst mode for {duration} seconds with {interval} second interval.\n")
        cam0.start()
        cam1.start()
        start_time = time.time()
        while right_button.is_pressed:
            cam0.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
            cam1.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
            time.sleep(interval)
        cam0.stop()
        cam1.stop()
        cam0.close()
        cam1.close()
        log.write("Burst mode ended.\n")

def cleanup():
    right_button.close()
    # left_button.close()

if __name__ == "__main__":
    log_file = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    cam0 = Picamera2(0)
    cam1 = Picamera2(1)

    try:
        burst_mode(cam0, cam1, log_file, duration, interval)
    finally:
        cleanup()  # Cleanup GPIO resources
    
