#!/usr/bin/env bash
set -e

PROJECT_DIR="/root/psychology_bot"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Directory $PROJECT_DIR not found. Detecting current directory..."
    PROJECT_DIR="$(pwd)"
fi

echo "Setting up services for project in: $PROJECT_DIR"

# 1. Detect Python virtual environment
VENV_PATH=""
if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    VENV_PATH="$PROJECT_DIR/venv"
elif [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    VENV_PATH="$PROJECT_DIR/.venv"
elif [ -f "/opt/psychology_bot/venv/bin/python" ]; then
    VENV_PATH="/opt/psychology_bot/venv"
else
    echo "No existing virtual environment found. Creating one at $PROJECT_DIR/venv..."
    python3 -m venv "$PROJECT_DIR/venv"
    VENV_PATH="$PROJECT_DIR/venv"
    "$VENV_PATH/bin/pip" install --upgrade pip
    "$VENV_PATH/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
fi

echo "Using virtual environment: $VENV_PATH"

# Ensure gunicorn is installed
if [ ! -f "$VENV_PATH/bin/gunicorn" ]; then
    echo "Installing gunicorn..."
    "$VENV_PATH/bin/pip" install gunicorn
fi

# Ensure storage directory exists
mkdir -p "$PROJECT_DIR/private_uploads"

# 2. Write Telegram Bot systemd unit
cat <<EOF > /etc/systemd/system/psychobot-bot.service
[Unit]
Description=Psychology Clinic Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=-$PROJECT_DIR/.env
ExecStart=$VENV_PATH/bin/python main.py
Restart=on-failure
RestartSec=5s
NoNewPrivileges=true
PrivateTmp=true
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
Alias=psychology_bot.service
EOF

# 3. Write Web Gunicorn systemd unit
cat <<EOF > /etc/systemd/system/psychobot-web.service
[Unit]
Description=Psychology Clinic Gunicorn Web Service
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=-$PROJECT_DIR/.env
ExecStart=$VENV_PATH/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=on-failure
RestartSec=5s
NoNewPrivileges=true
PrivateTmp=true
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
Alias=psychology_web.service
EOF

# 4. Create explicit symlinks for psychology_bot and psychology_web
ln -sf /etc/systemd/system/psychobot-bot.service /etc/systemd/system/psychology_bot.service
ln -sf /etc/systemd/system/psychobot-web.service /etc/systemd/system/psychology_web.service

# 5. Reload systemd daemon
systemctl daemon-reload

# 6. Enable and restart both services
systemctl enable psychobot-bot.service psychobot-web.service
systemctl restart psychobot-bot.service psychobot-web.service

echo "Services successfully configured and started!"
echo "--- Telegram Bot Status ---"
systemctl status psychobot-bot.service --no-pager || true
echo "--- Web Service Status ---"
systemctl status psychobot-web.service --no-pager || true
