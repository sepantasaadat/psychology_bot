# Role-Based Booking Date Restrictions Spec

## Goal
Restrict regular users from selecting appointment slots for the current day (today) and the following day (tomorrow), while preserving full access for clinic administrators to schedule same-day and next-day sessions.

## Requirements
1. **Regular Users (Non-Admins)**:
   - Today (`today`) and tomorrow (`today + 1 day`) must not appear in the date selection keyboard.
   - Date selection for regular users starts from 2 days ahead (`today + 2 days`), listing 5 selectable working days.
   - Callback protection: If a regular user sends `date_<date>` where `date` is today or tomorrow, the bot denies slot selection and politely refers them to phone reception.
2. **Admins (`user_id in ADMIN_IDS`)**:
   - Admins retain unrestricted access to select dates starting from today, including same-day and next-day working days.
