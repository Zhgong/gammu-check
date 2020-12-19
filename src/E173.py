# todo: if use lsusb found e173 but no ttyUSB was found.
# execute: sudo usb_modeswitch -I -W -c /etc/usb_modeswitch.d/E173.conf to show ttyUSB again
import subprocess
import time
from src import utils
import re

class E173_Dongle:
    def __init__(self) -> None:
        pass
    def get_huwei_usb(self):
        # get huawei usbid with lsusb
        # --> 'Bus 001 Device 005: ID 12d1:1436 Huawei Technologies Co., Ltd. E173 3G Modem (modem-mode)'
        cmd = 'lsusb'
        lsres = subprocess.check_output(cmd, shell=True).decode().split('\n')

        for r in lsres:
            if 'Huawei' in r:
                return r

    def usb_modeswitch_config(self):
        # run usb_modeswitch after running,
        # the /dev/ttyUSB0 should appear
        cmd = r'sudo usb_modeswitch -I -W -c /etc/usb_modeswitch.d/E173.conf'
        print('Executing command: %s' % cmd)

        lsres = subprocess.check_output(cmd, shell=True).decode().split('\n')
        time.sleep(1)
        device = utils.get_first_tty_usb()
        if device:
            print("Device: %s exists! Success." % device)
            return True
        else:
            print("No 'ttyUSB*' Device under /dev! Command failed.")
            return False

    def reset_usb(self):    
        # execute command 'sudo usb_modeswitch -v 0x12d1 -p1436 --reset-usb'
        usb = self.get_huwei_usb()
        id1, id2 = self.get_usb_id(usb)
        cmd = 'sudo usb_modeswitch -v 0x%s -p%s --reset-usb' % (id1, id2)
        print("Resetting USB with command: %s" % cmd)
        res = subprocess.check_output(cmd, shell=True)

    def get_usb_id(self,usb:str):
        # input 'Bus 001 Device 005: ID 12d1:1436 Huawei Technologies Co., Ltd. E173 3G Modem (modem-mode)'
        # output: '12d1', '1436'
        idRegex = re.compile(r'ID\s(.*)?:(.*)?\sHuawei')
        match = idRegex.search(usb)
        return match.groups()

if __name__ == "__main__":
    e173 = E173_Dongle()
    print(e173.get_huwei_usb())