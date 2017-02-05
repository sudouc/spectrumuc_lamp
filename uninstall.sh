#!/bin/bash
pip uninstall lamp
systemctl stop lamp.service
systemctl disable lamp.service
rm /lib/systemd/system/lamp.service
rm /lib/systemd/system/lamp.service # symlinks?
systemctl daemon-reload
systemctl reset-failed

# TODO: What if systemd isn't installed, what can we do then?