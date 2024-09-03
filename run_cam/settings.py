# Generate configuration settings

from picamera2 import Picamera2
from libcamera import ColorSpace, Transform
from utils import *

def auto():
    cam = Picamera2()
    config = cam.create_preview_configuration()
    
    # Customizing the configuration
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888' 
    config['controls']['FrameDurationLimits'] = (33333, 33333)  
    config['controls']['ExposureTime'] = 10000 
    
    cam.close()
    return config

def still():
    cam = Picamera2()
    config = cam.create_still_configuration()

    # Customizing the configuration
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'RGB888'
    config['controls']['FrameDurationLimits'] = (33333, 33333)  
    config['controls']['ExposureTime'] = 10000 

    cam.close()
    return config

def get_config():
    fdir, fname = setup_logging()
    inputs = read_inputs_yaml(fname)
    mode = inputs['shooting_mode']
    if mode == 'auto':
        return auto()
    elif mode == 'still':
        return still()
    else:
        raise ValueError(f"Invalid mode: {mode}")


