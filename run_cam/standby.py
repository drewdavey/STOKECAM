

from gpiozero import Button
from subprocess import check_call
from signal import pause

def get_stoked():
    check_call(['sudo', 'poweroff'])

stoke_on = Button(17, hold_time=5)
stoke_on.when_held = get_stoked

pause()