# User Appointment Cancellation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow regular clients to view dynamic cancellation buttons for their confirmed weekly bookings in the main menu and cancel them directly, deleting the booking and notifying admins with main menu redirect.

**Architecture:** Add `get_user_confirmed_appointments_for_week` to `database.py`. In `main.py`, dynamically inject cancellation buttons into `get_main_menu_keyboard` for regular users who have confirmed appointments in the upcoming 7-day window. In `button_handler`, handle `user_cancel_<id>` by deleting the booking from the database, confirming to the user, sending an alert to all `ADMIN_IDS`, and delivering the main menu to each admin.

**Tech Stack:** Python 3.12, `python-telegram-bot`, `sqlite3`, `jdatetime`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-11-user-cancellation-spec.md`

## Global Constraints
- Admin IDs must NEVER see these dynamic cancellation buttons in their main menu.
- Non-admin users must only see buttons for their OWN confirmed appointments.
- Appointments outside the upcoming 7-day window must not produce cancellation buttons.
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Clean 4-space indentation and full docstring/comment preservation.

## Review Focus
1. Role isolation: Verify admins (`user_id in ADMIN_IDS`) never see cancellation buttons on their main menu.
2. User isolation: Verify user A cannot see or cancel user B's appointments.
3. Multiple bookings: Verify each confirmed booking for the week produces a separate button with date and time.
4. Database deletion: Verify the appointment is deleted immediately from `clinic.db`.
5. Admin alert and return to menu: Verify every admin receives the cancellation alert followed by their main menu.

---

### Task 1: Add User Weekly Confirmed Appointments Query to Database

**Files:**
- Modify: `database.py:95-115`
- Test: `tests/test_database.py`

**Interfaces:**
- Produces: `get_user_confirmed_appointments_for_week(user_id: int, start_date_str: str, end_date_str: str) -> list[tuple]`

- [ ] **Step 1: Write failing test in `tests/test_database.py`**

Add `test_get_user_confirmed_appointments_for_week` to `tests/test_database.py` asserting:
- Returns only appointments belonging to the specified `user_id`.
- Returns only `status = 'confirmed'`.
- Returns only dates within `[start_date_str, end_date_str]`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_database.py -v`
Expected: FAIL with `AttributeError: module 'database' has no attribute 'get_user_confirmed_appointments_for_week'`

- [ ] **Step 3: Implement `get_user_confirmed_appointments_for_week` in `database.py`**

```python
def get_user_confirmed_appointments_for_week(user_id, start_date_str, end_date_str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, date, time, full_name, session_type 
        FROM appointments 
        WHERE user_id = ? 
          AND status = 'confirmed' 
          AND date >= ? 
          AND date <= ?
        ORDER BY date, time
    ''', (user_id, start_date_str, end_date_str))
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
git commit -m "feat(database): add get_user_confirmed_appointments_for_week helper"
```

---

### Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py`

**Files:**
- Modify: `main.py:75-100`, `main.py:150-180`
- Test: `tests/test_user_cancellation.py`

**Interfaces:**
- Consumes: `database.get_user_confirmed_appointments_for_week`, `database.delete_appointment`, `database.get_appointment`
- Updates: `get_main_menu_keyboard(user_id)` to append `user_cancel_<id>` buttons for regular users.
- Updates: `button_handler` to process `user_cancel_<id>`.

- [ ] **Step 1: Write failing tests in `tests/test_user_cancellation.py`**

Create `tests/test_user_cancellation.py` testing:
1. `test_admin_menu_has_no_user_cancel_buttons`: Admin menu does not contain `user_cancel_` buttons even if admin has confirmed bookings.
2. `test_user_menu_contains_dynamic_cancel_buttons`: Regular user with 2 bookings gets 2 cancellation buttons displaying date and time.
3. `test_user_cancel_callback_deletes_record_and_notifies_admins`: Clicking cancel deletes the appointment from DB, updates user message, sends alert to all `ADMIN_IDS`, and sends main menu to each admin.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_user_cancellation.py -v`
Expected: FAIL

- [ ] **Step 3: Implement dynamic buttons and `user_cancel_` handler in `main.py`**

1. In `get_main_menu_keyboard(user_id)`:
   - If `user_id not in ADMIN_IDS`:
     - Determine 7-day range from `today` (`start_date` to `start_date + 6 days`).
     - Query `database.get_user_confirmed_appointments_for_week(user_id, start_str, end_str)`.
     - For each `(app_id, d, t, name, stype)`:
       `keyboard.append([InlineKeyboardButton(f"❌ لغو نوبت: {d} ساعت {t}", callback_data=f"user_cancel_{app_id}")])`
2. In `button_handler`:
   - Handle `query.data.startswith("user_cancel_")`:
     - Extract `app_id`.
     - Fetch appointment details via `database.get_appointment(app_id)`.
     - If exists:
       - Call `database.delete_appointment(app_id)`.
       - Edit user message with confirmation:
         `"✅ نوبت مشاوره شما با موفقیت لغو شد و ساعت آن آزاد گردید. 🌱\nجهت انتخاب نوبت جدید می‌توانید از منوی زیر استفاده فرمایید:"`
         and `reply_markup=get_main_menu_keyboard(user_id)`.
       - For each `admin in ADMIN_IDS`:
         Send cancellation alert:
         `"⚠️ گزارش لغو نوبت توسط مراجع:\n\n👤 نام مراجع: {name}\n📅 تاریخ جلسه: {date}\n⏰ ساعت جلسه: {time}\n🩺 نوع جلسه: {s_type}\n🆔 شناسه نوبت: #{app_id}"`
         Send main menu to admin:
         `"منوی اصلی پذیرش و مدیریت کلینیک: 🌿"` with `reply_markup=get_main_menu_keyboard(admin)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_user_cancellation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_user_cancellation.py
git commit -m "feat(bot): add dynamic appointment cancellation feature for regular users"
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
