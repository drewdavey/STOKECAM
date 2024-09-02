from gpiozero import LED
from time import sleep

red = LED(26)
green = LED(12)
yellow = LED(16)

while True:
    red.on()
    green.on()
    yellow.on()
    sleep(1)
    red.off()
    green.off()
    yellow.off()
    sleep(1)