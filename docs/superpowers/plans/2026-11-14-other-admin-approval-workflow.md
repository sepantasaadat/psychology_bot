# Other Admin Approval Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete obsolete receipt messages for other administrators and dispatch the updated 7-day schedule plus main menu when one administrator approves a booking.

**Architecture:** Create an `admin_receipt_messages` table in `database.py` to record `(appointment_id, admin_id, message_id)`. In `main.py`, record sent message IDs in `handle_receipt`. Upon approval in `button_handler`, delete other administrators' receipt messages via `context.bot.delete_message`, dispatch the updated 7-day schedule, and restore the main menu.

**Tech Stack:** Python 3.12, `python-telegram-bot`, `sqlite3`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-14-other-admin-approval-workflow-spec.md`

## Global Constraints
- Persian clinical tone.
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Clean 4-space indentation and full docstring/comment preservation.

## Review Focus
1. Message tracking: Ensure `save_admin_receipt_message` records the message ID for each administrator in `ADMIN_IDS`.
2. Acting admin isolation: Ensure the approving administrator's receipt message is NOT deleted, but edited to show confirmed status.
3. Other admin cleanup: Ensure `context.bot.delete_message` is called for other administrators who received the receipt.
4. Payload correctness: Ensure other administrators receive only the 7-day schedule message followed by the main menu message (no extraneous alert).
5. Database hygiene: Ensure records in `admin_receipt_messages` are cleared after processing.

---

### Task 1: Add `admin_receipt_messages` Table and Database Helpers

**Files:**
- Modify: `database.py:15-35`, `database.py:145-155`
- Test: `tests/test_database.py`

**Interfaces:**
- Produces:
  - `save_admin_receipt_message(appointment_id: int, admin_id: int, message_id: int) -> None`
  - `get_admin_receipt_messages(appointment_id: int) -> list[tuple[int, int]]`
  - `delete_admin_receipt_messages(appointment_id: int) -> None`

- [ ] **Step 1: Write failing tests in `tests/test_database.py`**

Test:
- `test_admin_receipt_messages_crud`:
  - Call `save_admin_receipt_message(10, 101, 501)` and `save_admin_receipt_message(10, 102, 502)`.
  - Assert `get_admin_receipt_messages(10)` returns `[(101, 501), (102, 502)]`.
  - Call `delete_admin_receipt_messages(10)`.
  - Assert `get_admin_receipt_messages(10)` returns `[]`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_database.py -v`
Expected: FAIL

- [ ] **Step 3: Implement table and helper functions in `database.py`**

In `setup_database`:
```python
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_receipt_messages (
            appointment_id INTEGER,
            admin_id INTEGER,
            message_id INTEGER,
            PRIMARY KEY (appointment_id, admin_id)
        )
    ''')
```
Functions:
```python
def save_admin_receipt_message(appointment_id, admin_id, message_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO admin_receipt_messages (appointment_id, admin_id, message_id)
        VALUES (?, ?, ?)
    ''', (appointment_id, admin_id, message_id))
    conn.commit()
    conn.close()

def get_admin_receipt_messages(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT admin_id, message_id
        FROM admin_receipt_messages
        WHERE appointment_id = ?
    ''', (appointment_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_admin_receipt_messages(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admin_receipt_messages WHERE appointment_id = ?', (appointment_id,))
    conn.commit()
    conn.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_database.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat(database): add admin_receipt_messages table and helpers"
```

---

### Task 2: Track Receipt Messages and Implement Other Admin Cleanup on Approval

**Files:**
- Modify: `main.py:620-635`, `main.py:440-475`
- Test: `tests/test_admin_workflow.py`

**Interfaces:**
- Consumes: `database.save_admin_receipt_message`, `database.get_admin_receipt_messages`, `database.delete_admin_receipt_messages`, `format_upcoming_week_appointments`, `get_main_menu_keyboard`

- [ ] **Step 1: Write failing integration test in `tests/test_admin_workflow.py`**

Test:
- `test_approval_deletes_receipt_and_notifies_other_admins`:
  - Create pending appointment `app_id`.
  - Save receipt message IDs for admin 1 (`MAIN_ADMIN_ID`, msg_id 1001) and admin 2 (`SECOND_ADMIN_ID`, msg_id 1002).
  - Simulate approval by admin 1 (`user_id = MAIN_ADMIN_ID`).
  - Verify `context.bot.delete_message` called for admin 2 with `chat_id = SECOND_ADMIN_ID` and `message_id = 1002`.
  - Verify `context.bot.delete_message` was NOT called for admin 1 (`MAIN_ADMIN_ID`).
  - Verify admin 2 received 7-day schedule and main menu.
  - Verify `database.get_admin_receipt_messages(app_id)` is now empty.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_admin_workflow.py -v`
Expected: FAIL

- [ ] **Step 3: Implement message tracking in `handle_receipt` and other admin cleanup in `button_handler`**

In `handle_receipt`:
```python
    for admin in ADMIN_IDS:
        try:
            sent_msg = await context.bot.send_photo(
                chat_id=admin,
                photo=photo_file_id,
                caption=caption,
                reply_markup=reply_markup
            )
            database.save_admin_receipt_message(appointment_id, admin, sent_msg.message_id)
        except Exception as e:
            logger.error(f"Error sending receipt to admin {admin}: {e}")
```

In `button_handler` under `if action == "approve":`:
```python
            # حذف پیام رسید و دکمه‌ها برای سایر ادمین‌ها و ارسال برنامه به‌روزشده هفتگی + منوی اصلی
            other_receipt_msgs = database.get_admin_receipt_messages(appointment_id)
            weekly_schedule_text = format_upcoming_week_appointments()
            for admin_id, msg_id in other_receipt_msgs:
                if admin_id != user_id:
                    try:
                        await context.bot.delete_message(chat_id=admin_id, message_id=msg_id)
                    except Exception as e:
                        logger.error(f"Error deleting receipt message for admin {admin_id}: {e}")
                    
                    try:
                        await context.bot.send_message(chat_id=admin_id, text=weekly_schedule_text)
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text="منوی اصلی پذیرش و مدیریت کلینیک: 🌿",
                            reply_markup=get_main_menu_keyboard(admin_id)
                        )
                    except Exception as e:
                        logger.error(f"Error sending schedule/menu to admin {admin_id}: {e}")
            
            database.delete_admin_receipt_messages(appointment_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_admin_workflow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_admin_workflow.py
git commit -m "feat(admin): delete receipt and send schedule to other admins upon approval"
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
