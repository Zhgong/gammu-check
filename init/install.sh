# 首次运行执行次脚本
# Install the service with systemctl
sudo ln -s /home/pi/gammu-check/init/gammu-check.service /etc/systemd/system

sudo systemctl enable gammu-check

sudo systemctl start gammu-check