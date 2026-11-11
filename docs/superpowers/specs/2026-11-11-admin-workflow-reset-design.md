# Admin Workflow Post-Decision Reset & Weekly Schedule Spec

## Goal
Improve the Telegram bot workflow for administrators after approving or rejecting payment receipts:
1. Prevent repeated clicks by removing the decision buttons on the handled receipt photo.
2. Deliver a complete schedule of all confirmed appointments for the next 7 days immediately after the decision.
3. Reset/restart the administrator's session state and return them directly to the main menu.

## Background & Problem
Previously, when an admin clicked "تایید نوبت" or "رد رسید" in [main.py](file:///c:/Users/PC%20Ishragh/Desktop/psychology_bot/main.py), the bot only edited the photo caption and notified the client. The inline buttons remained visible, `context.user_data` was not reset, no feedback regarding upcoming bookings was given, and the admin had to manually send `/start` to see the main menu again.

## Requirements
1. **Decision Button Cleanup**: After an admin confirms an approval or rejection, the inline keyboard on the receipt message must be cleared (`reply_markup=None`) to avoid duplicate clicks.
2. **Weekly Bookings Query**: A database helper must retrieve all confirmed appointments falling within the 7-day range starting from the current date (handling `1405` base date conventions cleanly).
3. **Weekly Bookings Message**: The acting admin receives a message listing all upcoming confirmed appointments in the next 7 days, or a message confirming that no appointments are scheduled.
4. **Session Reset & Main Menu Redirect**: The acting admin's session data is cleared (`context.user_data.clear()`), and a fresh main menu message with `get_main_menu_keyboard(admin_id)` is sent to them.
