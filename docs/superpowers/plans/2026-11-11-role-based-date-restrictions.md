# Role-Based Booking Date Restrictions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent regular users from booking appointment slots for today and tomorrow while maintaining unrestricted same-day and next-day booking access for admins.

**Architecture:** Extend `get_upcoming_days` in `main.py` with an `is_admin` parameter and offset calculation. In `button_handler`, pass `is_admin` when building the date selection keyboard, and guard the `date_` callback to reject unauthorized same-day or next-day attempts from non-admins.

**Tech Stack:** Python 3.12, `python-telegram-bot`, `jdatetime`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-11-role-based-date-restrictions-spec.md`

## Global Constraints
- Persian Jalali date formatting (`YYYY/MM/DD`) and week days (Saturday through Wednesday working days).
- Year 1405 base-date convention.
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Clean 4-space indentation and full docstring/comment preservation.

## Review Focus
1. Non-admin date filtering: Ensure neither today nor tomorrow appears in the regular user's date keyboard.
2. Admin date availability: Ensure today and tomorrow are included for admins when they are working days.
3. Callback tampering prevention: Ensure a direct `date_<today>` callback from a non-admin is blocked with an informative message.
4. Weekend boundary handling: Ensure skipping 2 calendar days correctly tracks subsequent working days.
5. Slot selection continuity: Ensure dates from day 2 onward function normally for both roles.

---

### Task 1: Update `get_upcoming_days` to Support Role-Based Offsets

**Files:**
- Modify: `main.py:35-55`
- Test: `tests/test_role_based_dates.py`

**Interfaces:**
- Produces: `get_upcoming_days(days_count=5, is_admin=False, reference_date=None) -> list[tuple[jdatetime.date, str]]`

- [ ] **Step 1: Write failing tests in `tests/test_role_based_dates.py`**

Test:
- With `reference_date = 1405/08/20` (Saturday):
  - `is_admin=True`: First day is `1405/08/20` (Saturday), second is `1405/08/21` (Sunday).
  - `is_admin=False`: Neither `1405/08/20` nor `1405/08/21` is present; first day is `1405/08/22` (Monday).

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_role_based_dates.py -v`
Expected: FAIL

- [ ] **Step 3: Implement role-based offset in `get_upcoming_days` in `main.py`**

```python
def get_upcoming_days(days_count=5, is_admin=False, reference_date=None):
    days = []
    if reference_date is not None:
        start_date = reference_date
    else:
        start_date = jdatetime.date.today()
        if start_date.year < 1405:
            start_date = jdatetime.date(1405, 1, 1)

    # مراجعین عادی امکان رزرو برای امروز و فردا را ندارند
    if not is_admin:
        current_date = start_date + jdatetime.timedelta(days=2)
    else:
        current_date = start_date

    added = 0
    while added < days_count:
        if current_date.weekday() <= 4:
            day_name = PERSIAN_WEEKDAYS[current_date.weekday()]
            days.append((current_date, day_name))
            added += 1
        current_date = current_date + jdatetime.timedelta(days=1)
    return days
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_role_based_dates.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_role_based_dates.py
git commit -m "feat(bot): add role-based date offset to get_upcoming_days"
```

---

### Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard

**Files:**
- Modify: `main.py:230-275`
- Test: `tests/test_role_based_dates.py`

**Interfaces:**
- Consumes: `get_upcoming_days(days_count=5, is_admin=...)`, `ADMIN_IDS`
- Updates:
  - `query.data == "book_appointment"`: passes `is_admin=(user_id in ADMIN_IDS)`.
  - `query.data.startswith("date_")`: rejects today and tomorrow if `user_id not in ADMIN_IDS`.

- [ ] **Step 1: Write failing integration tests in `tests/test_role_based_dates.py`**

Test:
- `test_book_appointment_keyboard_for_admin_vs_user`: Checks rendered buttons.
- `test_user_selecting_today_or_tomorrow_blocked`: Non-admin sending `date_<today>` gets warning, no time slots shown.
- `test_admin_selecting_today_allowed`: Admin sending `date_<today>` gets time slots.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_role_based_dates.py -v`
Expected: FAIL

- [ ] **Step 3: Implement date callback guard in `main.py`**

In `main.py`:
1. In `book_appointment`: `is_admin = user_id in ADMIN_IDS`, `upcoming_days = get_upcoming_days(5, is_admin=is_admin)`.
2. In `date_`:
```python
        selected_date = query.data.split("_")[1]
        
        # بررسی دسترسی نقش: مراجعین عادی مجاز به انتخاب امروز یا فردا نیستند
        if user_id not in ADMIN_IDS:
            today_date = jdatetime.date.today()
            if today_date.year < 1405:
                today_date = jdatetime.date(1405, 1, 1)
            tomorrow_date = today_date + jdatetime.timedelta(days=1)
            today_str = today_date.strftime("%Y/%m/%d")
            tomorrow_str = tomorrow_date.strftime("%Y/%m/%d")
            
            if selected_date in (today_str, tomorrow_str):
                keyboard = [[InlineKeyboardButton("🔙 بازگشت به انتخاب تاریخ", callback_data="book_appointment")]]
                await query.edit_message_text(
                    "⚠️ مراجع گرامی؛\\n"
                    "رزرو نوبت برای امروز و فردا منحصراً از طریق تماس تلفنی با پذیرش کلینیک امکان‌پذیر می‌باشد.\\n"
                    "لطفاً نوبت مورد نظر خود را از میان روزهای بعد انتخاب فرمایید. 🌱",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests/test_role_based_dates.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_role_based_dates.py
git commit -m "feat(bot): enforce today and tomorrow booking restrictions for non-admins"
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
