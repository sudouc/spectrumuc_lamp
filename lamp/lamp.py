#!/usr/bin/env python3
"""
lamp.py subscribes to this node's color in firebase,
then issues shell commands to change the color of the light.

This module designed to run on a raspberry pi that is also running OLA https://www.openlighting.org/
"""
import os
from . import firebase as backend

__version__ = '0.0.1'

def main():
    """Initialise the backend and register a callback when the color changes"""
    database = backend.Database(config_file_path="firebase.cfg")
    database.initialise()
    database.register_callback(change_color)


def change_color(color):
    """Issue the command to change the color"""

    dmx_string = ",".join(str(x) for x in [color['red'], color['green'], color['blue']])
    command = "ola_streaming_client -d '{0}'".format(dmx_string)
    os.system(command)
