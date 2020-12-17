from src.create_gammu_smsdrc import generate_smsdrc


def test_generate_smsdrc():
    dev0 = "/dev/ttyUSB0"
    dev1 = "/dev/ttyUSB1"
    content = generate_smsdrc(dev0)
    assert dev0 in content
    assert not dev1 in content