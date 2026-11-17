import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sqlite3
import jdatetime
import config
import database
import main
from telegram import InlineKeyboardMarkup

class TestBotWorkflowFixes(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = database.get_connection
        self.test_db = "test_bot_workflow_fixes.db"
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

    # 1. Issue 1: none_callback
    async def test_none_callback_answers_query_with_alert(self):
        update = MagicMock()
        query = MagicMock()
        query.data = "none"
        query.answer = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        await main.none_callback(update, context)

        query.answer.assert_awaited_once()
        args, kwargs = query.answer.call_args
        self.assertTrue(kwargs.get("show_alert"))
        self.assertIn("تکمیل است", args[0])

    # 2. Issue 2: safe_edit_message fallback on media message
    async def test_safe_edit_message_fallback_on_photo_message(self):
        query = MagicMock()
        query.edit_message_text = AsyncMock(side_effect=Exception("BadRequest: There is no text in the message to edit"))
        query.delete_message = AsyncMock()
        query.message = MagicMock()
        query.message.reply_text = AsyncMock()

        await main.safe_edit_message(query, "تست متن جدید")

        query.delete_message.assert_awaited_once()
        query.message.reply_text.assert_awaited_once_with("تست متن جدید", reply_markup=None)

    # 3. Issue 2: safe_edit_review_caption fallback on text message
    async def test_safe_edit_review_caption_fallback_on_text_message(self):
        query = MagicMock()
        query.edit_message_caption = AsyncMock(side_effect=Exception("BadRequest: Message has no caption to edit"))
        query.edit_message_text = AsyncMock()
        query.message = MagicMock()
        query.message.caption = None
        query.message.text = "کپشن اولیه"

        await main.safe_edit_review_caption(query, "تایید شد")

        query.edit_message_text.assert_awaited_once()
        called_text = query.edit_message_text.call_args[1]["text"]
        self.assertIn("تایید شد", called_text)

    # 4. Issue 3: admin_view_pending displays photo for Telegram file_id
    async def test_admin_view_pending_telegram_file_id(self):
        # Insert appointment with telegram file_id
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (99, '1405/01/20', '17:00', 'حضوری', 'کاربر تستی', 'pending', 'AgACAgIAAxkBAAI')
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        update = MagicMock()
        query = MagicMock()
        query.data = f"admin_view_pending_{app_id}"
        query.answer = AsyncMock()
        query.delete_message = AsyncMock()
        update.callback_query = query
        update.effective_user.id = main.MAIN_ADMIN_ID

        context = MagicMock()
        context.bot.send_photo = AsyncMock()

        await main.admin_view_pending_callback(update, context)

        context.bot.send_photo.assert_awaited_once()
        call_kwargs = context.bot.send_photo.call_args[1]
        self.assertEqual(call_kwargs["photo"], "AgACAgIAAxkBAAI")
        self.assertIn(f"مشخصات نوبت در انتظار #{app_id}", call_kwargs["caption"])

    # 5. Issue 4: text in awaiting_receipt state reminds user without dropping state
    async def test_text_in_awaiting_receipt_state_reminds_user(self):
        update = MagicMock()
        update.effective_user.id = 555
        update.message.text = "شماره کارت چی بود؟"
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            "state": "awaiting_receipt",
            "selected_date": "1405/01/20",
            "selected_time": "18:00",
            "full_name": "نام مراجع"
        }

        await main.handle_text(update, context)

        self.assertEqual(context.user_data.get("state"), "awaiting_receipt")
        update.message.reply_text.assert_called_once()
        reply_msg = update.message.reply_text.call_args[0][0]
        self.assertIn("منتظر دریافت تصویر یا فایل فیش", reply_msg)

    # 6. Issue 5: handle_receipt accepts document uploads (PDF/file)
    async def test_handle_receipt_accepts_document_upload(self):
        user_id = 444
        update = MagicMock()
        update.effective_user.id = user_id
        update.effective_user.first_name = "کاربر"
        update.effective_user.username = "client_doc"
        update.message.photo = None
        update.message.document = MagicMock(file_id="doc_pdf_1234")
        update.message.message_id = 901
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            "state": "awaiting_receipt",
            "selected_date": "1405/01/22",
            "selected_time": "19:00",
            "session_type": "حضوری",
            "full_name": "سارا کمالی"
        }
        sent_mock = MagicMock(message_id=7711)
        context.bot.send_document = AsyncMock(return_value=sent_mock)

        await main.handle_receipt(update, context)

        # 1. Database has pending appointment with document file_id
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT receipt_file_id FROM appointments WHERE user_id = 444")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "doc_pdf_1234")

        # 2. Admin received document
        context.bot.send_document.assert_awaited()
        doc_sent = context.bot.send_document.call_args[1]["document"]
        self.assertEqual(doc_sent, "doc_pdf_1234")

    # 7. Issue 6: SlotAlreadyBookedError handled in handle_receipt
    async def test_handle_receipt_catches_slot_already_booked(self):
        user_id = 333
        update = MagicMock()
        update.effective_user.id = user_id
        update.effective_user.first_name = "کاربر"
        update.effective_user.username = "client_race"
        update.message.photo = [MagicMock(file_id="photo_race")]
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            "state": "awaiting_receipt",
            "selected_date": "1405/01/25",
            "selected_time": "17:00",
            "session_type": "حضوری",
            "full_name": "کاربر دوم"
        }

        # First appointment takes the slot
        database.add_confirmed_appointment(111, "1405/01/25", "17:00", "حضوری", "کاربر اول")

        # Second appointment tries to take the same slot
        await main.handle_receipt(update, context)

        # Session cleared and error message replied
        self.assertEqual(context.user_data, {})
        update.message.reply_text.assert_called_once()
        msg = update.message.reply_text.call_args[0][0]
        self.assertIn("این ساعت توسط مراجع دیگری رزرو گردید", msg)

    # 8. Issue 6: Admin direct booking catches SlotAlreadyBookedError
    async def test_admin_direct_booking_catches_slot_already_booked(self):
        admin_id = main.MAIN_ADMIN_ID
        update = MagicMock()
        update.effective_user.id = admin_id
        update.effective_user.first_name = "مدیر"
        update.effective_user.username = "clinic_admin"
        update.message.text = "مراجع تست"
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            "state": "awaiting_name",
            "selected_date": "1405/01/25",
            "selected_time": "18:00",
            "session_type": "حضوری"
        }

        # Slot already occupied
        database.add_confirmed_appointment(222, "1405/01/25", "18:00", "حضوری", "مراجع قبلی")

        # Admin tries to direct book the same occupied slot
        await main.handle_text(update, context)

        self.assertEqual(context.user_data, {})
        update.message.reply_text.assert_called_once()
        msg = update.message.reply_text.call_args[0][0]
        self.assertIn("خطا در ثبت مستقیم: این ساعت قبلاً رزرو شده است", msg)

    # 9. Issue 8: Name validation rejects empty, short, or non-alphabetical inputs
    async def test_handle_text_validates_name_length_and_content(self):
        update = MagicMock()
        update.effective_user.id = 666
        update.effective_user.first_name = "کاربر"
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            "state": "awaiting_name",
            "selected_date": "1405/01/20",
            "selected_time": "17:00",
            "session_type": "حضوری"
        }

        # Case A: Too short
        update.message.text = ".."
        await main.handle_text(update, context)
        self.assertEqual(context.user_data.get("state"), "awaiting_name")
        self.assertIn("حداقل ۳ حرف", update.message.reply_text.call_args[0][0])

        # Case B: Only digits / symbols
        update.message.reply_text.reset_mock()
        update.message.text = "12345"
        await main.handle_text(update, context)
        self.assertEqual(context.user_data.get("state"), "awaiting_name")
        self.assertIn("حداقل ۳ حرف", update.message.reply_text.call_args[0][0])

    # 10. Issue 9: Receipt ack includes main menu keyboard
    async def test_handle_receipt_ack_contains_main_menu_keyboard(self):
        user_id = 888
        update = MagicMock()
        update.effective_user.id = user_id
        update.effective_user.first_name = "کاربر"
        update.effective_user.username = "client_menu"
        update.message.photo = [MagicMock(file_id="photo_ack")]
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            "state": "awaiting_receipt",
            "selected_date": "1405/01/26",
            "selected_time": "16:00",
            "session_type": "حضوری",
            "full_name": "نرگس صادقی"
        }
        context.bot.send_photo = AsyncMock()

        await main.handle_receipt(update, context)

        update.message.reply_text.assert_called_once()
        reply_markup = update.message.reply_text.call_args[1].get("reply_markup")
        self.assertIsInstance(reply_markup, InlineKeyboardMarkup)
        btn_data = [btn.callback_data for row in reply_markup.inline_keyboard for btn in row if btn.callback_data]
        self.assertIn("book_appointment", btn_data)

    # 11. Issue 11: type_callback has back button to hour selection
    async def test_type_callback_has_back_button_to_hour_selection(self):
        update = MagicMock()
        query = MagicMock()
        query.data = "type_حضوری"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 12345

        context = MagicMock()
        context.user_data = {'selected_date': '1405/01/15', 'selected_time': '17:00'}

        await main.type_callback(update, context)

        query.edit_message_text.assert_awaited_once()
        markup = query.edit_message_text.call_args[1].get("reply_markup")
        btn_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
        self.assertIn("date_1405/01/15", btn_data)
        self.assertIn("main_menu", btn_data)

    # 12. Issue 12: admin_delete_callback provides return to confirmed list button
    async def test_admin_delete_callback_provides_return_to_confirmed_list_button(self):
        # Insert future appointment
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (105, '1405/12/28', '19:00', 'حضوری', 'کاربر لغو ادمین', 'confirmed', 'r5')
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        update = MagicMock()
        query = MagicMock()
        query.data = f"del_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = main.MAIN_ADMIN_ID
        context = MagicMock()

        await main.admin_delete_callback(update, context)

        query.edit_message_text.assert_awaited_once()
        markup = query.edit_message_text.call_args[1].get("reply_markup")
        btn_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
        self.assertIn("admin_confirmed_list", btn_data)
        self.assertIn("admin_panel", btn_data)


if __name__ == '__main__':
    unittest.main()
