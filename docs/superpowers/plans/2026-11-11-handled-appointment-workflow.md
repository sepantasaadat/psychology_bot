# Handled Appointment Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure admins who click an already-handled appointment receive the 7-day clinic schedule and are redirected to the main menu with a reset session.

**Architecture:** Extract `complete_admin_review_session` helper in `main.py` to encapsulate session clearing, 7-day schedule delivery, and admin main menu transmission. Use this helper across approve, reject, and the already-handled callback branches.

**Tech Stack:** Python 3.12, `python-telegram-bot`, `sqlite3`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-11-handled-appointment-workflow-spec.md`

## Global Constraints
- Persian clinical tone.
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Clean 4-space indentation and full docstring/comment preservation.

## Review Focus
1. Already-handled detection: Ensure `current_status != "pending"` removes inline buttons (`reply_markup=None`).
2. Schedule delivery: Ensure the 7-day schedule message is delivered to the exact admin who triggered the callback.
3. Session reset: Ensure `context.user_data` is cleared.
4. Main menu restoration: Ensure the admin menu with administrative buttons (`admin_panel`) is delivered.
5. No side-effect on database: Ensure already-handled appointments are not modified in SQLite.

---

### Task 1: Extract `complete_admin_review_session` and Update Already-Handled Branch

**Files:**
- Modify: `main.py:405-485`
- Test: `tests/test_admin_workflow.py`

**Interfaces:**
- Produces: `complete_admin_review_session(query, context, user_id) -> None`
- Consumes: `format_upcoming_week_appointments()`, `get_main_menu_keyboard(user_id)`

- [ ] **Step 1: Write failing test in `tests/test_admin_workflow.py`**

Test:
- `test_already_handled_appointment_triggers_schedule_and_menu`:
  - Create appointment with status `confirmed`.
  - Call `button_handler` with `query.data = f"approve_{app_id}"` from admin.
  - Assert `query.edit_message_caption` called with handled notice and `reply_markup=None`.
  - Assert `context.user_data.clear` called (or dict empty).
  - Assert `context.bot.send_message` called twice (once for schedule, once for main menu).
  - Assert database status remains `confirmed`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_admin_workflow.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `complete_admin_review_session` and update `main.py`**

```python
async def complete_admin_review_session(query, context, user_id):
    context.user_data.clear()
    weekly_schedule = format_upcoming_week_appointments()
    await context.bot.send_message(chat_id=query.message.chat_id, text=weekly_schedule)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="منوی اصلی پذیرش و مدیریت کلینیک: 🌿",
        reply_markup=get_main_menu_keyboard(user_id)
    )
```
In `button_handler`:
```python
        # جلوگیری از تداخل دو ادمین: اگر قبلاً تایید/رد شده، دیگر کاری نکن
        if current_status != "pending":
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n⚠️ این نوبت قبلاً توسط ادمین دیگری تعیین تکلیف شده است.",
                reply_markup=None
            )
            await complete_admin_review_session(query, context, user_id)
            return
```
And replace the trailing duplicate block in `approve` / `reject` with `await complete_admin_review_session(query, context, user_id)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_admin_workflow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_admin_workflow.py
git commit -m "feat(admin): send weekly schedule and menu when appointment already handled"
```

---

### Task 2: Full Verification, Knowledge Graph Update, and Push to GitHub

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
