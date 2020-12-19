"""
# Problem
sometimes the after rebotting the E173 will be mounted as 
- /dev/ttyUSB0 /dev/ttyUSB1  /dev/ttyUSB2 or 
- /dev/ttyUSB1 /dev/ttyUSB2  /dev/ttyUSB3 

but only the first one should be configured in ~/etc/gammu-smsdrc~.
therefore this script will get the first ttyUSB* device. ("/dev/ttyUSB0" or "/dev/ttyUSB0")
and then generate /etc/gammu-smsdrc

"""
from os import write
from src import utils

def generate_smsdrc(device:str):
    """
    device: /dev/ttyUSB0
    """
    with open("./src/gammu-smsdrc.template") as f:
        template = f.read()
        # print(template)
        result = template.format(device=device)

    return result

def create_to_etc_smsdrc(dest="/etc/gammu-smsdrc"):
    device = utils.get_first_tty_usb()
    if not device:
        print("Not /dev/ttyUSB* found. Exit!")
        return
    content = generate_smsdrc(device)

    if not content:
        print("Something wrong with content of config file.Please check 'gammu-smsdrc.template'. Exit!")
        return

    with open(dest, "w") as f:
        f.write(content)

    print(f"'{dest}' for [{device}] was created succesfully")