from picamera2 import Picamera2

def get_preview_configuration():
    cam = Picamera2()
    config = cam.create_preview_configuration()
    
    # Customizing the configuration
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'BGR888'
    config['controls']['FrameDurationLimits'] = (33333, 33333)  
    config['controls']['ExposureTime'] = 10000 

    return config

def get_still_configuration():
    cam = Picamera2()
    config = cam.create_still_configuration()

    # Customizing the configuration
    config['main']['size'] = (1440, 1080)
    config['main']['format'] = 'BGR888'
    config['controls']['FrameDurationLimits'] = (33333, 33333)  
    config['controls']['ExposureTime'] = 10000 

    return config
