import time
import sys
from picamera2 import Picamera2

def burst_mode(camera, log_file, duration, interval):
    with open(log_file, 'a') as log:
        log.write(f"Starting burst mode for {duration} seconds with {interval} second interval.\n")
        camera.start_preview()
        start_time = time.time()
        while time.time() - start_time < duration:
            camera.capture_file(f'../../DATA/{time.strftime("%Y%m%d_%H%M%S")}.jpg')
            time.sleep(interval)
        camera.stop_preview()
        log.write("Burst mode ended.\n")

if __name__ == "__main__":
    log_file = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    camera = Picamera2()
    burst_mode(camera, log_file, duration, interval)
