#!/bin/bash
pip uninstall spectrumuc_lamp
systemctl stop spectrumuc.service
systemctl disable spectrumuc.service
rm /lib/systemd/system/spectrumuc.service
rm /lib/systemd/system/spectrumuc.service # symlinks?
systemctl daemon-reload
systemctl reset-failed

