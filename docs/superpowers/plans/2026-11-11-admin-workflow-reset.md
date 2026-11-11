# Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reset the admin's session and display both the 7-day upcoming confirmed appointment schedule and the main menu immediately after an admin approves or rejects a payment receipt.

**Architecture:** Add a date-range appointment query function to `database.py` to fetch confirmed appointments for the next 7 days. In `main.py`, create a reporting helper to format the 7-day schedule, update the `approve` and `reject` branches to clear the receipt's inline keyboard, clear `context.user_data`, send the report, and redirect the admin to the main menu.

**Tech Stack:** Python 3.12, `python-telegram-bot`, `sqlite3`, `jdatetime`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-11-admin-workflow-reset-design.md`

## Global Constraints
- Persian Jalali calendar formatting (`YYYY/MM/DD`) must be preserved.
- Year 1405 base-date convention (`if current_date.year < 1405: current_date = jdatetime.date(1405, 1, 1)`) must be respected so appointments work consistently across simulated and actual dates.
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Clean 4-space indentation and full docstring/comment preservation.

## Review Focus
1. Empty schedule in the next 7 days: Verify friendly fallback message is returned when no appointments are booked.
2. Appointments outside the 7-day window: Verify appointments prior to start date or after day 7 are excluded.
3. Multi-admin conflict safety: Verify second admin clicking after a decision does not trigger double-reset or error.
4. Button deactivation: Verify the receipt inline buttons are disabled/cleared after decision.
5. Session clearance: Verify `context.user_data` is completely cleared so the admin starts from root state.

---

### Task 1: Add Weekly Confirmed Appointments Query to Database

**Files:**
- Modify: `database.py:90-105`
- Test: `tests/test_database.py`

**Interfaces:**
- Produces: `get_upcoming_week_confirmed_appointments(start_date_str: str, end_date_str: str) -> list[tuple]` returning `[(id, date, time, full_name, session_type), ...]` ordered by `date, time`.

- [ ] **Step 1: Write the failing test for `get_upcoming_week_confirmed_appointments`**

Create `tests/test_database.py` testing:
- Empty result when no appointments exist.
- Returns only appointments with `status = 'confirmed'`.
- Filters between `start_date_str` and `end_date_str` inclusive.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_database.py -v`
Expected: FAIL with `AttributeError: module 'database' has no attribute 'get_upcoming_week_confirmed_appointments'`

- [ ] **Step 3: Implement `get_upcoming_week_confirmed_appointments` in `database.py`**

Add the function to `database.py`:
```python
def get_upcoming_week_confirmed_appointments(start_date_str, end_date_str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, date, time, full_name, session_type 
        FROM appointments 
        WHERE status = 'confirmed' 
          AND date >= ? 
          AND date <= ?
        ORDER BY date, time
    ''', (start_date_str, end_date_str))
    rows = cursor.fetchall()
    conn.close()
    return rows
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_database.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat(database): add get_upcoming_week_confirmed_appointments query"
```

---

### Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`

**Files:**
- Modify: `main.py:50-70`, `main.py:220-290`
- Test: `tests/test_admin_workflow.py`

**Interfaces:**
- Consumes: `database.get_upcoming_week_confirmed_appointments(start_date, end_date)`
- Produces: `format_upcoming_week_appointments(reference_date=None) -> str`
- Updates: `button_handler` approve/reject callback actions to clear receipt buttons, send report, reset user session, and send main menu.

- [ ] **Step 1: Write failing test for `format_upcoming_week_appointments`**

Create `tests/test_admin_workflow.py` testing:
- Returns "در ۷ روز آینده هیچ نوبت قطعی ثبت نشده است." when empty.
- Returns formatted lines with date, time, full name, and session type when appointments exist.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_admin_workflow.py -v`
Expected: FAIL with `ImportError` or `AttributeError`

- [ ] **Step 3: Implement `format_upcoming_week_appointments` and update `button_handler` in `main.py`**

In `main.py`:
1. Add `format_upcoming_week_appointments(reference_date=None)`:
   - Compute start date using `reference_date` or `jdatetime.date.today()`, with `if current_date.year < 1405: current_date = jdatetime.date(1405, 1, 1)`.
   - Compute end date: `start_date + jdatetime.timedelta(days=6)`.
   - Query `database.get_upcoming_week_confirmed_appointments(start_str, end_str)`.
   - Format response with clinical emoji and layout without raw asterisks.
2. In `button_handler` inside `if action == "approve":` and `elif action == "reject":`:
   - Edit photo reply markup: `await query.edit_message_reply_markup(reply_markup=None)`
   - Clear admin session: `context.user_data.clear()`
   - Generate schedule: `schedule_text = format_upcoming_week_appointments()`
   - Send schedule to admin: `await context.bot.send_message(chat_id=query.message.chat_id, text=schedule_text)`
   - Send main menu to admin: `await context.bot.send_message(chat_id=query.message.chat_id, text="بازگشت به منوی اصلی:", reply_markup=get_main_menu_keyboard(user_id))`

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_admin_workflow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_admin_workflow.py
git commit -m "feat(bot): add weekly schedule report and reset admin session after receipt decision"
```

---

### Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

**Files:**
- Modify: `graphify-out/`

- [ ] **Step 1: Run all unit tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover tests -v`
Expected: All tests pass.

- [ ] **Step 2: Verify Python syntax compilation**

Run: `.\.venv\Scripts\python.exe -m py_compile main.py database.py app.py`
Expected: 0 errors.

- [ ] **Step 3: Update knowledge graph**

Run: `.\.venv\Scripts\graphify.exe update .`
Expected: Updated nodes and edges in `graphify-out/`.

- [ ] **Step 4: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 5: Provide VPS deployment instructions to the user**
