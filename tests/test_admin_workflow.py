import unittest
from unittest.mock import AsyncMock, MagicMock
import sqlite3
import os
import jdatetime
import database
import main

class TestAdminWorkflow(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = database.get_connection
        self.test_db = "test_clinic_workflow.db"
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

    def test_format_upcoming_week_appointments_empty(self):
        ref_date = jdatetime.date(1405, 1, 1)
        text = main.format_upcoming_week_appointments(reference_date=ref_date)
        self.assertIn("در ۷ روز آینده هیچ نوبت قطعی ثبت نشده است", text)

    def test_format_upcoming_week_appointments_with_data(self):
        ref_date = jdatetime.date(1405, 1, 1)
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (101, '1405/01/02', '18:00', 'حضوری', 'علی محمدی', 'confirmed', 'p1')
        ''')
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (102, '1405/01/04', '19:00', 'آنلاین', 'سارا احمدی', 'confirmed', 'p2')
        ''')
        conn.commit()
        conn.close()

        text = main.format_upcoming_week_appointments(reference_date=ref_date)
        self.assertIn("1405/01/02", text)
        self.assertIn("18:00", text)
        self.assertIn("علی محمدی", text)
        self.assertIn("حضوری", text)
        self.assertIn("1405/01/04", text)
        self.assertIn("سارا احمدی", text)
        self.assertIn("آنلاین", text)
        # Ensure no raw markdown asterisks or backticks are present
        self.assertNotIn("**", text)
        self.assertNotIn("`", text)

    async def test_button_handler_approve_resets_session_and_sends_menu(self):
        # Insert a pending appointment
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (999, '1405/01/03', '17:00', 'حضوری', 'تست مراجع', 'pending', 'p_test')
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Mock Update and Context
        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        query.message.caption = "درخواست نوبت جدید"
        query.message.chat_id = main.MAIN_ADMIN_ID
        query.from_user.id = main.MAIN_ADMIN_ID
        update.callback_query = query
        update.effective_user.id = main.MAIN_ADMIN_ID
        update.effective_user.username = "clinic_admin"

        context = MagicMock()
        context.user_data = {"some_key": "some_value"}
        context.bot.send_message = AsyncMock()

        # Call button_handler
        await main.button_handler(update, context)

        # Verify database updated to confirmed
        app_info = database.get_appointment(app_id)
        self.assertEqual(app_info[5], "confirmed")

        # Verify edit_message_caption was called with reply_markup=None
        query.edit_message_caption.assert_called_once()
        self.assertIn("تایید قطعی شد", query.edit_message_caption.call_args[1]["caption"])
        self.assertIsNone(query.edit_message_caption.call_args[1]["reply_markup"])

        # Verify admin user_data was cleared
        self.assertEqual(context.user_data, {})

        # Verify messages sent to client and admin
        # Call 1: confirmation to client (chat_id=999)
        # Call 2: weekly schedule to admin (chat_id=MAIN_ADMIN_ID)
        # Call 3: main menu to admin (chat_id=MAIN_ADMIN_ID)
        self.assertEqual(context.bot.send_message.call_count, 3)

        admin_schedule_call = context.bot.send_message.call_args_list[1]
        self.assertEqual(admin_schedule_call[1]["chat_id"], main.MAIN_ADMIN_ID)
        self.assertIn("برنامه کاری ۷ روز آینده", admin_schedule_call[1]["text"])

        admin_menu_call = context.bot.send_message.call_args_list[2]
        self.assertEqual(admin_menu_call[1]["chat_id"], main.MAIN_ADMIN_ID)
        self.assertIn("منوی اصلی", admin_menu_call[1]["text"])
        self.assertIsNotNone(admin_menu_call[1]["reply_markup"])

if __name__ == '__main__':
    unittest.main()
