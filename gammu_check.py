import sys
from src import run

if len(sys.argv) == 2:
    loggingfile = sys.argv[1]
else:
    loggingfile = ''
run.logging_config(loggingfile)
print("<----------- START --------------------------->")
# usb_modeswitch()
run.run()