# Admin Direct Booking Flow Spec

## Goal
Implement a specialized, streamlined booking workflow for users with administrator IDs (`ADMIN_IDS`), allowing them to schedule appointments directly without payment receipt uploads or verification queues.

## Requirements
1. **Flow Preservation**: The selection of working day (`date_`), time slot (`time_`), session type (`type_`), and full name input must remain identical for all users.
2. **Admin Identification**: In `handle_text`, when `state == 'awaiting_name'`, check if `user_id in ADMIN_IDS`.
3. **Bypass Receipt & Verification**:
   - For regular users: retain the existing transition to `state = 'awaiting_receipt'` and receipt prompt.
   - For admin users: bypass receipt upload and approval queue completely.
4. **Direct Database Persistence**:
   - Immediately persist the appointment with `status = 'confirmed'` and `receipt_file_id = 'admin_direct'`.
5. **Immediate Confirmation & Reset**:
   - Clear `context.user_data`.
   - Send direct confirmation to the admin with appointment details and tracking ID.
   - Send the updated 7-day schedule report (`format_upcoming_week_appointments()`).
   - Send the main menu keyboard (`get_main_menu_keyboard(user_id)`).
