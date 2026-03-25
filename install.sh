#!/bin/bash
set -e

USER_HOME=$(eval echo ~$SUDO_USER)
USERNAME=$SUDO_USER

echo "=== Installiere logo-cam für $USERNAME ==="

# Abhängigkeiten
sudo apt-get update -q
sudo apt-get install -y mpv python3-pip
pip3 install python-snap7 --break-system-packages

# Service-Datei mit korrekten Pfaden generieren
sudo tee /etc/systemd/system/logo_cam.service > /dev/null <<EOF
[Unit]
Description=LOGO! Monitor
After=graphical-session.target network-online.target
Wants=graphical-session.target network-online.target

[Service]
User=$USERNAME
WorkingDirectory=$USER_HOME/logo-cam
ExecStart=/usr/bin/python3 $USER_HOME/logo-cam/logo_cam.py
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/$(id -u $USERNAME)

[Install]
WantedBy=graphical-session.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable logo_cam
sudo systemctl restart logo_cam

echo "=== Fertig! ==="
sudo systemctl status logo_cam --no-pager
