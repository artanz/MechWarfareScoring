Mech Warfare Scoring Server

Edited by R-TEAM Robotics

Download and install Python: https://www.python.org/downloads/

Download and install wxPython: https://www.wxpython.org/pages/downloads/ (pip install -U wxPython)

Download and install latest PySerial: https://pypi.org/project/pyserial/ (pip install pyserial)

Install all required libraries with pip (recommended):

    pip install -r requirements.txt

This installs wxPython and PySerial automatically from the requirements.txt file.

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

OBS Overlay

An HTML overlay (obs_overlay.html) shows the same match information as the GUI:
match timer, status, team names, and each mech's HP bar and value. The GUI
writes this data to obs_score.json while running.

To use it in OBS:

1. Run the scoring GUI (MWScoreGUI.py).
2. In the GUI menu, select Overlay > Enable Overlay. This starts a local
   HTTP server that serves the overlay.
3. In OBS, add a Browser Source and point it to:

        http://localhost:8080/obs_overlay.html

   Use Overlay > Stop Overlay (or toggle Enable Overlay off) to stop the
   server.

(Alternatively, you can serve the folder yourself with `python3
serve_overlay.py`, or load obs_overlay.html as a local file in the Browser
Source, but the in-app menu option is the easiest.)

The overlay refreshes automatically every half second.

Note: The older obs_score_*.txt files (red/blue text sources) are still written
for backwards compatibility.
