# Handled Appointment Workflow Design Spec

## Intent
When an administrator attempts to approve or reject an appointment that has already been confirmed, rejected, or canceled by another administrator, the bot notifies the administrator and ensures their administrative workflow continues smoothly by sending the updated 7-day clinic schedule, resetting session state, and returning the administrator to the main menu.

## Context & Problem
In `main.py`, lines 417-419:
```python
if current_status != "pending":
    await query.edit_message_caption(caption=f"{query.message.caption}\n\n⚠️ این نوبت قبلاً توسط ادمین دیگری تعیین تکلیف شده است.")
    return
```
When this occurs:
- The receipt message caption is updated, but obsolete action buttons remain on the message.
- The administrator's session state is not cleared.
- The administrator does not receive the upcoming 7-day schedule.
- The administrator is left stranded without the main menu keyboard.

## Goals
- Edit the message caption on the handled appointment receipt and remove obsolete inline buttons (`reply_markup=None`).
- Dispatch the 7-day appointment schedule (`format_upcoming_week_appointments()`) to that administrator.
- Clear the administrator's `context.user_data`.
- Deliver the administrator main menu (`get_main_menu_keyboard(user_id)`).

## Non-Goals
- Changing database schema or appointment states.
- Changing regular user notifications.

## Approaches Considered
- Approach 1: Duplicate inline post-action code inside `if current_status != "pending":`.
- Approach 2 (Selected): Extract `complete_admin_review_session(query, context, user_id)` helper to unify post-handling behavior across approval, rejection, and already-handled states.

## Constraints
- Persian clinical tone.
- No raw asterisks (`**` or `*`) or backticks in Telegram messages.
- Clean separation of concerns and robust unit/integration test coverage.
