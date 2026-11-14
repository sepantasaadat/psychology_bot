import unittest
import os
import sqlite3
import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import config
import database
import main

class TestCheckoutTimeout(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = database.get_connection
        self.test_db = f"test_clinic_timeout_{os.getpid()}.db"
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

    def test_config_timeout_constants_defined(self):
        """Verify BOOKING_STEP_TIMEOUT_MINUTES and PENDING_EXPIRY_MINUTES are defined in config."""
        self.assertTrue(hasattr(config, "BOOKING_STEP_TIMEOUT_MINUTES"))
        self.assertEqual(config.BOOKING_STEP_TIMEOUT_MINUTES, 60)
        self.assertTrue(hasattr(config, "PENDING_EXPIRY_MINUTES"))
        self.assertEqual(config.PENDING_EXPIRY_MINUTES, 120)

    async def test_time_callback_sets_booking_started_at_and_schedules_job(self):
        """Selecting a time slot records booking_started_at in Asia/Tehran and schedules job_queue timeout."""
        user_id = 98765
        valid_date = config.get_upcoming_working_days(1, is_admin=False)[0]
        update = MagicMock()
        query = MagicMock()
        query.data = f"time_{valid_date}_17:00"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = user_id
        update.effective_chat.id = user_id

        context = MagicMock()
        context.user_data = {}
        context.job_queue = MagicMock()
        context.job_queue.get_jobs_by_name.return_value = []

        await main.time_callback(update, context)

        # 1. booking_started_at is saved in context.user_data
        self.assertIn("booking_started_at", context.user_data)
        started_at = context.user_data["booking_started_at"]
        dt = datetime.datetime.fromisoformat(started_at)
        self.assertIsNotNone(dt)

        # 2. job_queue schedules checkout_timeout_{user_id}
        context.job_queue.run_once.assert_called_once()
        call_kwargs = context.job_queue.run_once.call_args[1]
        self.assertEqual(call_kwargs.get("when"), 3600)
        self.assertEqual(call_kwargs.get("name"), f"checkout_timeout_{user_id}")

    async def test_type_callback_prompt_contains_1_hour_timeout_notice(self):
        """Prompt message in type_callback informs the user about the 1-hour completion limit."""
        update = MagicMock()
        query = MagicMock()
        query.data = "type_حضوری"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 98765

        context = MagicMock()
        context.user_data = {
            "selected_date": "1405/01/20",
            "selected_time": "17:00",
            "booking_started_at": config.now_tehran().isoformat()
        }

        await main.type_callback(update, context)

        query.edit_message_text.assert_called_once()
        prompt_text = query.edit_message_text.call_args[0][0]
        self.assertIn("۱ ساعت", prompt_text)
        self.assertIn("آزاد خواهد شد", prompt_text)

    async def test_reactive_expiration_at_name_entry_step(self):
        """User pausing at awaiting_name for > 60 minutes is rejected and session is cleared."""
        user_id = 98765
        update = MagicMock()
        update.effective_user.id = user_id
        update.effective_user.first_name = "کاربر"
        update.message.text = "علی رضایی"
        update.message.reply_text = AsyncMock()

        # Simulate 65 minutes elapsed
        now_tehran = config.now_tehran()
        past_time = now_tehran - datetime.timedelta(minutes=65)

        context = MagicMock()
        context.user_data = {
            "state": "awaiting_name",
            "selected_date": "1405/01/20",
            "selected_time": "17:00",
            "session_type": "حضوری",
            "booking_started_at": past_time.isoformat()
        }
        context.job_queue = MagicMock()
        context.job_queue.get_jobs_by_name.return_value = []

        await main.handle_text(update, context)

        # 1. user_data must be cleared
        self.assertEqual(context.user_data, {})

        # 2. Expiration message must be replied
        update.message.reply_text.assert_called_once()
        reply_text = update.message.reply_text.call_args[0][0]
        self.assertIn("مهلت ۱ ساعته شما برای تکمیل رزرو به پایان رسیده است", reply_text)
        self.assertIn("از صفحه اول مجدداً نوبت خود را انتخاب کنید", reply_text)

    async def test_reactive_expiration_at_receipt_upload_step(self):
        """User pausing at awaiting_receipt for > 60 minutes has receipt rejected and no DB appointment created."""
        user_id = 98765
        update = MagicMock()
        update.effective_user.id = user_id
        update.effective_user.first_name = "کاربر"
        update.effective_user.username = "test_user"
        update.message.photo = [MagicMock(file_id="photo_123")]
        update.message.message_id = 456
        update.message.reply_text = AsyncMock()

        # Simulate 70 minutes elapsed
        now_tehran = config.now_tehran()
        past_time = now_tehran - datetime.timedelta(minutes=70)

        context = MagicMock()
        context.user_data = {
            "state": "awaiting_receipt",
            "selected_date": "1405/01/20",
            "selected_time": "17:00",
            "session_type": "حضوری",
            "full_name": "سارا احمدی",
            "booking_started_at": past_time.isoformat()
        }
        context.job_queue = MagicMock()
        context.job_queue.get_jobs_by_name.return_value = []

        await main.handle_receipt(update, context)

        # 1. user_data must be cleared
        self.assertEqual(context.user_data, {})

        # 2. No pending appointment created in database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE date = '1405/01/20' AND time = '17:00'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

        # 3. Expiration message replied
        update.message.reply_text.assert_called_once()
        reply_text = update.message.reply_text.call_args[0][0]
        self.assertIn("مهلت ۱ ساعته شما برای تکمیل رزرو به پایان رسیده است", reply_text)

    async def test_proactive_checkout_timeout_job_resets_session_and_notifies_user(self):
        """When checkout_timeout_job executes after 1 hour, it clears user_data and sends timeout notification."""
        user_id = 55555
        chat_id = 55555

        job_context = MagicMock()
        job_context.job.data = {"user_id": user_id, "chat_id": chat_id}
        job_context.bot.send_message = AsyncMock()

        user_dict = {
            "state": "awaiting_name",
            "selected_date": "1405/01/20",
            "selected_time": "17:00",
            "booking_started_at": (config.now_tehran() - datetime.timedelta(minutes=61)).isoformat()
        }
        job_context.user_data = user_dict

        await main.checkout_timeout_job(job_context)

        # 1. user_data must be cleared
        self.assertEqual(user_dict, {})

        # 2. Push message sent to user
        job_context.bot.send_message.assert_called_once()
        sent_args = job_context.bot.send_message.call_args[1]
        self.assertEqual(sent_args["chat_id"], chat_id)
        self.assertIn("مهلت ۱ ساعته شما برای تکمیل مراحل رزرو و ارسال فیش واریزی به پایان رسید", sent_args["text"])
        self.assertIn("آزاد شد", sent_args["text"])
        self.assertIsNotNone(sent_args.get("reply_markup"))

    async def test_completing_receipt_upload_within_60_minutes_cancels_job(self):
        """Uploading receipt within 60 minutes succeeds and cancels scheduled timeout job."""
        user_id = 77777
        update = MagicMock()
        update.effective_user.id = user_id
        update.effective_user.first_name = "کاربر"
        update.effective_user.username = "test_user_77"
        update.message.photo = [MagicMock(file_id="photo_777")]
        update.message.message_id = 100
        update.message.reply_text = AsyncMock()

        # Started 15 minutes ago
        started_at = (config.now_tehran() - datetime.timedelta(minutes=15)).isoformat()

        mock_job = MagicMock()
        context = MagicMock()
        context.user_data = {
            "state": "awaiting_receipt",
            "selected_date": "1405/01/22",
            "selected_time": "18:00",
            "session_type": "حضوری",
            "full_name": "مریم عباسی",
            "booking_started_at": started_at
        }
        context.job_queue = MagicMock()
        context.job_queue.get_jobs_by_name.return_value = [mock_job]
        context.bot.send_photo = AsyncMock()

        await main.handle_receipt(update, context)

        # 1. Scheduled job must be cancelled
        mock_job.schedule_removal.assert_called_once()

        # 2. Pending appointment created in database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM appointments WHERE date = '1405/01/22' AND time = '18:00'")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "pending")

if __name__ == "__main__":
    unittest.main()
