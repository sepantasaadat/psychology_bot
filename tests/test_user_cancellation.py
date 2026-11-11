import unittest
from unittest.mock import AsyncMock, MagicMock
import sqlite3
import os
import jdatetime
import database
import main

class TestUserCancellation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = database.get_connection
        self.test_db = "test_clinic_user_cancel.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
        def get_test_connection():
            return sqlite3.connect(self.test_db)
            
        database.get_connection = get_test_connection
        database.setup_database()
        
    def tearDown(self):
        database.get_connection = self.original_db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_admin_menu_has_no_user_cancel_buttons(self):
        # Insert confirmed appointment for admin
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        date_str = today_date.strftime("%Y/%m/%d")

        database.add_confirmed_appointment(
            user_id=main.MAIN_ADMIN_ID,
            date=date_str,
            time='18:00',
            session_type='حضوری',
            full_name='ادمین اصلی',
            receipt_file_id='admin_direct'
        )

        keyboard = main.get_main_menu_keyboard(main.MAIN_ADMIN_ID)
        all_callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row if btn.callback_data]

        # Verify NO user_cancel_ buttons exist for admin
        cancel_buttons = [cb for cb in all_callbacks if cb.startswith("user_cancel_")]
        self.assertEqual(cancel_buttons, [])

        # Verify admin_panel button is present
        self.assertIn("admin_panel", all_callbacks)

    def test_user_menu_contains_dynamic_cancel_buttons(self):
        user_id = 555
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        d1 = (today_date + jdatetime.timedelta(days=1)).strftime("%Y/%m/%d")
        d2 = (today_date + jdatetime.timedelta(days=2)).strftime("%Y/%m/%d")

        app1 = database.add_confirmed_appointment(user_id, d1, '17:00', 'حضوری', 'کاربر تستی', 'rec1')
        app2 = database.add_confirmed_appointment(user_id, d2, '19:00', 'آنلاین', 'کاربر تستی', 'rec2')

        keyboard = main.get_main_menu_keyboard(user_id)
        
        cancel_btns = [
            btn for row in keyboard.inline_keyboard for btn in row 
            if btn.callback_data and btn.callback_data.startswith("user_cancel_")
        ]
        self.assertEqual(len(cancel_btns), 2)
        
        # Check callback data and text
        self.assertEqual(cancel_btns[0].callback_data, f"user_cancel_{app1}")
        self.assertIn(d1, cancel_btns[0].text)
        self.assertIn("17:00", cancel_btns[0].text)

        self.assertEqual(cancel_btns[1].callback_data, f"user_cancel_{app2}")
        self.assertIn(d2, cancel_btns[1].text)
        self.assertIn("19:00", cancel_btns[1].text)

        # Admin panel must NOT be in regular user's menu
        all_callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row if btn.callback_data]
        self.assertNotIn("admin_panel", all_callbacks)

    async def test_user_cancel_callback_deletes_record_and_notifies_admins(self):
        user_id = 777
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        # Schedule 3 days ahead (72h) to satisfy the 48-hour cancellation policy
        d_str = (today_date + jdatetime.timedelta(days=3)).strftime("%Y/%m/%d")

        app_id = database.add_confirmed_appointment(
            user_id=user_id,
            date=d_str,
            time='18:00',
            session_type='حضوری',
            full_name='محمد رضایی',
            receipt_file_id='rec777'
        )

        update = MagicMock()
        query = MagicMock()
        query.data = f"user_cancel_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = user_id
        update.effective_user.username = "mohammad_r"

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()

        await main.button_handler(update, context)

        # 1. Appointment must be deleted from database
        self.assertIsNone(database.get_appointment(app_id))

        # 2. User message edited with confirmation
        query.edit_message_text.assert_called_once()
        user_reply_text = query.edit_message_text.call_args[0][0]
        self.assertIn("با موفقیت لغو", user_reply_text)

        # 3. Admins receive notification + main menu
        # Total admin count = len(main.ADMIN_IDS)
        # Each admin gets: 1 alert message + 1 main menu message = 2 messages per admin
        expected_calls = len(main.ADMIN_IDS) * 2
        self.assertEqual(context.bot.send_message.call_count, expected_calls)

        # Verify alert content for the first admin
        first_admin_alert = context.bot.send_message.call_args_list[0]
        self.assertEqual(first_admin_alert[1]["chat_id"], main.ADMIN_IDS[0])
        self.assertIn("گزارش لغو نوبت توسط مراجع", first_admin_alert[1]["text"])
        self.assertIn("محمد رضایی", first_admin_alert[1]["text"])
        self.assertIn(d_str, first_admin_alert[1]["text"])

        # Verify main menu for the first admin
        first_admin_menu = context.bot.send_message.call_args_list[1]
        self.assertEqual(first_admin_menu[1]["chat_id"], main.ADMIN_IDS[0])
        self.assertIn("منوی اصلی", first_admin_menu[1]["text"])
        self.assertIsNotNone(first_admin_menu[1]["reply_markup"])

if __name__ == '__main__':
    unittest.main()
