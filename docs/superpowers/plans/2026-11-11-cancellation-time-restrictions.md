# Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce a 48-hour cancellation policy for regular users and automatically remove cancellation buttons once appointment times have passed.

**Architecture:** Create datetime parsing and cancellation policy evaluation helpers in `main.py`. Filter out past appointments in `get_main_menu_keyboard` so expired buttons disappear. In `button_handler`, enforce the 48-hour rule, denying cancellations with an explanatory apology when under 48 hours, and processing cancellations only when 48 or more hours remain.

**Tech Stack:** Python 3.12, `python-telegram-bot`, `jdatetime`, `sqlite3`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-11-cancellation-time-restrictions-spec.md`

## Global Constraints
- Persian Jalali calendar parsing must strictly match `YYYY/MM/DD` and `HH:MM`.
- Year 1405 base-date convention must be supported.
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Clean 4-space indentation and full docstring/comment preservation.

## Review Focus
1. Exact 48-hour boundary: Verify appointment exactly 48.0 hours away can be canceled.
2. Less than 48 hours (e.g. 47.9 hours): Verify appointment cancellation is denied, DB record is not deleted, admins are not alerted.
3. Expired appointment (in the past): Verify button is not rendered in main menu; if clicked, denied without error.
4. Over 48 hours (e.g. 72 hours): Verify appointment cancellation succeeds, DB record deleted, admins alerted with main menu.
5. Role exclusion: Verify admins still do not see these dynamic cancellation buttons.

---

### Task 1: Add Datetime Parsing and Cancellation Eligibility Helper

**Files:**
- Modify: `main.py:45-75`
- Test: `tests/test_cancellation_policy.py`

**Interfaces:**
- Produces:
  - `parse_appointment_datetime(date_str: str, time_str: str) -> jdatetime.datetime`
  - `get_current_jalali_datetime(now=None) -> jdatetime.datetime`
  - `can_cancel_appointment(date_str: str, time_str: str, now=None) -> tuple[bool, str]` returning `(True, "ok")`, `(False, "expired")`, or `(False, "within_48_hours")`.

- [ ] **Step 1: Write failing tests in `tests/test_cancellation_policy.py`**

Test:
- `parse_appointment_datetime` converts `"1405/08/25"`, `"18:00"` to `jdatetime.datetime(1405, 8, 25, 18, 0)`.
- `can_cancel_appointment` with `now = 1405/08/20 18:00`:
  - `1405/08/23 18:00` (72 hrs away) -> `(True, "ok")`
  - `1405/08/22 18:00` (exactly 48 hrs away) -> `(True, "ok")`
  - `1405/08/22 17:00` (47 hrs away) -> `(False, "within_48_hours")`
  - `1405/08/19 18:00` (past) -> `(False, "expired")`

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_cancellation_policy.py -v`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Implement helpers in `main.py`**

Add `parse_appointment_datetime`, `get_current_jalali_datetime`, and `can_cancel_appointment` in `main.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_cancellation_policy.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_cancellation_policy.py
git commit -m "feat(bot): add appointment datetime parser and 48-hour eligibility helper"
```

---

### Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback

**Files:**
- Modify: `main.py:90-130`, `main.py:190-230`
- Test: `tests/test_cancellation_policy.py`

**Interfaces:**
- Updates: `get_main_menu_keyboard(user_id)` to filter out appointments where `parse_appointment_datetime(d, t) <= get_current_jalali_datetime()`.
- Updates: `button_handler` under `user_cancel_<id>` to check `can_cancel_appointment(date, time)`.

- [ ] **Step 1: Write failing tests in `tests/test_cancellation_policy.py`**

Add tests:
- `test_expired_appointment_buttons_not_rendered`: Past appointments do not generate buttons in `get_main_menu_keyboard`.
- `test_cancel_within_48_hours_denied_without_db_change_or_admin_alert`: When < 48 hours remain, apology message is returned, appointment remains in DB, no admin alert sent.
- `test_cancel_over_48_hours_succeeds`: When >= 48 hours remain, appointment deleted from DB, confirmation returned, admins alerted.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_cancellation_policy.py -v`
Expected: FAIL

- [ ] **Step 3: Implement button filtering and cancellation policy handling in `main.py`**

1. In `get_main_menu_keyboard(user_id)`:
   - For regular users, before adding each `user_cancel_<app_id>` button, check:
     `if parse_appointment_datetime(d, t) > get_current_jalali_datetime():`
     Only append buttons for future appointments.
2. In `button_handler` under `query.data.startswith("user_cancel_")`:
   - Check `eligible, reason = can_cancel_appointment(date, time)`.
   - If not eligible and `reason == "expired"`:
     `"⚠️ زمان این نوبت مشاوره سپری شده است و امکان لغو آن وجود ندارد."`
     Refresh menu, return.
   - If not eligible and `reason == "within_48_hours"`:
     `"⚠️ مراجع ارجمند؛\nطبق قوانین کلینیک، لغو نوبت مشاوره حداکثر تا ۴۸ ساعت پیش از موعد جلسه امکان‌پذیر می‌باشد.\nبا توجه به اینکه کمتر از ۴۸ ساعت تا زمان جلسه شما باقی مانده است، امکان لغو خودکار از طریق سامانه وجود ندارد.\nدر صورت بروز شرایط اضطراری یا نیاز به هماهنگی، لطفاً مستقیماً با پذیرش کلینیک تماس حاصل فرمایید. 🌱"`
     Refresh menu, return.
   - If eligible:
     Proceed with deletion, user confirmation, admin notification, and admin menu delivery.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_cancellation_policy.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_cancellation_policy.py
git commit -m "feat(bot): enforce 48-hour cancellation policy and automatic expiration of past buttons"
```

---

### Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

- [ ] **Step 1: Run all unit tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover tests -v`
Expected: All tests pass.

- [ ] **Step 2: Verify Python compilation**

Run: `.\.venv\Scripts\python.exe -m py_compile main.py database.py app.py`

- [ ] **Step 3: Update knowledge graph**

Run: `.\.venv\Scripts\graphify.exe update .`

- [ ] **Step 4: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 5: Provide VPS deployment instructions to the user**
