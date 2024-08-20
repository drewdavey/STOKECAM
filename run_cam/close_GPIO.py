import gpiozero.pins.rpigpio

def close(self): pass
gpiozero.pins.rpigpio.RPiGPIOPin.close = close

gpiozero.LED(..., pin_factory=gpiozero.pins.rpigpio.RPiGPIOFactory())