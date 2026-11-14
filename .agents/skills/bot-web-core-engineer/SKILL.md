---
name: bot-web-core-engineer
description: >-
  Use for unified domain architecture, Flask web route design, Telegram bot handlers
  refactoring, appointment validation, numeral normalization, background job queues,
  and dual-channel reporting.
---

# `bot-web-core-engineer` (Unified Domain Logic, Flask & Telegram Bot Architect)

## Mission
Eliminate logic drift between Web (`app.py`) and Telegram Bot (`main.py`) layers. Centralize clinic business rules in `config.py`, replace monolithic handlers with modular, single-responsibility callback routers, ensure clean routing in Flask, implement client reminder queues, and maintain dual-channel management reports.

## Core Capabilities & Operational Scope
1. **Centralized Configuration & Constants (`config.py`):**
   - Unify clinic parameters across Web, Bot, and background scripts:
     - `ADMIN_IDS`, `ADMIN_USERNAME`, `ADMIN_PHONE`, `CLINIC_WEBSITE`.
     - `WORKING_HOURS = ["16:00", "17:00", "18:00", "19:00", "20:00"]`.
     - `WORKING_WEEKDAYS = [0, 1, 2, 3, 4]` (Saturday through Wednesday in Jalali).
     - `MIN_ADVANCE_DAYS = 2` (regular users cannot book today or tomorrow; admins bypass).
     - `CANCELLATION_HOURS_LIMIT = 48`.
2. **Unified Booking Validation & Normalization:**
   - Implement `normalize_digits(text)` converting Persian (`۰-۹`) and Arabic (`٠-٩`) numerals to ASCII digits (`0-9`).
   - Validate Iranian mobile numbers strictly matching `^09\d{9}$`.
   - Provide a shared `validate_booking_request(date, time, full_name, phone, is_admin)` invoked identically by `POST /reserve` and the Telegram Bot wizard.
3. **Flask Route Architecture:**
   - Eliminate broken stacked route decorators (e.g. `@app.route('/')` stacked directly over `@app.route('/about') def about():`).
   - Give `home()` its dedicated `@app.route('/')` mapping to `index.html`.
   - Give `about()` its dedicated `@app.route('/about')` mapping to `about.html`.
   - Implement structured error handling, flash messages, and standardized JSON/HTML responses.
4. **Modular Telegram Bot Callback Architecture:**
   - Break down monolithic `button_handler` `if/elif` chains into modular callback handlers registered via pattern matching:
     - `admin_approval_callback`: Dispatched via `pattern=r"^approve_\d+$"`.
     - `admin_rejection_callback`: Dispatched via `pattern=r"^reject_\d+$"`.
     - `user_cancel_callback`: Dispatched via `pattern=r"^user_cancel_\d+$"`.
     - `date_selection_callback`: Dispatched via `pattern=r"^date_"`.
     - `time_selection_callback`: Dispatched via `pattern=r"^time_"`.
     - `type_selection_callback`: Dispatched via `pattern=r"^type_"`.
     - `main_menu_callback`: Dispatched via `pattern=r"^main_menu$"`.
5. **Scheduled Jobs & Dual-Channel Reporting:**
   - Leverage `python-telegram-bot`'s `Application.job_queue` to run repeating background jobs:
     - **24-Hour Client Reminders:** Periodically scans for confirmed appointments occurring within the next 24 hours and dispatches friendly reminder messages to patients, flagging `reminder_sent = 1`.
     - **Automated Expiration:** Cleans up stale pending reservations.
   - Refactor `daily_report.py` to send dual-channel executive digests:
     - Channel 1: Formatted HTML email via Gmail SMTP using credentials from `.env`.
     - Channel 2: Real-time broadcast directly to all Telegram administrators in `ADMIN_IDS`.

## Verification Checklist
- [ ] `config.py` acts as the single source of truth for all business rules and clinic constants.
- [ ] Persian and Arabic numerals normalize accurately before phone and date validation.
- [ ] Both Web and Bot reject booking attempts for today/tomorrow by non-admin users.
- [ ] Flask route decorators are unstacked and bind correctly to distinct handler functions.
- [ ] Telegram callbacks route cleanly to modular handlers without monolithic `if/elif` blocks.
- [ ] Automated appointment reminder job dispatches exactly once per confirmed booking.
- [ ] Daily report dispatches via both SMTP email and Telegram administrative broadcast.
