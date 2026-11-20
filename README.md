# Psychology Clinic Bot and Web Reservation System

Production-grade hybrid Telegram Bot and Flask web booking application for Dr. Shafaei's Psychological Clinic, backed by an ACID-compliant SQLite WAL database and automated dual-channel reporting.

## System Architecture

The application is structured into decoupled components sharing a single local SQLite database (`clinic.db`) in WAL mode:

- **Flask Web Portal (`app.py`)**: Patient-facing booking portal with CSRF protection, rate limiting, and private receipt upload validation via Pillow.
- **Telegram Bot Daemon (`main.py`)**: Multi-role Telegram bot using `python-telegram-bot` v21+, with modular callback query handlers, administrative appointment approvals/rejections, user cancellation rules, and a 24-hour appointment reminder background job.
- **Automated Dual-Channel Reporter (`daily_report.py`)**: Nightly scheduler service generating upcoming 7-day appointment agendas and dispatching them simultaneously via SMTP HTML email and Telegram admin broadcast.
- **Database Engine (`database.py`)**: SQLite with `PRAGMA journal_mode=WAL`, `busy_timeout=30000`, `foreign_keys=ON`, and partial unique indexing (`idx_appointments_active_slot`) preventing double-booking race conditions across processes.
- **Shared Configuration & Jalali Logic (`config.py`)**: Centralized Iranian calendar math using `jdatetime` and `ZoneInfo("Asia/Tehran")`, rolling-window working days across Nowruz boundaries, numeral normalization, and validation rules.

---

## Security and Privacy Guardrails

1. **Zero-PII Logging**:
   - Patient names, phone numbers, and conversational bodies are excluded from application logs.
   - Logs track only non-sensitive metadata (`user_id`, `message_id`, callback action types).
   - Upstream HTTP and library loggers (`httpx`, `telegram`, `werkzeug`) are set to `WARNING` to prevent token leakage in query strings.

2. **Secure File Upload Pipeline**:
   - Web receipt uploads are stored outside the web root in `private_uploads/`.
   - Filenames are generated as random UUID4 hex hashes (`<uuid4>.jpg`) to prevent collisions or user-controlled path traversal.
   - Files are validated by inspecting binary headers with Pillow (`Image.open().verify()`) and restricted to `JPEG`, `PNG`, and `WEBP`. Non-image or spoofed files are rejected with HTTP 400.
   - Maximum upload payload is capped at 5 MB (`MAX_CONTENT_LENGTH = 5 * 1024 * 1024`).

3. **Strict RBAC and Ownership Checks**:
   - Administrative actions (`approve_`, `reject_`, `del_`) are restricted to `ADMIN_IDS`.
   - Patient cancellations (`user_cancel_`) enforce ownership: users can only cancel their own appointments, and only if greater than 48 hours remain before the scheduled session.

---

## Leaked Secret Remediation with git-filter-repo

If historical commits contain exposed credentials (such as an SMTP App Password), rewrite git history locally before pushing with `git-filter-repo`:

```bash
# 1. Install git-filter-repo
pip install git-filter-repo

# 2. Create expressions file with string to redact
echo "OLD_GMAIL_APP_PASSWORD==>REDACTED_PASSWORD" > replace.txt

# 3. Run git-filter-repo across all commits and branches
git filter-repo --replace-text replace.txt --force

# 4. Re-link remote origin and force-push clean history
git remote add origin https://github.com/sepantasaadat/psychology_bot.git
git push origin --force --all
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure appropriate values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `BOT_TOKEN` | Telegram Bot API token from @BotFather | *Required in production* |
| `FLASK_SECRET_KEY` | Cryptographic secret for session cookies and CSRF | *Auto-generated if unset* |
| `FLASK_DEBUG` | Enable Flask debug mode (`1` or `0`) | `0` |
| `ADMIN_IDS` | Comma-separated administrative Telegram user IDs | `56073956,8034655716,95033750` |
| `ADMIN_PHONE` | Clinic reception phone number | `09213689461` |
| `ADMIN_USERNAME` | Clinic reception Telegram handle | `drshafaei_psychological_clinic` |
| `CLINIC_WEBSITE` | Official clinic website URL | `https://drshafaeiclinic.ir/` |
| `CARD_NUMBER` | Bank card number for consultation fees | `5894631804709814` |
| `SMTP_SERVER` | SMTP host for daily report emails | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_EMAIL` / `SENDER_EMAIL` | Sender email address | *Required for email reports* |
| `SMTP_PASSWORD` / `SENDER_PASSWORD` | Google App Password for SMTP | *Required for email reports* |
| `REPORT_RECIPIENT_EMAIL` / `RECEIVER_EMAIL` | Recipient email address | *Required for email reports* |
| `DB_PATH` | Path to SQLite database file | `<project_root>/clinic.db` |
| `PRIVATE_UPLOADS_DIR` | Private directory for uploaded payment receipts | `<project_root>/private_uploads` |

---

## VPS Deployment (Systemd Services)

Production deployment templates are located in `deploy/systemd/`:

1. `deploy/systemd/psychobot-web.service`: Gunicorn WSGI server for Flask.
2. `deploy/systemd/psychobot-bot.service`: Long-polling daemon for the Telegram bot.
3. `deploy/systemd/psychobot-report.service`: One-shot execution of `daily_report.py`.
4. `deploy/systemd/psychobot-report.timer`: Daily timer triggering at 21:00 Asia/Tehran.

### Service Installation

```bash
# Copy unit files to systemd directory
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo cp deploy/systemd/*.timer /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable --now psychobot-web.service
sudo systemctl enable --now psychobot-bot.service
sudo systemctl enable --now psychobot-report.timer

# Check status
sudo systemctl status psychobot-web psychobot-bot psychobot-report.timer
```

---

## Docker Deployment

To build and run all services using Docker Compose:

```bash
# Build and start services in background
docker compose up -d --build

# View container logs
docker compose logs -f
```

---

## Testing & Quality Assurance

Run the test suite locally with `pytest`:

```bash
# Run all unit and integration tests with verbose output
pytest -v

# Run specific test modules
pytest tests/test_database.py -v
pytest tests/test_bot_handlers.py -v
pytest tests/test_web_routes.py -v
pytest tests/test_concurrency.py -v
pytest tests/test_security.py -v
```
