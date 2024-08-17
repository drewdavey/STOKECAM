

from gpiozero import Button
from subprocess import check_call
from signal import pause

def start_stoke():
    # check_call(['sudo', 'poweroff'])
    print('start stoke.py')

def stop_stoke():
    print('stop stoke.py')


button0 = Button(17, hold_time=5)
button0.when_held = start_stoke

button1 = Button(23, hold_time=5)
stoke_on.when_held = stop_stoke

pause()