# 更改smsutil.serive文件之后执行此脚本

#!/bin/bash
sudo systemctl daemon-reload
sudo systemctl restart gammu-check
sleep 3
sudo systemctl status gammu-check