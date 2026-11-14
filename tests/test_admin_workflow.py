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

        # Verify messages sent to client and admins
        # Client: 1 confirmation
        # Other admins: 2 messages each (schedule + menu)
        # Approving admin: 2 messages (schedule + menu)
        # Total = 1 + 2*(len(ADMIN_IDS)-1) + 2 = 7 messages
        expected_total = 1 + 2 * (len(main.ADMIN_IDS) - 1) + 2
        self.assertEqual(context.bot.send_message.call_count, expected_total)

        approving_admin_calls = [
            call for call in context.bot.send_message.call_args_list
            if call[1].get("chat_id") == main.MAIN_ADMIN_ID
        ]
        self.assertEqual(len(approving_admin_calls), 2)
        self.assertIn("برنامه کاری ۷ روز آینده", approving_admin_calls[0][1]["text"])
        self.assertIn("منوی اصلی", approving_admin_calls[1][1]["text"])
        self.assertIsNotNone(approving_admin_calls[1][1]["reply_markup"])

    async def test_already_handled_appointment_triggers_schedule_and_menu(self):
        # Insert an already confirmed appointment
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (999, '1405/01/03', '17:00', 'حضوری', 'تست مراجع', 'confirmed', 'p_test')
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
        query.message.chat_id = main.SECOND_ADMIN_ID
        query.from_user.id = main.SECOND_ADMIN_ID
        update.callback_query = query
        update.effective_user.id = main.SECOND_ADMIN_ID
        update.effective_user.username = "second_admin"

        context = MagicMock()
        context.user_data = {"pending_state": "some_value"}
        context.bot.send_message = AsyncMock()

        # Call button_handler
        await main.button_handler(update, context)

        # Database appointment status must remain unchanged
        app_info = database.get_appointment(app_id)
        self.assertEqual(app_info[5], "confirmed")

        # Verify edit_message_caption was called with already handled message and reply_markup=None
        query.edit_message_caption.assert_called_once()
        self.assertIn("تعیین تکلیف شده است", query.edit_message_caption.call_args[1]["caption"])
        self.assertIsNone(query.edit_message_caption.call_args[1].get("reply_markup"))

        # Verify admin user_data was cleared
        self.assertEqual(context.user_data, {})

        # Verify messages sent to admin: 1 schedule + 1 main menu = 2 calls
        self.assertEqual(context.bot.send_message.call_count, 2)

        admin_schedule_call = context.bot.send_message.call_args_list[0]
        self.assertEqual(admin_schedule_call[1]["chat_id"], main.SECOND_ADMIN_ID)
        self.assertIn("برنامه کاری ۷ روز آینده", admin_schedule_call[1]["text"])

        admin_menu_call = context.bot.send_message.call_args_list[1]
        self.assertEqual(admin_menu_call[1]["chat_id"], main.SECOND_ADMIN_ID)
        self.assertIn("منوی اصلی", admin_menu_call[1]["text"])
        self.assertIsNotNone(admin_menu_call[1]["reply_markup"])

    async def test_missing_appointment_triggers_schedule_and_menu(self):
        # Mock Update and Context for a non-existent appointment ID
        update = MagicMock()
        query = MagicMock()
        query.data = "approve_999999"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        query.message.caption = "رسید ارسالی"
        query.message.chat_id = main.MAIN_ADMIN_ID
        query.from_user.id = main.MAIN_ADMIN_ID
        update.callback_query = query
        update.effective_user.id = main.MAIN_ADMIN_ID
        update.effective_user.username = "clinic_admin"

        context = MagicMock()
        context.user_data = {"temp": "data"}
        context.bot.send_message = AsyncMock()

        # Call button_handler
        await main.button_handler(update, context)

        # Verify caption edited and buttons stripped
        query.edit_message_caption.assert_called_once()
        self.assertIn("یافت نشد", query.edit_message_caption.call_args[1]["caption"])
        self.assertIn("reply_markup", query.edit_message_caption.call_args[1])
        self.assertIsNone(query.edit_message_caption.call_args[1]["reply_markup"])

        # Verify session cleared
        self.assertEqual(context.user_data, {})

        # Verify schedule and main menu sent
        self.assertEqual(context.bot.send_message.call_count, 2)
        schedule_call = context.bot.send_message.call_args_list[0]
        self.assertIn("برنامه کاری ۷ روز آینده", schedule_call[1]["text"])
        menu_call = context.bot.send_message.call_args_list[1]
        self.assertIn("منوی اصلی", menu_call[1]["text"])

    async def test_approval_deletes_receipt_and_notifies_other_admins(self):
        # Insert a pending appointment
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (888, '1405/01/03', '17:00', 'حضوری', 'مراجع تست', 'pending', 'p_test')
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Save receipt messages for admin 1 (approver) and admin 2 (other admin)
        database.save_admin_receipt_message(app_id, main.MAIN_ADMIN_ID, 1001)
        database.save_admin_receipt_message(app_id, main.SECOND_ADMIN_ID, 1002)

        # Mock Update and Context
        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        query.message.caption = "رسید ارسالی"
        query.message.chat_id = main.MAIN_ADMIN_ID
        query.from_user.id = main.MAIN_ADMIN_ID
        update.callback_query = query
        update.effective_user.id = main.MAIN_ADMIN_ID
        update.effective_user.username = "clinic_admin"

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()
        context.bot.delete_message = AsyncMock()

        # Call button_handler
        await main.button_handler(update, context)

        # 1. Message deletion:
        # Must delete message 1002 for SECOND_ADMIN_ID
        context.bot.delete_message.assert_called_once_with(chat_id=main.SECOND_ADMIN_ID, message_id=1002)

        # 2. Other admin messages:
        # Check messages sent to SECOND_ADMIN_ID:
        # Should receive 2 messages: 7-day schedule and main menu
        second_admin_calls = [
            call for call in context.bot.send_message.call_args_list
            if call[1].get("chat_id") == main.SECOND_ADMIN_ID
        ]
        self.assertEqual(len(second_admin_calls), 2)
        self.assertIn("برنامه کاری ۷ روز آینده", second_admin_calls[0][1]["text"])
        self.assertIn("منوی اصلی", second_admin_calls[1][1]["text"])
        self.assertIsNotNone(second_admin_calls[1][1]["reply_markup"])

        # 3. Database tracking cleanup:
        # All receipt messages for this appointment should be cleared
        self.assertEqual(database.get_admin_receipt_messages(app_id), [])

    async def test_approval_untracked_receipt_still_notifies_other_admins(self):
        # Insert a pending appointment without any records in admin_receipt_messages
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (555, '1405/01/03', '17:00', 'حضوری', 'کاربر قدیمی', 'pending', 'p_old')
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        query.message.caption = "رسید قدیمی"
        query.message.chat_id = main.MAIN_ADMIN_ID
        query.from_user.id = main.MAIN_ADMIN_ID
        update.callback_query = query
        update.effective_user.id = main.MAIN_ADMIN_ID
        update.effective_user.username = "clinic_admin"

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()
        context.bot.delete_message = AsyncMock()

        await main.button_handler(update, context)

        # delete_message should not be called because receipt was not tracked
        context.bot.delete_message.assert_not_called()

        # But SECOND_ADMIN_ID and SEPANTA_ADMIN_ID must still receive schedule and menu
        for other_admin in [main.SECOND_ADMIN_ID, main.SEPANTA_ADMIN_ID]:
            other_calls = [
                call for call in context.bot.send_message.call_args_list
                if call[1].get("chat_id") == other_admin
            ]
            self.assertEqual(len(other_calls), 2)
            self.assertIn("برنامه کاری ۷ روز آینده", other_calls[0][1]["text"])
            self.assertIn("منوی اصلی", other_calls[1][1]["text"])

    async def test_approval_delete_message_failure_falls_back_to_edit_reply_markup(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (444, '1405/01/03', '17:00', 'حضوری', 'کاربر تستی', 'pending', 'p_err')
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        database.save_admin_receipt_message(app_id, main.SECOND_ADMIN_ID, 5005)

        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        query.message.caption = "رسید تست"
        query.message.chat_id = main.MAIN_ADMIN_ID
        query.from_user.id = main.MAIN_ADMIN_ID
        update.callback_query = query
        update.effective_user.id = main.MAIN_ADMIN_ID
        update.effective_user.username = "clinic_admin"

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()
        context.bot.delete_message = AsyncMock(side_effect=Exception("Telegram deleteMessage failed"))
        context.bot.edit_message_reply_markup = AsyncMock()

        await main.button_handler(update, context)

        # verify delete_message was attempted
        context.bot.delete_message.assert_called_once_with(chat_id=main.SECOND_ADMIN_ID, message_id=5005)
        # verify fallback to edit_message_reply_markup
        context.bot.edit_message_reply_markup.assert_called_once_with(
            chat_id=main.SECOND_ADMIN_ID,
            message_id=5005,
            reply_markup=None
        )

        # verify other admin still received schedule and menu
        second_admin_calls = [
            call for call in context.bot.send_message.call_args_list
            if call[1].get("chat_id") == main.SECOND_ADMIN_ID
        ]
        self.assertEqual(len(second_admin_calls), 2)

    async def test_handle_receipt_saves_admin_receipt_messages(self):
        user_update = MagicMock()
        user_update.effective_user.id = 777
        user_update.effective_user.first_name = "تست"
        user_update.effective_user.username = "test_user"
        user_update.message.photo = [MagicMock(file_id="photo_123")]
        user_update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            'state': 'awaiting_receipt',
            'selected_date': '1405/01/02',
            'selected_time': '18:00',
            'session_type': 'حضوری',
            'full_name': 'نام کاربر'
        }
        
        sent_mock = MagicMock()
        sent_mock.message_id = 8888
        context.bot.send_photo = AsyncMock(return_value=sent_mock)

        await main.handle_receipt(user_update, context)

        # Verify sent_photo was called for each admin
        self.assertEqual(context.bot.send_photo.call_count, len(main.ADMIN_IDS))

        # Retrieve pending appointment id from db
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM appointments WHERE user_id = 777")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        app_id = row[0]
        conn.close()

        # Verify admin_receipt_messages has entries for all admins
        saved_msgs = database.get_admin_receipt_messages(app_id)
        self.assertEqual(len(saved_msgs), len(main.ADMIN_IDS))
        for admin_id in main.ADMIN_IDS:
            self.assertIn((admin_id, 8888), saved_msgs)

    def test_main_calls_setup_database(self):
        with unittest.mock.patch('database.setup_database') as mock_setup, \
             unittest.mock.patch('telegram.ext.Application.builder') as mock_builder:
            mock_app = MagicMock()
            mock_builder.return_value.token.return_value.build.return_value = mock_app
            main.main()
            mock_setup.assert_called_once()

    def test_web_send_receipt_saves_admin_receipt_messages(self):
        import app
        with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=b'fake_image')), \
             unittest.mock.patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"ok": True, "result": {"message_id": 9911}}
            mock_post.return_value = mock_resp

            app.send_receipt_to_telegram(55, "مراجع وب", "1405/01/01", "18:00", "حضوری", "fake.png")

            saved_msgs = database.get_admin_receipt_messages(55)
            self.assertEqual(len(saved_msgs), len(app.ADMIN_IDS))
            for admin in app.ADMIN_IDS:
                self.assertIn((admin, 9911), saved_msgs)

if __name__ == '__main__':
    unittest.main()
