# Other Admin Approval Workflow Design Spec

## Intent
When one administrator approves an appointment, obsolete payment receipt and approval request messages are deleted from the chat of all other administrators. Those other administrators then receive only the updated 7-day schedule of booked appointments, followed by the clinic main menu.

## Context & Problem
Currently in `main.py`:
1. `handle_receipt` broadcasts the receipt photo to each administrator in `ADMIN_IDS` via `context.bot.send_photo`, but does not save the message IDs.
2. In `button_handler` under `action == "approve"`, only the acting administrator's message is updated (`query.edit_message_caption`), and only the acting administrator receives the 7-day schedule and main menu.
3. Other administrators still have the obsolete receipt message and action buttons in their chats.

## Goals
- Track the message ID sent to each administrator for an appointment's receipt request in a persistent SQLite table (`admin_receipt_messages`).
- When an administrator approves an appointment:
  - For each other administrator in `ADMIN_IDS`:
    - Delete the receipt message via `context.bot.delete_message(chat_id=other_admin, message_id=stored_msg_id)`.
    - Send only the updated 7-day schedule (`format_upcoming_week_appointments()`).
    - Send the administrator main menu (`get_main_menu_keyboard(other_admin)`).
  - Clear the tracked message IDs for that appointment from `admin_receipt_messages`.
- Handle potential errors gracefully if a message was already deleted or cannot be removed.

## Non-Goals
- Changing the workflow when an appointment is rejected (the prompt specifies approval: "When an appointment is approved/confirmed by one admin").
- Changing regular user confirmation messages.

## Data Model & Interfaces
In `database.py`:
- Table `admin_receipt_messages`:
  - `appointment_id INTEGER`
  - `admin_id INTEGER`
  - `message_id INTEGER`
  - `PRIMARY KEY (appointment_id, admin_id)`
- Functions:
  - `save_admin_receipt_message(appointment_id: int, admin_id: int, message_id: int) -> None`
  - `get_admin_receipt_messages(appointment_id: int) -> list[tuple[int, int]]` (returns `[(admin_id, message_id), ...]`)
  - `delete_admin_receipt_messages(appointment_id: int) -> None`

## Bot Flow Updates
In `main.py`:
1. In `handle_receipt`:
   ```python
   for admin in ADMIN_IDS:
       try:
           sent_msg = await context.bot.send_photo(...)
           database.save_admin_receipt_message(appointment_id, admin, sent_msg.message_id)
       except Exception as e:
           ...
   ```
2. In `button_handler` when `action == "approve"`:
   - Query tracked receipt messages via `database.get_admin_receipt_messages(appointment_id)`.
   - For `other_admin, msg_id` in tracked messages where `other_admin != user_id`:
     - Delete message: `await context.bot.delete_message(chat_id=other_admin, message_id=msg_id)` (wrapped in `try...except`).
     - Send schedule: `await context.bot.send_message(chat_id=other_admin, text=weekly_schedule)`.
     - Send main menu: `await context.bot.send_message(chat_id=other_admin, text="منوی اصلی پذیرش و مدیریت کلینیک: 🌿", reply_markup=get_main_menu_keyboard(other_admin))`.
   - Call `database.delete_admin_receipt_messages(appointment_id)`.

## Constraints
- Persian clinical tone.
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Clean separation of concerns and robust unit/integration test coverage.
