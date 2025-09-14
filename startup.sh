#!/bin/bash

# Register lumon-ui.py as a debian system startup service

# Get the directory where the current script is located
DIR="$(cd "$(dirname "$0")" && pwd)"
# Define service file path
SERVICE_FILE="/etc/systemd/system/lumon-ui.service"
# Define Python script path
PYTHON_SCRIPT="$DIR/lumon-ui.py"
# Define Python interpreter path
PYTHON_INTERPRETER="/usr/bin/python3"

# Create service file
echo "[Unit]
Description=lumon-ui Service
After=network.target
[Service]
ExecStart=$PYTHON_INTERPRETER $PYTHON_SCRIPT
WorkingDirectory=$DIR
Restart=always
User=$(whoami)
[Install]
WantedBy=multi-user.target" | sudo tee $SERVICE_FILE
# Reload systemd daemon
sudo systemctl daemon-reload
# Start the service
sudo systemctl start lumon-ui.service
# Enable service to start on boot
sudo systemctl enable lumon-ui.service
