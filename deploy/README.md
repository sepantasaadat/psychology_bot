# Psychology Clinic Bot & Web Service — VPS Deployment Guide

This guide describes how to deploy, harden, and manage the **Psychology Clinic Telegram Bot and Web Reservation System** on an Ubuntu 22.04 / 24.04 LTS VPS using production-grade **systemd** services and timers.

---

## Architecture Overview

The system runs as decoupled services on an Ubuntu VPS:

1. **`psychobot-web.service`**: Gunicorn WSGI HTTP server executing Flask (`app:app`), binding to `127.0.0.1:5000` behind an Nginx reverse proxy.
2. **`psychobot-bot.service`**: Standalone daemon running the python-telegram-bot application (`python main.py`).
3. **`psychobot-report.service` & `psychobot-report.timer`**: Systemd timer firing nightly at 21:00 Tehran time (`OnCalendar=*-*-* 21:00:00`, `Persistent=true`) to generate and dispatch the daily summary via Telegram and Email.

---

## 1. System Prerequisites

On a fresh Ubuntu VPS:

```bash
# Update repositories
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.12, venv, git, compilation tools, and image libraries
sudo apt-get install -y python3 python3-venv python3-pip git gcc libjpeg-dev zlib1g-dev nginx
```

### Configure System Timezone
The clinic operates in Iran Standard Time. Set the system timezone to `Asia/Tehran` so that systemd timers and cron triggers fire synchronously with Tehran local time:

```bash
sudo timedatectl set-timezone Asia/Tehran
timedatectl status
```

---

## 2. User & Directory Setup

For production security, do not run services as `root`. Create a dedicated system user `psychobot`:

```bash
# Create system user without login shell
sudo useradd -r -s /usr/sbin/nologin -d /opt/psychology_bot psychobot

# Clone repository into /opt/psychology_bot
sudo git clone <REPOSITORY_URL> /opt/psychology_bot
cd /opt/psychology_bot

# Set up Python virtual environment
sudo python3 -m venv /opt/psychology_bot/venv
sudo /opt/psychology_bot/venv/bin/pip install --upgrade pip
sudo /opt/psychology_bot/venv/bin/pip install -r /opt/psychology_bot/requirements.txt

# Create storage directories
sudo mkdir -p /opt/psychology_bot/private_uploads

# Set ownership and permissions
sudo chown -R psychobot:psychobot /opt/psychology_bot
sudo chmod 750 /opt/psychology_bot
sudo chmod 700 /opt/psychology_bot/private_uploads
```

> **Note on `/root/psychology_bot` deployments:**
> If you deploy under `/root/psychology_bot` as `root`, update the unit files in `deploy/systemd/` by changing `User=root`, `Group=root`, and updating `WorkingDirectory`, `EnvironmentFile`, and `ExecStart` paths to `/root/psychology_bot`.

---

## 3. Environment Configuration

Copy the example environment file and populate your production secrets:

```bash
sudo cp /opt/psychology_bot/.env.example /opt/psychology_bot/.env
sudo nano /opt/psychology_bot/.env
```

Ensure the following variables are properly configured:
- `BOT_TOKEN`: Production Telegram Bot token from @BotFather.
- `FLASK_SECRET_KEY`: Cryptographically secure random secret (e.g., generated with `python3 -c "import secrets; print(secrets.token_hex(32))"`).
- `ADMIN_IDS`: Comma-separated list of administrative Telegram user IDs.
- `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD`, `RECEIVER_EMAIL`: Email alert credentials.

Lock down permissions on the `.env` file:
```bash
sudo chown psychobot:psychobot /opt/psychology_bot/.env
sudo chmod 600 /opt/psychology_bot/.env
```

---

## 4. Install & Enable Systemd Units

Copy the unit files into the systemd system directory:

```bash
sudo cp /opt/psychology_bot/deploy/systemd/*.service /etc/systemd/system/
sudo cp /opt/psychology_bot/deploy/systemd/*.timer /etc/systemd/system/

# Reload systemd manager configuration
sudo systemctl daemon-reload
```

### Enable & Start Services

```bash
# Enable and start Web WSGI service
sudo systemctl enable --now psychobot-web.service

# Enable and start Telegram Bot daemon
sudo systemctl enable --now psychobot-bot.service

# Enable and start Daily Report Timer
sudo systemctl enable --now psychobot-report.timer
```

---

## 5. Verify & Monitor Services

Check service statuses:
```bash
sudo systemctl status psychobot-web.service
sudo systemctl status psychobot-bot.service
sudo systemctl status psychobot-report.timer
```

Check active timers:
```bash
sudo systemctl list-timers --all | grep psychobot
```

Stream logs using `journalctl`:
```bash
# Web application logs
sudo journalctl -u psychobot-web.service -f

# Telegram bot logs
sudo journalctl -u psychobot-bot.service -f

# Daily report logs
sudo journalctl -u psychobot-report.service -f
```

---

## 6. Nginx Reverse Proxy & TLS Configuration

Configure Nginx to proxy requests from the public domain to Gunicorn on `127.0.0.1:5000`.

Create `/etc/nginx/sites-available/psychobot`:

```nginx
server {
    listen 80;
    server_name drshafaeiclinic.ir www.drshafaeiclinic.ir;

    client_max_body_size 10M;

    # Static assets caching
    location /static/ {
        alias /opt/psychology_bot/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Deny direct access to private uploads
    location /private_uploads/ {
        deny all;
        return 404;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/psychobot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Obtain Let's Encrypt SSL certificate via Certbot:
```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d drshafaeiclinic.ir -d www.drshafaeiclinic.ir
```

---

## 7. Service Management Cheatsheet

| Action | Command |
|---|---|
| Restart Web | `sudo systemctl restart psychobot-web.service` |
| Restart Bot | `sudo systemctl restart psychobot-bot.service` |
| Trigger Report Manually | `sudo systemctl start psychobot-report.service` |
| Check Timer Schedule | `sudo systemctl list-timers` |
| View Combined Logs | `sudo journalctl -u psychobot-web -u psychobot-bot -f` |
