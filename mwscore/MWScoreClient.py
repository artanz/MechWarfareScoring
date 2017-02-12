#   MWScoreClient.py
#
#   This is a basic client for the MWScoreGUI server.

import MWScore
import time
import sys

def fn(mechsAndScores):
    print("Received update: " + repr(mechsAndScores))

def main(server):
    print("Connecting to host: " + server)
    conn = MWScore.SocketClient(server, 2525, fn)
    # run whatever GUI you want here
    time.sleep(10)
    conn.ThreadKill = True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main('192.168.1.102')

