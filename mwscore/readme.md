Mech Warfare Scoring Server

Edited by R-TEAM Robotics

Download and install latest Python 2.x: http://www.python.org/download/releases/

Download and install latest wxPython: http://www.wxpython.org/download.php

Download and install latest PySerial: https://pypi.python.org/pypi/pyserial

More detailed instructions here: https://learn.adafruit.com/arduino-lesson-17-email-sending-movement-detector/installing-python-and-pyserial

Edit mechs.conf to include mechs

Requires XBEE S1 and XBee explorer hooked up to PC

    Scoring Receiver XBEE setup (Send Broadcast message)
        ATBD = 5 (38400bps)
        ATID = 6200
        MY   = 6201
        DL   = FFFF
        DH   = 0
        CH   = c

Run MWScoreGUI.py to launch scoring system
