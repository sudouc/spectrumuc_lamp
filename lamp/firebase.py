#!/usr/bin/env python3
"""Firebase backend for lamp"""

import configparser
from threading import Thread
import sys
import os
import time
import copy
import pyrebase

HEARTBEAT_INTERVAL = 5 # seconds

class Database(object):
    """Encapsulation of the firebase connection in an object"""

    def __init__(self, config_file_path):
        """
        Create the database object

        param config_file_path: path to the desired config file
        """

        if not config_file_path or not os.path.exists(config_file_path):
            raise FileNotFoundError("Config File {0} Not Found".format(config_file_path))

        self.database = None
        self.user = None
        self.stream = None
        self.stop_heartbeat = False
        self.color = {}

        self.config = configparser.ConfigParser() # todo move all of this out into the using module so we don't parse a config file here
        self.config.optionxform = str
        self.config_file_path = config_file_path
        self.config.read_file(open(self.config_file_path))


    def initialise(self):
        """
        Initialise the connection to firebase, (authenticate), spawn a heartbeat thread
        """

        print('Initialise Backend')
        sys.stdout.flush()

        # Get the firebase configuration and init a connection
        self.database = pyrebase.initialize_app(self.get_firebase_config())

        auth = self.database.auth()
        self.user = auth.sign_in_with_email_and_password(*self.get_credentials())

        print("Authenticated")
        sys.stdout.flush()

        # Spawn a thread to issue heartbeat to the firebase
        self.spawn_heartbeat()

        print('Spawned Heartbeat')
        sys.stdout.flush()


    def get_firebase_config(self):
        """Returns the firebase_config object"""

        firebase_config = {}
        for key, value in self.config.items('firebase-config'):
            firebase_config[key] = value
        return firebase_config


    def get_credentials(self):
        """Returns the email and password from the firebase-credentials in config, as a tuple"""

        email = self.config.get('firebase-credentials', 'email')
        password = self.config.get('firebase-credentials', 'password')

        return email, password

    def get_online_leaf(self):
        """
        Return a reference to the leaf in the database,
        that is the online time/status of this node
        """
        return (
            self.database.database()
            .child('nodes')
            .child(self.user['localId'])
            .child('online')
        )

    def spawn_heartbeat(self):
        """Spawn and return heartbeat thread"""

        hb_thread = Thread(target=self.heartbeat_task, args=(self.get_online_leaf(),))
        hb_thread.start()

        return hb_thread


    def heartbeat_task(self, node_to_set):
        """Heartbeat thread, update this node's timestamp in the firebase at HEARTBEAT_INTERVAL"""
        while not self.stop_heartbeat:
            beat_response = node_to_set.set({".sv": "timestamp"})
            # TODO, check the response for errors
            time.sleep(HEARTBEAT_INTERVAL)

        self.stop_heartbeat = False

    def register_callback(self, callback):
        """
        Register a callback function to be called when the node color changes
        The callback will be called with a Color object with RGB properties
        """

        self.color = {
            "red": 0,
            "green": 0,
            "blue": 0
        }

        def stream_handler(message):
            """Handler method for the stream response from firebase"""

            new_color = copy.deepcopy(self.color)

            if message['path'] == '/':
                new_color['red'] = message['data']['red']
                new_color['green'] = message['data']['green']
                new_color['blue'] = message['data']['blue']

            elif message['path'] == '/red':
                new_color['red'] = message['data']

            elif message['path'] == '/green':
                new_color['green'] = message['data']

            elif message['path'] == '/blue':
                new_color['blue'] = message['data']
            else:
                print('No Valid Colors')
                print(message)
                return False

            self.color = new_color
            callback(self.color)
            return True

        print('Color change callback registered')
        sys.stdout.flush()

        # FIXME: Move getting the color node out to a different method
        self.stream = (
            self.database.database().child('nodes')
            .child(self.user['localId'])
            .child('color').stream(stream_handler)
        )

        print("Stream started, you're good to go!")
        sys.stdout.flush()
