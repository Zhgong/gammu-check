from nose.tools import *
from gammu_check import gammu_check

def setup():
    print ("SETUP!")

def teardown():
    print ("TEAR DOWN!")

def test_basic():
    print ("I RAN!")

def test_file_modified():
    file = '/var/log/gammu-smsd'
    assert gammu_check.file_modified_timeout(file, 100) == False

def test_get_pid():
    name = "gammu"
    pid = gammu_check.get_pid(name)

    assert pid >= 0

def test_find_huawei_usb():
    assert "E173" in gammu_check.get_huwei_usb()


def test_get_usb_id():
    usb= 'Bus 001 Device 005: ID 12d1:1436 Huawei Technologies Co., Ltd. E173 3G Modem (modem-mode)'
    res = gammu_check.get_usb_id(usb)
    print(res)
    assert res == ('12d1', '1436')



def test_stop_gammu():
    assert gammu_check.stop_gammu() == True


def test_reset_huawei():
    assert gammu_check.reset_huawei() == True

def test_start_gammu():
    assert gammu_check.start_gammu() == True


def test_check_logfile_size():
    assert gammu_check.check_logfile_size(50) == True

def test_usb_modeswitch():
    assert gammu_check.usb_modeswitch() == True