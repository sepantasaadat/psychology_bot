# Admin Direct Booking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable admin users to book appointments directly, bypassing receipt upload and manual approval while immediately confirming and saving the appointment to the database.

**Architecture:** Add `add_confirmed_appointment` to `database.py` to persist bookings with `status = 'confirmed'`. In `main.py`, check `user_id in ADMIN_IDS` when the full name is submitted in `handle_text`. For admins, save directly, reset session, return confirmation, 7-day schedule, and the main menu; for non-admins, preserve the receipt upload requirement.

**Tech Stack:** Python 3.12, `python-telegram-bot`, `sqlite3`, `jdatetime`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-11-admin-direct-booking-spec.md`

## Global Constraints
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Maintain existing non-admin booking flow without regressions.
- Preserve Persian Jalali date conventions and clinical psychology emojis.
- Clean 4-space indentation and full docstring/comment preservation.

## Review Focus
1. Non-admin booking behavior: Ensure regular users still transition to `awaiting_receipt` and must upload receipts.
2. Admin direct persistence: Ensure appointments booked by admin are created with `status = 'confirmed'` and `receipt_file_id = 'admin_direct'`.
3. Session reset for admin: Ensure `context.user_data` is cleared immediately after direct booking.
4. Schedule and menu dispatch: Verify the acting admin receives confirmation details, 7-day schedule, and main menu.
5. Missing temporary session data: Handle safe retrieval of date/time/session_type from user_data.

---

### Task 1: Add `add_confirmed_appointment` Helper to Database

**Files:**
- Modify: `database.py:55-65`
- Test: `tests/test_database.py`

**Interfaces:**
- Produces: `add_confirmed_appointment(user_id, date, time, session_type, full_name, receipt_file_id='admin_direct') -> int` returning the new appointment id.

- [ ] **Step 1: Write failing test in `tests/test_database.py`**

Add `test_add_confirmed_appointment` to `tests/test_database.py` asserting:
- Returns integer appointment id.
- Appointment row in DB has `status = 'confirmed'` and `receipt_file_id = 'admin_direct'`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_database.py -v`
Expected: FAIL with `AttributeError: module 'database' has no attribute 'add_confirmed_appointment'`

- [ ] **Step 3: Implement `add_confirmed_appointment` in `database.py`**

```python
def add_confirmed_appointment(user_id, date, time, session_type, full_name, receipt_file_id='admin_direct'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
        VALUES (?, ?, ?, ?, ?, 'confirmed', ?)
    ''', (user_id, date, time, session_type, full_name, receipt_file_id))
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return appointment_id
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_database.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat(database): add add_confirmed_appointment helper for direct bookings"
```

---

### Task 2: Implement Admin Direct Booking Flow in `handle_text`

**Files:**
- Modify: `main.py:320-360`
- Test: `tests/test_admin_direct_booking.py`

**Interfaces:**
- Consumes: `database.add_confirmed_appointment`, `ADMIN_IDS`, `format_upcoming_week_appointments`, `get_main_menu_keyboard`
- Updates: `handle_text` when `state == 'awaiting_name'` to differentiate admin vs regular users.

- [ ] **Step 1: Write failing tests in `tests/test_admin_direct_booking.py`**

Create `tests/test_admin_direct_booking.py` with two test cases:
1. `test_admin_booking_bypasses_receipt_and_confirms`: Admin submits name -> appointment is saved as confirmed, receipt skipped, confirmation + schedule + main menu sent, session cleared.
2. `test_regular_user_booking_requires_receipt`: Regular user submits name -> state becomes `awaiting_receipt`, receipt request message sent.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_admin_direct_booking.py -v`
Expected: FAIL

- [ ] **Step 3: Implement admin branch in `handle_text` in `main.py`**

In `main.py`:
When `context.user_data.get('state') == 'awaiting_name'`:
```python
        full_name = update.message.text.strip()
        user_id = update.effective_user.id
        
        # اگر کاربر در لیست ادمین‌ها باشد، فیش پرداخت و تایید ادمین بایپس شده و نوبت مستقیماً تایید می‌شود
        if user_id in ADMIN_IDS:
            date = context.user_data.get('selected_date')
            time = context.user_data.get('selected_time')
            session_type = context.user_data.get('session_type')
            
            user = update.effective_user
            database.add_user(user.id, user.first_name, user.username)
            appointment_id = database.add_confirmed_appointment(
                user_id=user.id,
                date=date,
                time=time,
                session_type=session_type,
                full_name=full_name,
                receipt_file_id="admin_direct"
            )
            
            context.user_data.clear()
            
            confirm_msg = (
                "✅ وقت مشاوره با موفقیت به‌صورت مستقیم ثبت قطعی شد. 🌱\n\n"
                "📋 مشخصات نوبت ثبت‌شده:\n"
                f"👤 نام مراجع: {full_name}\n"
                f"📅 تاریخ جلسه: {date}\n"
                f"⏰ ساعت جلسه: {time}\n"
                f"🩺 نوع جلسه: {session_type}\n"
                f"🆔 کد پیگیری: #{appointment_id}"
            )
            await update.message.reply_text(confirm_msg)
            
            # ارسال گزارش نوبت‌های هفتگی و منوی اصلی
            weekly_schedule = format_upcoming_week_appointments()
            await update.message.reply_text(weekly_schedule)
            await update.message.reply_text(
                "منوی اصلی پذیرش و مدیریت کلینیک: 🌿",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_admin_direct_booking.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_admin_direct_booking.py
git commit -m "feat(bot): implement specialized direct booking flow for admins"
```

---

### Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

- [ ] **Step 1: Run all unit tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover tests -v`
Expected: All tests pass.

- [ ] **Step 2: Verify Python compilation**

Run: `.\.venv\Scripts\python.exe -m py_compile main.py database.py app.py`
Expected: 0 errors.

- [ ] **Step 3: Update knowledge graph**

Run: `.\.venv\Scripts\graphify.exe update .`

- [ ] **Step 4: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 5: Provide VPS deployment instructions to the user**
