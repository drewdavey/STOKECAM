

from gpiozero import Button
from subprocess import check_call
from signal import pause

def shutdown():
    check_call(['sudo', 'poweroff'])

stoke_on = Button(17, hold_time=5)
stoke_on.when_held = stoke_on

pause()