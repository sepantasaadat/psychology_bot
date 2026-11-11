import unittest
from unittest.mock import AsyncMock, MagicMock
import sqlite3
import os
import jdatetime
import database
import main

class TestAdminDirectBooking(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = database.get_connection
        self.test_db = "test_clinic_direct_booking.db"
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

    async def test_admin_booking_bypasses_receipt_and_confirms(self):
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        date_str = today_date.strftime("%Y/%m/%d")

        update = MagicMock()
        update.effective_user.id = main.MAIN_ADMIN_ID
        update.effective_user.first_name = "دکتر"
        update.effective_user.username = "clinic_admin"
        update.message.text = "دکتر سپنتا"
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            'state': 'awaiting_name',
            'selected_date': date_str,
            'selected_time': '18:00',
            'session_type': 'حضوری'
        }

        await main.handle_text(update, context)

        # 1. Verify user_data is cleared
        self.assertEqual(context.user_data, {})

        # 2. Verify appointment is saved in DB as confirmed with admin_direct
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, date, time, session_type, full_name, status, receipt_file_id FROM appointments")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row[1], main.MAIN_ADMIN_ID)
        self.assertEqual(row[2], date_str)
        self.assertEqual(row[3], '18:00')
        self.assertEqual(row[4], 'حضوری')
        self.assertEqual(row[5], 'دکتر سپنتا')
        self.assertEqual(row[6], 'confirmed')
        self.assertEqual(row[7], 'admin_direct')

        # 3. Verify 3 messages were replied to admin
        self.assertEqual(update.message.reply_text.call_count, 3)
        msg1 = update.message.reply_text.call_args_list[0][0][0]
        self.assertIn("با موفقیت به‌صورت مستقیم ثبت قطعی شد", msg1)
        self.assertIn("دکتر سپنتا", msg1)

        msg2 = update.message.reply_text.call_args_list[1][0][0]
        self.assertIn("فهرست نوبت‌های تایید‌شده ۷ روز آینده", msg2)
        self.assertIn(date_str, msg2)
        self.assertIn("دکتر سپنتا", msg2)

        msg3_args = update.message.reply_text.call_args_list[2]
        self.assertIn("منوی اصلی", msg3_args[0][0])
        self.assertIsNotNone(msg3_args[1].get('reply_markup'))

    async def test_regular_user_booking_requires_receipt(self):
        regular_user_id = 123456789
        update = MagicMock()
        update.effective_user.id = regular_user_id
        update.effective_user.first_name = "کاربر"
        update.effective_user.username = "regular_client"
        update.message.text = "علی رضایی"
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            'state': 'awaiting_name',
            'selected_date': '1405/01/04',
            'selected_time': '18:00',
            'session_type': 'آنلاین'
        }

        await main.handle_text(update, context)

        # 1. State must transition to awaiting_receipt
        self.assertEqual(context.user_data.get('state'), 'awaiting_receipt')
        self.assertEqual(context.user_data.get('full_name'), 'علی رضایی')

        # 2. Database must not have confirmed appointment
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM appointments WHERE status = 'confirmed'")
        rows = cursor.fetchall()
        conn.close()
        self.assertEqual(len(rows), 0)

        # 3. Exactly one message requesting receipt upload
        self.assertEqual(update.message.reply_text.call_count, 1)
        prompt_text = update.message.reply_text.call_args_list[0][0][0]
        self.assertIn("بارگذاری رسید پرداخت", prompt_text)

if __name__ == '__main__':
    unittest.main()
