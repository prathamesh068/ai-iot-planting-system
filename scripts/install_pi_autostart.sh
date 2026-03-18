#!/usr/bin/env bash

set -euo pipefail

SERVICE_NAME="ai-iot-planting-system.service"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
RUN_AS_USER="${SUDO_USER:-$USER}"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "Error: systemctl not found. This script must be run on a systemd-based Linux distro (Raspberry Pi OS)." >&2
  exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Error: virtualenv python not found at $PYTHON_BIN" >&2
  echo "Create it first: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.pi.txt" >&2
  exit 1
fi

echo "Creating /etc/systemd/system/$SERVICE_NAME"
sudo tee "/etc/systemd/system/$SERVICE_NAME" >/dev/null <<EOF
[Unit]
Description=AI + IoT Smart Plant System Listener
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_AS_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_BIN run.py --listen-commands
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd"
sudo systemctl daemon-reload

echo "Enabling service on boot"
sudo systemctl enable "$SERVICE_NAME"

echo "Starting service now"
sudo systemctl restart "$SERVICE_NAME"

echo
echo "Service status:"
sudo systemctl --no-pager --full status "$SERVICE_NAME"

echo
echo "Done. On reboot, the listener will start automatically."
echo "Log follow command: sudo journalctl -u $SERVICE_NAME -f"