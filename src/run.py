#!/usr/bin/python3

__author__ = 'gong'


import time
import logging
import subprocess
import re
import os
import sys
import shutil
import click
import config
from src import utils
from src import create_gammu_smsdrc
from src.E173_Dongle import E173_Dongle

global LOGFILE
global DEVICE

LOGFILE = config.LOGFILE  # '/var/log/gammu-smsd'
DEVICE = None  # first of '/dev/ttyUSB0' '/dev/ttyUSB1'
DEVICE_OLD = None

CYCLE_TIME = 10

# monitor logfile to check if gammu is dead
LOGFILE_TIMEOUT = 30

restart_count = 0

e173 = E173_Dongle()

@click.command()
@click.option('--interval', '-i', default=2, help='number of greetings')
def run(interval):
    CYCLE_TIME = interval
    print('set CYCLE_TIME: %d ' % interval)
    main()


def logging_config(loggingfile):
    # configure logging, log data will be store with the same name.log under the same folder.

    # path, file = os.path.split(sys.argv[0])
    # name, ext = os.path.splitext(file)
    # name += '.log'
    # loggingfile = os.path.join(path, name)

    FORMAT = '%(asctime)-15s %(name)s %(levelname)s: %(message)s'
    # logging.basicConfig(level=logging.INFO,filename=loggingfile, format=FORMAT)
    if loggingfile:
        logging.basicConfig(level=logging.INFO,
                            filename=loggingfile, format=FORMAT)
        print('Logging file for is: %s' % loggingfile)
    else:
        logging.basicConfig(level=logging.INFO, format=FORMAT)


# compare last time with current time, if the file has not been changed in "seconds" seconds, return true
def file_modified_timeout(file, seconds):
    mftime = os.path.getmtime(file)
    now = time.time()

    logging.debug('File: %s last modified at: %s.' % (file, mftime))
    logging.debug('Current time: %s' % now)
    logging.debug('Time deviation is: %s' % (abs(now - mftime)))

    return abs(now-mftime) > seconds

# check if the gammu is dead


def is_gammu_dead():
    return file_modified_timeout(LOGFILE, LOGFILE_TIMEOUT)


def get_pid(name):
    # get the pid of a process
    cmd = r'pgrep %s' % name
    # getting the pid of gammu-smsd
    try:
        pid = int(subprocess.check_output(cmd, shell=True))
        print("Process: %s is running with pid: %s" % (name, pid))
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            print("Process: %s is not running" % name)
            return 0
        else:
            print(
                "Error while executing %s with return value: %d" % (cmd, e.returncode))
            return -1
    except ValueError as e:
        print(
            "More than one matched process found. Error with: %s." % e)
        return -1
    except Exception as e:
        print("unkonw Error with: %s." % e)
        return -1
    return pid

# stop gammu process


def stop_gammu():
    return subprocess.check_output("sudo /etc/init.d/gammu-smsd stop", shell=True)


# def get_huwei_usb():
#     # get huawei usbid with lsusb
#     # --> 'Bus 001 Device 005: ID 12d1:1436 Huawei Technologies Co., Ltd. E173 3G Modem (modem-mode)'
#     cmd = 'lsusb'
#     lsres = subprocess.check_output(cmd, shell=True).decode().split('\n')

#     for r in lsres:
#         if 'Huawei' in r:
#             return r


# def get_usb_id(usb):
#     # input 'Bus 001 Device 005: ID 12d1:1436 Huawei Technologies Co., Ltd. E173 3G Modem (modem-mode)'
#     # output: '12d1', '1436'
#     idRegex = re.compile(r'ID\s(.*)?:(.*)?\sHuawei')
#     match = idRegex.search(usb)
#     return match.groups()

# reset Huawei usb UTMS disk


# def reset_huawei():

#     # execute command 'sudo usb_modeswitch -v 0x12d1 -p1436 --reset-usb'
#     usb = e173.get_huwei_usb()
#     id1, id2 = get_usb_id(usb)
#     cmd = 'sudo usb_modeswitch -v 0x%s -p%s --reset-usb' % (id1, id2)
#     print("Resetting USB with command: %s" % cmd)
#     res = subprocess.check_output(cmd, shell=True)


