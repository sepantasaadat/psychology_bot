# User Appointment Cancellation Feature Spec

## Goal
Enable regular (non-admin) clients to view and directly cancel their confirmed bookings for the upcoming week from the Telegram bot's main menu, with automatic database removal and real-time notification dispatch to clinic administrators.

## Requirements
1. **Target Audience & Role Exclusion**:
   - Dynamic cancellation buttons are strictly for regular users (`user_id not in ADMIN_IDS`).
   - Admin IDs manage cancellations exclusively through the admin panel (`admin_panel`).
2. **Dynamic Button Generation**:
   - In `get_main_menu_keyboard(user_id)`, for non-admin users, query confirmed appointments for the current 7-day window.
   - For each booking found, append a distinct inline button:
     `❌ لغو نوبت: [تاریخ] ساعت [ساعت]` with callback data `user_cancel_<id>`.
3. **Immediate Database Deletion**:
   - When `user_cancel_<id>` is clicked, fetch appointment details and immediately execute `database.delete_appointment(app_id)`.
4. **User Confirmation**:
   - Display a reassuring cancellation confirmation message to the user and refresh their main menu keyboard (with the canceled button now removed).
5. **Admin Notification & Main Menu Refresh**:
   - Send a formal cancellation notification to all administrators in `ADMIN_IDS`:
     `⚠️ گزارش لغو نوبت توسط مراجع:`
     Listing: client name, date, time slot, session type, and tracking ID.
   - Immediately follow up with the main menu keyboard for each administrator so their session returns to the main root menu.
