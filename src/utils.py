import subprocess
def get_first_tty_usb():
    cmd = r"ls /dev/ttyUSB*"
    try:
        lsres = subprocess.check_output(cmd, shell=True).decode().split('\n')
        print(lsres)
        first_ttyUSB = lsres[0]
    except subprocess.CalledProcessError as e:
        first_ttyUSB = None
    return first_ttyUSB