# start gammu process again
def start_gammu():
    return subprocess.check_output("sudo /etc/init.d/gammu-smsd start", shell=True)


def gammu_restart_daemon():
    global restart_count
    # check if gammu is dead
    if is_gammu_dead():
        restart_count += 1
        logging.error("---- Restart Count: %d ----" % restart_count)
        logging.error("gammu-smsd is dead, start restarting process")
        # stop gammu
        print("Stopping gammu ...")
        stop_gammu()
        # reset usb
        # print("Resetting Huawei E173 ...")
        # reset_huawei()
        e173.reset_usb()

        # check log file size
        check_logfile_size(10)

        # start gammu
        print("Starting gammu ...")
        start_gammu()
        print("Process finished.")


def check_logfile_size(MAX_SIZE=20):
    # check gammu-smsd file size
    # if size > 50mb then move (rename) it as archieve
    # and touch a new file

    # get file size as mb
    log_size = os.path.getsize(LOGFILE) >> 20

    if log_size > MAX_SIZE:
        # rename as archieve
        archieve = LOGFILE + '.archieve'
        shutil.move(LOGFILE, archieve)

        # touch new file
        with open(LOGFILE, 'a'):
            pass
        return True


def usb_modeswitch():
    # run usb_modeswitch after running,
    # the /dev/ttyUSB0 should appear
    cmd = r'sudo usb_modeswitch -I -W -c /etc/usb_modeswitch.d/E173.conf'
    print('Executing command: %s' % cmd)

    lsres = subprocess.check_output(cmd, shell=True).decode().split('\n')
    time.sleep(1)
    utils.get_first_tty_usb()
    if DEVICE:
        print("Device: %s exists! Success." % DEVICE)
        return True
    else:
        print("No 'ttyUSB*' Device under /dev! Command failed.")
        return False



def main():
    global DEVICE
    cycle_time = 10
    print("Starting gammu-check Daemon.")
    Error = 0
    while True:
        # todo: if error happened too many, increase cycle time
        time.sleep(cycle_time)

        try:
            # if usb stick not exists, sleep 60 seconds
            DEVICE = utils.get_first_tty_usb()
            if not DEVICE:
                print(
                    "Device: %s not exists! Sleep 60 seconds." % DEVICE)
                cycle_time = 60

            # if not os.path.exists(DEVICE):
            #     # force to run usb_modeswitch to get /dev/ttyUSB0
            #     logging.debug('Device : %s not detected. Trying usb_modeswtich' % DEVICE)
            #     usb_modeswitch()
            #     Error += 1
            else:

                check_change_of_device()

                gammu_restart_daemon()
                Error = 0
                cycle_time = CYCLE_TIME
        except Exception as e:
            print('Error: %s' % e)
            Error += 1

        if Error > 30:
            print('Too many errors. Sleep 60 seconds.')
            cycle_time = 120

def create_config_file():
    """ find the first device of /dev/ttyUSB* and 
    generate /etc/gammu-smsdrc
    """
    
    global DEVICE
    global DEVICE_OLD
    cycle_time = 10
    print("find the first device of /dev/ttyUSB* and generate /etc/gammu-smsdrc")
    Error = 0
    while True:
        # todo: if error happened too many, increase cycle time
        time.sleep(cycle_time)

        try:
            # if usb stick not exists, sleep 60 seconds
            DEVICE = utils.get_first_tty_usb()
            if not DEVICE:
                print(
                    "Device: %s not exists! Sleep 60 seconds." % DEVICE)
                cycle_time = 60
            else:

                create_gammu_smsdrc.create_to_etc_smsdrc("/etc/gammu-smsdrc")
                stop_gammu()
                start_gammu()
                Error = 0
                cycle_time = CYCLE_TIME
                DEVICE_OLD = DEVICE
                break
        except Exception as e:
            print('Error: %s' % e)
            Error += 1

        if Error > 30:
            print('Too many errors. Sleep 60 seconds.')
            cycle_time = 120

def check_change_of_device():
    global DEVICE_OLD
    if DEVICE_OLD != DEVICE:
        print(f"device changed {DEVICE_OLD} -> {DEVICE}")

        create_config_file()

        DEVICE_OLD = DEVICE

