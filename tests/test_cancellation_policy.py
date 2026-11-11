import unittest
from unittest.mock import AsyncMock, MagicMock
import os
import sqlite3
import jdatetime
import database
import main

class TestCancellationPolicyHelpers(unittest.TestCase):
    def test_parse_appointment_datetime(self):
        dt = main.parse_appointment_datetime("1405/08/25", "18:30")
        self.assertEqual(dt.year, 1405)
        self.assertEqual(dt.month, 8)
        self.assertEqual(dt.day, 25)
        self.assertEqual(dt.hour, 18)
        self.assertEqual(dt.minute, 30)

    def test_can_cancel_appointment_eligibility(self):
        # Simulated "now": 1405/08/20 at 18:00
        ref_now = jdatetime.datetime(1405, 8, 20, 18, 0)

        # 1. 72 hours away: eligible
        eligible, reason = main.can_cancel_appointment("1405/08/23", "18:00", now=ref_now)
        self.assertTrue(eligible)
        self.assertEqual(reason, "ok")

        # 2. Exactly 48 hours away: eligible
        eligible, reason = main.can_cancel_appointment("1405/08/22", "18:00", now=ref_now)
        self.assertTrue(eligible)
        self.assertEqual(reason, "ok")

        # 3. 47 hours away: within 48 hours, ineligible
        eligible, reason = main.can_cancel_appointment("1405/08/22", "17:00", now=ref_now)
        self.assertFalse(eligible)
        self.assertEqual(reason, "within_48_hours")

        # 4. Same day, 2 hours away: within 48 hours, ineligible
        eligible, reason = main.can_cancel_appointment("1405/08/20", "20:00", now=ref_now)
        self.assertFalse(eligible)
        self.assertEqual(reason, "within_48_hours")

        # 5. Exactly now (0 hours left): expired
        eligible, reason = main.can_cancel_appointment("1405/08/20", "18:00", now=ref_now)
        self.assertFalse(eligible)
        self.assertEqual(reason, "expired")

        # 6. Past appointment (yesterday): expired
        eligible, reason = main.can_cancel_appointment("1405/08/19", "18:00", now=ref_now)
        self.assertFalse(eligible)
        self.assertEqual(reason, "expired")

class TestCancellationPolicyIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = database.get_connection
        self.test_db = "test_clinic_policy.db"
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

    def test_expired_appointment_buttons_not_rendered(self):
        user_id = 888
        now = jdatetime.datetime.now()
        if now.year < 1405:
            now = now.replace(year=1405)

        past_date = (now - jdatetime.timedelta(days=1)).strftime("%Y/%m/%d")
        future_date = (now + jdatetime.timedelta(days=3)).strftime("%Y/%m/%d")

        # Insert past appointment
        past_id = database.add_confirmed_appointment(user_id, past_date, '17:00', 'حضوری', 'کاربر منقضی', 'r_past')
        # Insert future appointment
        future_id = database.add_confirmed_appointment(user_id, future_date, '18:00', 'آنلاین', 'کاربر فعال', 'r_fut')

        keyboard = main.get_main_menu_keyboard(user_id)
        callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row if btn.callback_data]

        # Past appointment button must NOT be present
        self.assertNotIn(f"user_cancel_{past_id}", callbacks)
        # Future appointment button MUST be present
        self.assertIn(f"user_cancel_{future_id}", callbacks)

    async def test_cancel_within_48_hours_denied_without_db_change_or_admin_alert(self):
        user_id = 889
        now = jdatetime.datetime.now()
        if now.year < 1405:
            now = now.replace(year=1405)

        # 24 hours in the future (< 48 hours)
        target_dt = now + jdatetime.timedelta(hours=24)
        target_date = target_dt.strftime("%Y/%m/%d")
        target_time = target_dt.strftime("%H:%M")

        app_id = database.add_confirmed_appointment(user_id, target_date, target_time, 'حضوری', 'کاربر نزدیک', 'r_near')

        update = MagicMock()
        query = MagicMock()
        query.data = f"user_cancel_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = user_id
        update.effective_user.username = "user_near"

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()

        await main.button_handler(update, context)

        # 1. Appointment must still exist in DB
        app_info = database.get_appointment(app_id)
        self.assertIsNotNone(app_info)
        self.assertEqual(app_info[5], 'confirmed')

        # 2. Apology message must explain 48-hour policy
        query.edit_message_text.assert_called_once()
        reply_text = query.edit_message_text.call_args[0][0]
        self.assertIn("۴۸ ساعت", reply_text)
        self.assertIn("امکان لغو", reply_text)

        # 3. Admins must NOT be alerted
        self.assertEqual(context.bot.send_message.call_count, 0)

    async def test_cancel_over_48_hours_succeeds(self):
        user_id = 890
        now = jdatetime.datetime.now()
        if now.year < 1405:
            now = now.replace(year=1405)

        # 72 hours in the future (>= 48 hours)
        target_dt = now + jdatetime.timedelta(hours=72)
        target_date = target_dt.strftime("%Y/%m/%d")
        target_time = target_dt.strftime("%H:%M")

        app_id = database.add_confirmed_appointment(user_id, target_date, target_time, 'آنلاین', 'کاربر مجاز', 'r_valid')

        update = MagicMock()
        query = MagicMock()
        query.data = f"user_cancel_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = user_id
        update.effective_user.username = "user_valid"

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()

        await main.button_handler(update, context)

        # 1. Appointment must be deleted from DB
        self.assertIsNone(database.get_appointment(app_id))

        # 2. Confirmation message sent to user
        query.edit_message_text.assert_called_once()
        reply_text = query.edit_message_text.call_args[0][0]
        self.assertIn("با موفقیت لغو", reply_text)

        # 3. Admins must be alerted
        self.assertGreater(context.bot.send_message.call_count, 0)

if __name__ == '__main__':
    unittest.main()
