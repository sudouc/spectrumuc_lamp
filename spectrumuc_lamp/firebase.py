"""Firebase backend for spectrumUC lamp"""

import configparser
import os
import threading
import sys
import pyrebase

class Color(object):

    def __init__(self):
        self.red = 0
        self.green = 0
        self.blue = 0

HEARTBEAT_INTERVAL = 5 # seconds
_DB = None
_USER = None
DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'firebase.cfg')

config = configparser.ConfigParser()
config.optionxform = str
config.readfp(open(DEFAULT_CONFIG_FILE))

def init():
    """
    Connect to firebase, show presence, spawn a heartbeat thread
    """

    global _DB, _USER

    # Get the firebase configuration and init a connection
    firebase_config = {}
    for key, value in config.items('firebase-config'):
        firebase_config[key] = value
    _DB = pyrebase.initialize_app(firebase_config)

    # Authenticate
    email = config.get('firebase-credentials', 'email')
    password = config.get('firebase-credentials', 'password')

    auth = _DB.auth()
    _USER = auth.sign_in_with_email_and_password(email, password)

    # Spawn a thread to issue heartbeat to the firebase
    _heartbeat()


def _heartbeat():
    """Set the last online time to the server timestamp, and schedule to do it again"""
    _DB.database().child('nodes').child(_USER['localId']).child('online').set({".sv": "timestamp"})
    threading.Timer(HEARTBEAT_INTERVAL, _heartbeat).start()


def register_callback(callback):
    """
    Register a callback function to be called when the node color changes
    The callback will be called with a Color object with RGB properties
    """

    color = Color()

    def stream_handler(message):

        if message['path'] == '/':
            color.red = message['data']['red']
            color.green = message['data']['green']
            color.blue = message['data']['blue']

        elif message['path'] == '/red':
            color.red = message['data']

        elif message['path'] == '/green':
            color.green = message['data']

        elif message['path'] == '/blue':
            color.blue = message['data']
        else:
            print('No Valid Colors')
            print(message)

        callback(color)

    _stream = _DB.database().child('nodes').child(_USER['localId']).child('color').stream(stream_handler)
