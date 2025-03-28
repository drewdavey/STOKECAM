# Last updated: 2024-10-03
##################################
# This file contains functions defining the camera settings for various shooting modes
##################################
from picamera2 import Picamera2
from libcamera import ColorSpace, Transform

def auto():
    cam = Picamera2()
    config = cam.create_preview_configuration(buffer_count=50)
    config['main']['size'] = (1440, 1080)
    # config['controls']['FrameDurationLimits'] = (0, 100)  
    cam.close()
    return config

def moderate():
    cam = Picamera2()
    config = cam.create_still_configuration()
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888'
    config['controls']['FrameDurationLimits'] = (0, 100)  
    config['controls']['ExposureTime'] = 1000
    cam.close()
    return config

def fast():
    cam = Picamera2()
    config = cam.create_still_configuration()
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888'
    config['controls']['FrameDurationLimits'] = (0, 100)  
    config['controls']['ExposureTime'] = 500
    cam.close()
    return config

def max():
    cam = Picamera2()
    config = cam.create_still_configuration()
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888'
    config['controls']['FrameDurationLimits'] = (0, 100)  
    config['controls']['ExposureTime'] = 125
    cam.close()
    return config

def slow():
    cam = Picamera2()
    config = cam.create_still_configuration()
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888'
    config['controls']['FrameDurationLimits'] = (33333, 33333)  
    config['controls']['ExposureTime'] = 5000 
    cam.close()
    return config

def dark():
    cam = Picamera2()
    config = cam.create_still_configuration()
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888'
    config['controls']['FrameDurationLimits'] = (33333, 33333)  
    config['controls']['ExposureTime'] = 100000 
    cam.close()
    return config

def get_config(mode):
    if mode == 'auto':
        return auto()
    elif mode == 'fast':
        return fast()
    elif mode == 'max':
        return max()
    elif mode == 'slow':
        return slow()
    elif mode == 'moderate':
        return moderate()
    elif mode == 'dark':
        return dark()
    else:
        raise ValueError(f"Invalid mode: {mode}")