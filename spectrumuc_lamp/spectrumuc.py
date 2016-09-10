"""
spectrumuc.py subscribes to this node's location in firebase and issues shell commands to change the color of the light

This module designed to run on a raspberry pi that is also running
OLA https://www.openlighting.org/
"""

import os
import sys
from . import firebase as backend

def main():
    """Entry point"""
    backend.init()
    backend.register_callback(change_color)


def change_color(color):
    """Issue the command to change the color"""

    assert isinstance(color, backend.Color)
    print("red:", color.red, "green:", color.green, "blue:", color.blue)
    sys.stdout.flush()

    # Execute command to change light to that color
    os.system("ola_streaming_client -d '"
              + str(color.red) + ","
              + str(color.green) + ","
              + str(color.blue) + "'")

if __name__ == '__main__':
    main()
