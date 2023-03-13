Mech Warfare Scoring Server

Edited by R-TEAM Robotics

Download and install Python 3.10.10: https://www.python.org/downloads/ (wxPython is broken with latest python 3.11.2 as of 3/12/23, may of been fixed since)

Download and install latest wxPython: https://www.wxpython.org/pages/downloads/ (pip install -U wxPython)

Download and install latest PySerial: https://pypi.org/project/pyserial/ (pip install pyserial)

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
