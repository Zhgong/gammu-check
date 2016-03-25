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

global LOGFILE
global DEVICE

LOGFILE = '/var/log/gammu-smsd'
DEVICE = '/dev/ttyUSB0'

CYCLE_TIME = 5

@click.command()
@click.option('--interval', '-i', default=2, help='number of greetings')
def run(interval):
    CYCLE_TIME = interval
    logging.info('set CYCLE_TIME: %d '% interval)
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
        logging.basicConfig(level=logging.INFO,filename=loggingfile, format=FORMAT)
        print('Logging file for is: %s'%loggingfile)
    else:
        logging.basicConfig(level=logging.INFO, format=FORMAT)


# compare last time with current time, if the file has not been changed in "seconds" seconds, return true
def file_modified_timeout(file, seconds):
    mftime = os.path.getmtime(file)
    now = time.time()

    logging.debug('File: %s last modified at: %s.' %(file, mftime))
    logging.debug('Current time: %s' % now)
    logging.debug('Time deviation is: %s' % (abs(now - mftime)))

    return abs(now-mftime) > seconds

# check if the gammu is dead
def is_gammu_dead():
    return file_modified_timeout(LOGFILE, 10)


def get_pid(name):
    # get the pid of a process
    cmd = r'pgrep %s' % name
    # getting the pid of gammu-smsd
    try:
        pid = int(subprocess.check_output(cmd, shell=True))
        logging.info("Process: %s is running with pid: %s" % (name, pid))
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            logging.info("Process: %s is not running" % name)
            return 0
        else:
            logging.info("Error while executing %s with return value: %d" % (cmd, e.returncode))
            return -1
    except ValueError as e:
        logging.info("More than one matched process found. Error with: %s." % e)
        return -1
    except Exception as e:
        logging.info("unkonw Error with: %s." % e)
        return -1
    return pid

# stop gammu process
def stop_gammu():
    name = "gammu-smsd"
    pid = get_pid(name)

    if pid < 0:
        raise Exception("Error while getting pid of: %s" % name)
    elif pid == 0:
        # process is not running
        return True
    else:
        # kill the gammu process
        cmd = r"sudo kill -9 %s" %str(pid)
        try:
            res = subprocess.check_output(cmd, shell=True)
            logging.info("Process: %s with pid: %s is killed" % (name, pid))
            return True
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                return True # process not found,
            else:
                logging.info("Error while killing process: %s with pid: %s." % (name, pid))
                raise


def get_huwei_usb():
    # get huawei usbid with lsusb
    # --> 'Bus 001 Device 005: ID 12d1:1436 Huawei Technologies Co., Ltd. E173 3G Modem (modem-mode)'
    cmd = 'lsusb'
    lsres = subprocess.check_output(cmd, shell=True).decode().split('\n')

    for r in lsres:
        if 'Huawei' in r:
            return r

def get_usb_id(usb):
    # input 'Bus 001 Device 005: ID 12d1:1436 Huawei Technologies Co., Ltd. E173 3G Modem (modem-mode)'
    # output: '12d1', '1436'
    idRegex = re.compile(r'ID\s(.*)?:(.*)?\sHuawei')
    match = idRegex.search(usb)
    return match.groups()

# reset Huawei usb UTMS disk
def reset_huawei():

    # execute command 'sudo usb_modeswitch -v 0x12d1 -p1436 --reset-usb'
    usb = get_huwei_usb()
    id1, id2 = get_usb_id(usb)
    cmd = 'sudo usb_modeswitch -v 0x%s -p%s --reset-usb' %(id1, id2)
    logging.info("Resetting USB with command: %s" % cmd)
    res = subprocess.check_output(cmd, shell=True)


# start gammu process again
def start_gammu():
    name = "gammu-smsd"
    # cmd = r'sudo /etc/init.d/%s start' %name
    cmd = r'sudo /etc/init.d/%s restart' %name
    res = subprocess.check_output(cmd, shell=True)

    logging.info("%s" %res)

    pid = get_pid(name)

    if pid > 0:
        logging.info("Process %s is successfully started with PID: %d." %(name, pid))
        return True
    else:
        logging.info("Failed to start process %s started with PID: %d." %(name, pid))
        return False

def gammu_restart_daemon():
    # check if gammu is dead
    if is_gammu_dead():
        logging.error("gammu-smsd is dead, start restarting process")
        # stop gammu
        logging.info("Stopping gammu ...")
        stop_gammu()
        # reset usb
        logging.info("Resetting Huawei E173 ...")
        reset_huawei()


        # check log file size
        check_logfile_size(10)

        #start gammu
        logging.info("Starting gammu ...")
        start_gammu()
        logging.info("Process finished.")


def check_logfile_size(MAX_SIZE = 20):
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
    logging.info('Executing command: %s' % cmd)

    lsres = subprocess.check_output(cmd, shell=True).decode().split('\n')

    if os.path.exists(DEVICE):
        logging.info("Device: %s exists! Success." % DEVICE)
        return True
    else:
        logging.info("Device: %s not exists! Command failed." % DEVICE)
        return False


def main():
    cycle_time = 10
    logging.info("Starting gammu-check Daemon.")
    Error = 0
    while True:
        # todo: if error happened too many, increase cycle time
        time.sleep(cycle_time)

        try:
            # if usb stick not exists, sleep 60 seconds
            if not os.path.exists(DEVICE):
                logging.info("Device: %s not exists! Sleep 60 seconds." % DEVICE)
                cycle_time = 60

            # if not os.path.exists(DEVICE):
            #     # force to run usb_modeswitch to get /dev/ttyUSB0
            #     logging.debug('Device : %s not detected. Trying usb_modeswtich' % DEVICE)
            #     usb_modeswitch()
            #     Error += 1
            else:

                gammu_restart_daemon()
                Error = 0
                cycle_time = CYCLE_TIME
        except Exception as e:
            logging.info('Error: %s' % e)
            Error += 1

        if Error > 30:
            logging.info('Too many errors. Sleep 60 seconds.')
            cycle_time = 60
if __name__ == '__main__':
    if len(sys.argv) == 2:
        loggingfile = sys.argv[1]
    else:
        loggingfile = ''
    logging_config(loggingfile)
    logging.info("<---------------------------------------->")
    usb_modeswitch()
    run()
