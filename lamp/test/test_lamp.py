"""Test for the lamp module"""
import unittest
from unittest.mock import patch
import os

from .. import firebase
from .. import lamp

class TestLamp(unittest.TestCase):
    """Lamp Test Case"""

    def test_main(self):
        """
        Test Lamp initialises firebase backend correctly
        """
        with patch.object(firebase, 'Database') as mock_database:
            lamp.main()

        mock_database.assert_called_once_with(config_file_path='firebase.cfg')
        mock_database.return_value.initialise.assert_called_once_with()
        mock_database.return_value.register_callback.assert_called_once_with(lamp.change_color)

    def test_change_color(self):
        """
        Test DMX command string is produced correctly in the callback
        """

        color = {
            "red": 50,
            "green": 100,
            "blue": 150
        }

        with patch.object(os, 'system') as mock_system:
            lamp.change_color(color)

        expected_command = "ola_streaming_client -d '50,100,150'"
        mock_system.assert_called_once_with(expected_command)
