# Generate configuration settings

from picamera2 import Picamera2
from libcamera import ColorSpace, Transform

def get_preview_configuration():
    cam = Picamera2()
    config = cam.create_preview_configuration()
    
    # Customizing the configuration
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888' 
    config['controls']['FrameDurationLimits'] = (33333, 33333)  
    config['controls']['ExposureTime'] = 10000 
    
    cam.close()
    return config

def get_still_configuration():
    cam = Picamera2()
    config = cam.create_still_configuration()

    # Customizing the configuration
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888'
    config['controls']['FrameDurationLimits'] = (33333, 33333)  
    config['controls']['ExposureTime'] = 10000 

    cam.close()
    return config

# config = get_still_configuration()
# print(config)