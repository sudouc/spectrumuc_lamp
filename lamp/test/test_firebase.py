"""Tests for the firebase module"""
import unittest
from unittest.mock import patch, call, MagicMock, NonCallableMagicMock, DEFAULT
import tempfile
import os
import time

import pyrebase
from .. import firebase

class TestFirebase(unittest.TestCase):

    config_file_path = os.path.join(os.path.dirname(__file__), 'test_firebase.cfg')
    old_heartbeat_interval = None

    # Helpers
    def get_database(self):
        return firebase.Database(self.config_file_path)

    def setUp(self):
        self.old_heartbeat_interval = firebase.HEARTBEAT_INTERVAL

    def tearDown(self):
        firebase.HEARTBEAT_INTERVAL = self.old_heartbeat_interval

    def test_database_init(self):
        """
        Test Init the firebase database object, test all attributes
        """
        database = firebase.Database(self.config_file_path)
        self.assertTrue(hasattr(database, 'database'))
        self.assertTrue(hasattr(database, 'user'))
        self.assertTrue(hasattr(database, 'stream'))
        self.assertTrue(hasattr(database, 'config'))
        self.assertTrue(hasattr(database, 'stop_heartbeat'))

        self.assertFalse(database.stop_heartbeat)


    def test_database_init_empty_string(self):
        """
        Test Firebase Config File Not Found: Empty String raises FileNotFoundError
        """
        self.assertRaises(FileNotFoundError, firebase.Database, "")


    def test_database_init_missing_file(self):
        """
        Test Firebase Config File Not Found: Missing File raises FileNotFoundError
        """
        self.assertRaises(FileNotFoundError, firebase.Database, self.config_file_path + '.missing')


    def test_get_firebase_config(self):
        """
        Test Creating the firebase_config object
        """

        database = firebase.Database(self.config_file_path)
        firebase_config = database.get_firebase_config()

        expected_config = {
            "apiKey": "APIKEYHERE",
            "authDomain": "AUTHDOMAIN",
            "databaseURL": "DATABASEURL",
            "storageBucket": "STORAGEBUCKET",
            "messagingSenderId": "MESSAGINGSENDERID"
        }

        self.assertEqual(firebase_config, expected_config)


    def test_get_credentials(self):
        """
        Test Credentials are returned correctly
        """
        database = firebase.Database(self.config_file_path)
        firebase_creds = database.get_credentials()

        expected_creds = ("hostname@example.com", "password")

        self.assertEqual(firebase_creds, expected_creds)


    def test_initialise(self):
        """
        Test Initialise called pyrebase and heartbeat methods correctly
        """

        expected_config = {
            "apiKey": "APIKEYHERE",
            "authDomain": "AUTHDOMAIN",
            "databaseURL": "DATABASEURL",
            "storageBucket": "STORAGEBUCKET",
            "messagingSenderId": "MESSAGINGSENDERID"
        }

        mockdb = NonCallableMagicMock()
        mockauth = MagicMock()
        mockdb.auth.return_value = mockauth

        with patch.object(pyrebase,
                          'initialize_app',
                          return_value=mockdb
                         ) as mock_initialize_app:

            with patch.object(firebase.Database,
                              'spawn_heartbeat',
                              return_value=True
                             ) as mock_spawn_heartbeat:

                database = firebase.Database(self.config_file_path)
                database.initialise()

        mock_initialize_app.assert_called_once_with(expected_config)
        mockdb.auth.assert_called_once_with()
        (mockauth.sign_in_with_email_and_password
         .assert_called_once_with('hostname@example.com', 'password'))
        mock_spawn_heartbeat.assert_called_once_with()


    def test_get_online_leaf(self):
        """
        Test Pyrebase is called correctly to identify the online leaf
        """

        database = firebase.Database(self.config_file_path)

        database.database = NonCallableMagicMock()
        database.user = {}

        with patch.dict(database.user, values={'localId': 'MOCK_ID'}) as mock_user:
            assert database.user == {'localId': 'MOCK_ID'}
            database.get_online_leaf()

        kall = call().child('nodes').child('MOCK_ID').child('online') # Expected

        # Mock auto-generates the members here, so we ignore the lint error
        database.database.database.assert_has_calls(kall.call_list()) #pylint: disable=no-member


    def test_spawn_heartbeat(self):
        """
        Test Heartbeat thread is spawned and calls set() at least twice
        """
        firebase.HEARTBEAT_INTERVAL = 0.25

        mock_node = NonCallableMagicMock()

        database = firebase.Database(self.config_file_path)

        with patch.object(database, 'get_online_leaf', return_value=mock_node) as mock_get_online_leaf:
            heartbeat_thread = database.spawn_heartbeat()

        time.sleep(firebase.HEARTBEAT_INTERVAL + 0.5)
        database.stop_heartbeat = True
        heartbeat_thread.join()

        mock_get_online_leaf.assert_called_once_with()
        mock_node.set.assert_has_calls([
            call({'.sv': 'timestamp'}),
            call({'.sv': 'timestamp'})
        ])
        print('This is actually testing a race condition, but on most systems should still pass as expected')


    def test_register_callback_and_callback_full_color(self):
        """
        Test Callback is registered correctly and receives callbacks for a partial color update
        """
        callback_function = MagicMock()

        database = self.get_database()

        mock_db = MagicMock()

        color_node = (
            mock_db.database.return_value
            .child.return_value
            .child.return_value
            .child.return_value
        ) = MagicMock()

        with patch.multiple(database, database=mock_db, user={'localId': 'MOCK_ID'}):
            database.register_callback(callback_function)

            message_object = {
                'path': '/',
                'data': {
                    "red": 7,
                    "green": 180,
                    "blue": 3
                }
            }

            (stream_handler,), _ = color_node.stream.call_args

            stream_handler(message_object)

        callback_function.assert_called_once_with(
            {
                "red": 7,
                "green": 180,
                "blue": 3
            }
        )


    def test_register_callback_and_callback_partial_color(self):
        """
        Test Callback is registered correctly and receives callbacks for a full color update
        """
        callback_function = MagicMock()

        database = self.get_database()

        mock_db = MagicMock()

        color_node = (
            mock_db.database.return_value
            .child.return_value
            .child.return_value
            .child.return_value
        ) = MagicMock()

        with patch.multiple(database, database=mock_db, user={'localId': 'MOCK_ID'}):

            database.register_callback(callback_function)

            (stream_handler,), _ = color_node.stream.call_args

            message_object_red = {'path': '/red', 'data': 50}
            message_object_green = {'path': '/green', 'data': 125}
            message_object_blue = {'path': '/blue', 'data': 200}
            message_object_invalid = {'path': 'invalid', 'invalid': 'invalid'}
            stream_handler(message_object_red)
            stream_handler(message_object_green)
            stream_handler(message_object_blue)
            stream_handler(message_object_invalid) # Shouldn't trigger a callback

        kall_list = [
            call({"red": 50,
                  "green": 0,
                  "blue": 0
                 }),
            call({"red": 50,
                  "green": 125,
                  "blue": 0
                 }),
            call({"red": 50,
                  "green": 125,
                  "blue": 200
                 })
            ]

        callback_function.assert_has_calls(kall_list)
        self.assertEqual(callback_function.call_count, 3)
