# Appointment Cancellation Time Restrictions & Button Expiration Spec

## Goal
Implement a 48-hour cancellation policy and automatic expiration of cancellation buttons for regular users, preventing cancellations close to session time and hiding buttons for past sessions.

## Requirements
1. **Automatic Removal of Expired Buttons**:
   - In `get_main_menu_keyboard(user_id)`, omit cancellation buttons for any appointment whose scheduled datetime is in the past (`appointment_datetime <= current_datetime`).
2. **48-Hour Cancellation Restriction**:
   - When a user clicks `user_cancel_<id>`, calculate the time difference: `(appointment_datetime - current_datetime).total_seconds() / 3600`.
   - If the appointment has already passed (`hours_remaining <= 0`):
     - Do not cancel or delete from database.
     - Display an informative message stating the appointment time has passed.
     - Refresh user menu (the expired button will vanish).
   - If less than 48 hours remain (`0 < hours_remaining < 48`):
     - Do not cancel or delete from database.
     - Do not notify admins.
     - Display an apology message explaining the clinic's 48-hour cancellation policy and advising the client to contact clinic reception directly for emergencies.
     - Refresh user menu.
   - If 48 hours or more remain (`hours_remaining >= 48`):
     - Delete appointment from database via `database.delete_appointment(app_id)`.
     - Send cancellation confirmation to the user and refresh user menu.
     - Dispatch alert to all `ADMIN_IDS`.
     - Deliver main menu to each administrator.
