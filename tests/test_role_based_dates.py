import unittest
from unittest.mock import AsyncMock, MagicMock
import os
import sqlite3
import jdatetime
import database
import main
from main import get_upcoming_days

class TestRoleBasedDates(unittest.TestCase):
    def test_admin_gets_today_and_tomorrow(self):
        # 1405/08/23 is Saturday (weekday 0)
        ref_date = jdatetime.date(1405, 8, 23)
        days = get_upcoming_days(days_count=5, is_admin=True, reference_date=ref_date)
        dates = [d[0].strftime("%Y/%m/%d") for d in days]
        
        self.assertEqual(len(days), 5)
        self.assertEqual(dates[0], "1405/08/23")
        self.assertEqual(dates[1], "1405/08/24")
        self.assertEqual(days[0][1], "شنبه")
        self.assertEqual(days[1][1], "یکشنبه")

    def test_regular_user_skips_today_and_tomorrow(self):
        # 1405/08/23 is Saturday (weekday 0)
        # Saturday + 2 days = Monday (1405/08/25, weekday 2)
        ref_date = jdatetime.date(1405, 8, 23)
        days = get_upcoming_days(days_count=5, is_admin=False, reference_date=ref_date)
        dates = [d[0].strftime("%Y/%m/%d") for d in days]
        
        self.assertEqual(len(days), 5)
        self.assertNotIn("1405/08/23", dates)
        self.assertNotIn("1405/08/24", dates)
        self.assertEqual(dates[0], "1405/08/25")
        self.assertEqual(days[0][1], "دوشنبه")

    def test_default_is_admin_is_false(self):
        ref_date = jdatetime.date(1405, 8, 23)
        days = get_upcoming_days(days_count=5, reference_date=ref_date)
        dates = [d[0].strftime("%Y/%m/%d") for d in days]
        
        self.assertNotIn("1405/08/23", dates)
        self.assertNotIn("1405/08/24", dates)


class TestRoleBasedDatesIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = database.get_connection
        self.test_db = "test_clinic_role_dates.db"
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

    async def test_book_appointment_keyboard_for_admin_vs_user(self):
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        tomorrow_date = today_date + jdatetime.timedelta(days=1)
        today_str = today_date.strftime("%Y/%m/%d")
        tomorrow_str = tomorrow_date.strftime("%Y/%m/%d")

        # 1. Regular user
        user_update = MagicMock()
        user_query = MagicMock()
        user_query.data = "book_appointment"
        user_query.answer = AsyncMock()
        user_query.edit_message_text = AsyncMock()
        user_update.callback_query = user_query
        user_update.effective_user.id = 999
        user_update.effective_user.username = "normal_user"

        context = MagicMock()
        context.user_data = {}
        await main.button_handler(user_update, context)

        user_query.edit_message_text.assert_called_once()
        user_markup = user_query.edit_message_text.call_args[1]["reply_markup"]
        user_callbacks = [btn.callback_data for row in user_markup.inline_keyboard for btn in row if btn.callback_data]

        self.assertNotIn(f"date_{today_str}", user_callbacks)
        self.assertNotIn(f"date_{tomorrow_str}", user_callbacks)

        # 2. Admin user
        admin_update = MagicMock()
        admin_query = MagicMock()
        admin_query.data = "book_appointment"
        admin_query.answer = AsyncMock()
        admin_query.edit_message_text = AsyncMock()
        admin_update.callback_query = admin_query
        admin_update.effective_user.id = main.MAIN_ADMIN_ID
        admin_update.effective_user.username = "admin"

        await main.button_handler(admin_update, context)

        admin_query.edit_message_text.assert_called_once()
        admin_markup = admin_query.edit_message_text.call_args[1]["reply_markup"]
        admin_callbacks = [btn.callback_data for row in admin_markup.inline_keyboard for btn in row if btn.callback_data]

        if today_date.weekday() <= 4:
            self.assertIn(f"date_{today_str}", admin_callbacks)
        if tomorrow_date.weekday() <= 4:
            self.assertIn(f"date_{tomorrow_str}", admin_callbacks)

    async def test_user_selecting_today_or_tomorrow_blocked(self):
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        tomorrow_date = today_date + jdatetime.timedelta(days=1)
        today_str = today_date.strftime("%Y/%m/%d")
        tomorrow_str = tomorrow_date.strftime("%Y/%m/%d")

        # Test today
        update = MagicMock()
        query = MagicMock()
        query.data = f"date_{today_str}"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 999
        context = MagicMock()
        context.user_data = {}

        await main.button_handler(update, context)

        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("تماس تلفنی با پذیرش کلینیک", text)
        markup = query.edit_message_text.call_args[1]["reply_markup"]
        callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
        time_callbacks = [cb for cb in callbacks if cb.startswith("time_")]
        self.assertEqual(time_callbacks, [])

        # Test tomorrow
        query.reset_mock()
        query.data = f"date_{tomorrow_str}"
        await main.button_handler(update, context)

        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("تماس تلفنی با پذیرش کلینیک", text)

    async def test_user_selecting_past_date_blocked(self):
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        yesterday_date = today_date - jdatetime.timedelta(days=1)
        yesterday_str = yesterday_date.strftime("%Y/%m/%d")

        update = MagicMock()
        query = MagicMock()
        query.data = f"date_{yesterday_str}"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 999
        context = MagicMock()
        context.user_data = {}

        await main.button_handler(update, context)

        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("تماس تلفنی با پذیرش کلینیک", text)

    async def test_user_tampering_time_callback_blocked(self):
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        today_str = today_date.strftime("%Y/%m/%d")

        update = MagicMock()
        query = MagicMock()
        query.data = f"time_{today_str}_17:00"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 999
        context = MagicMock()
        context.user_data = {}

        await main.button_handler(update, context)

        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("تماس تلفنی با پذیرش کلینیک", text)
        self.assertNotIn("selected_date", context.user_data)

    async def test_admin_selecting_today_allowed(self):
        today_date = jdatetime.date.today()
        if today_date.year < 1405:
            today_date = jdatetime.date(1405, 1, 1)
        today_str = today_date.strftime("%Y/%m/%d")

        update = MagicMock()
        query = MagicMock()
        query.data = f"date_{today_str}"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = main.MAIN_ADMIN_ID
        context = MagicMock()
        context.user_data = {}

        await main.button_handler(update, context)

        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("گام دوم: انتخاب ساعت جلسه مشاوره", text)
        markup = query.edit_message_text.call_args[1]["reply_markup"]
        callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
        time_callbacks = [cb for cb in callbacks if cb.startswith("time_")]
        self.assertTrue(len(time_callbacks) > 0)

if __name__ == "__main__":
    unittest.main()
