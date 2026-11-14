import io
import os
import re
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image

import config
import database
import main
import app

class TestUploadSecurityAndRBAC(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = database.get_connection
        self.test_db = f"test_clinic_sec_{os.getpid()}.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        def get_test_connection():
            return sqlite3.connect(self.test_db)

        database.get_connection = get_test_connection
        database.setup_database()

        # Temporary folder for testing uploads
        self.temp_upload_dir = tempfile.mkdtemp(prefix="test_private_uploads_")
        self.created_files = []

        # Configure Flask app for testing
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.app.test_client()

    def tearDown(self):
        database.get_connection = self.original_db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.temp_upload_dir):
            shutil.rmtree(self.temp_upload_dir, ignore_errors=True)
        for f in self.created_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def _create_dummy_image(self, fmt="PNG", size=(50, 50), color="blue"):
        bio = io.BytesIO()
        img = Image.new("RGB", size, color=color)
        img.save(bio, format=fmt)
        bio.seek(0)
        return bio

    def test_spoofed_image_rejected(self):
        """
        Uploading text/script content disguised as .jpg fails validation
        and returns HTTP 400 with a flash error message.
        """
        from security import process_and_save_receipt

        # 1. Direct validation via process_and_save_receipt
        spoofed_payload = b"<html><script>alert('malicious payload')</script></html>"
        with self.assertRaises(ValueError) as ctx:
            process_and_save_receipt(spoofed_payload, dest_dir=self.temp_upload_dir)
        self.assertTrue(
            "corrupted" in str(ctx.exception).lower() or "invalid" in str(ctx.exception).lower() or "unsupported" in str(ctx.exception).lower(),
            f"Expected corruption/invalid error, got: {ctx.exception}"
        )

        # 2. Uploading spoofed file through Flask /booking endpoint
        valid_date = config.get_upcoming_working_days(1, is_admin=False)[0]
        response = self.client.post(
            '/booking',
            data={
                'date': valid_date,
                'time': '17:00',
                'full_name': 'مهاجم سایبری',
                'phone': '09120000000',
                'session_type': 'آنلاین',
                'receipt': (io.BytesIO(spoofed_payload), 'fake_receipt.jpg')
            },
            content_type='multipart/form-data'
        )

        # Should be rejected with HTTP 400
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            "نامعتبر" in response.data.decode('utf-8') or "تصویر" in response.data.decode('utf-8'),
            "User-facing error message must warn about invalid image format"
        )

        # Verify no appointment was created in the database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE full_name LIKE '%مهاجم%'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0, "No appointment record should be saved for invalid receipt")

    def test_valid_image_stored_in_private_uploads_with_uuid(self):
        """
        Valid Pillow image upload saves in private_uploads/ with UUID filename and .jpg extension.
        """
        from security import process_and_save_receipt

        valid_png = self._create_dummy_image(fmt="PNG", size=(64, 64), color="green")
        saved_path = process_and_save_receipt(valid_png, dest_dir=self.temp_upload_dir)
        self.created_files.append(saved_path)

        self.assertTrue(os.path.exists(saved_path), f"File {saved_path} must exist on disk")
        
        # Verify stored inside designated private directory
        self.assertTrue(
            saved_path.startswith(self.temp_upload_dir) or "private_uploads" in saved_path,
            f"File must be stored in private folder, got: {saved_path}"
        )

        # Filename must be UUID4 hex with .jpg extension
        basename = os.path.basename(saved_path)
        self.assertRegex(basename, r"^[0-9a-f]{32}\.jpg$", f"Filename must be UUID hex + .jpg: {basename}")

        # Verify image integrity and clean re-encoding
        with Image.open(saved_path) as verified_img:
            self.assertEqual(verified_img.format, "JPEG")
            self.assertEqual(verified_img.mode, "RGB")
            self.assertEqual(verified_img.size, (64, 64))

        # Test end-to-end booking upload with mock telegram notification
        valid_jpeg = self._create_dummy_image(fmt="JPEG", size=(80, 80), color="purple")
        valid_date = config.get_upcoming_working_days(1, is_admin=False)[0]
        with patch.object(app, 'send_receipt_to_telegram') as mock_send:
            res = self.client.post(
                '/booking',
                data={
                    'date': valid_date,
                    'time': '18:00',
                    'full_name': 'سارا احمدی',
                    'phone': '09121111111',
                    'session_type': 'حضوری',
                    'receipt': (valid_jpeg, 'my_receipt.jpg')
                },
                content_type='multipart/form-data',
                follow_redirects=False
            )
            self.assertEqual(res.status_code, 302)
            mock_send.assert_called_once()
            called_filepath = mock_send.call_args[0][5]
            self.created_files.append(called_filepath)
            self.assertTrue(os.path.exists(called_filepath))
            self.assertTrue("private_uploads" in called_filepath)
            self.assertFalse("static" in called_filepath, "Receipts must not reside in public static/ directory")

    async def test_unauthorized_admin_approval_blocked(self):
        """
        Non-admin user sending approve_1 callback is rejected and appointment status remains pending.
        """
        # Create a pending appointment
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (123, '1405/01/15', '17:00', 'حضوری', 'تست کاربر', 'pending', 'rec_123')
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        unauthorized_user_id = 987654321
        self.assertNotIn(unauthorized_user_id, main.ADMIN_IDS)

        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        update.callback_query = query
        update.effective_user.id = unauthorized_user_id
        update.effective_user.username = "intruder"

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()

        await main.button_handler(update, context)

        # 1. Appointment status must remain 'pending'
        app_info = database.get_appointment(app_id)
        self.assertIsNotNone(app_info)
        self.assertEqual(app_info[5], "pending", "Unauthorized user must not be able to approve appointment")

        # 2. query.answer must have received authorization denial alert
        self.assertTrue(query.answer.called)
        called_args = [str(arg) for call in query.answer.call_args_list for arg in call.args]
        self.assertTrue(
            any("دسترسی مدیریت" in a for a in called_args),
            f"Expected admin access denial message, got: {query.answer.call_args_list}"
        )

        # Repeat for reject_ action
        query.data = f"reject_{app_id}"
        query.answer.reset_mock()
        await main.button_handler(update, context)
        app_info = database.get_appointment(app_id)
        self.assertEqual(app_info[5], "pending", "Unauthorized user must not be able to reject appointment")
        called_args = [str(arg) for call in query.answer.call_args_list for arg in call.args]
        self.assertTrue(any("دسترسی مدیریت" in a for a in called_args))

    async def test_unauthorized_user_cancellation_blocked(self):
        """
        User attempting to cancel another user's appointment is rejected and appointment remains confirmed.
        """
        owner_id = 777
        intruder_id = 888
        self.assertNotIn(intruder_id, main.ADMIN_IDS)

        app_id = database.add_confirmed_appointment(
            user_id=owner_id,
            date='1405/01/20',
            time='18:00',
            session_type='حضوری',
            full_name='مالک واقعی نوبت',
            receipt_file_id='rec777'
        )

        update = MagicMock()
        query = MagicMock()
        query.data = f"user_cancel_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = intruder_id
        update.effective_user.username = "intruder_user"

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()

        await main.button_handler(update, context)

        # 1. Appointment must still exist in DB and remain confirmed
        app_info = database.get_appointment(app_id)
        self.assertIsNotNone(app_info, "Appointment must not be deleted by unauthorized user")
        self.assertEqual(app_info[5], "confirmed", "Appointment must remain confirmed")

        # 2. query.answer must have received cancellation authorization denial alert
        self.assertTrue(query.answer.called)
        called_args = [str(arg) for call in query.answer.call_args_list for arg in call.args]
        self.assertTrue(
            any("مجاز به لغو" in a for a in called_args),
            f"Expected cancellation denial message, got: {query.answer.call_args_list}"
        )

        # 3. Admins must not be notified of cancellation
        context.bot.send_message.assert_not_called()

    def test_csrf_protection_enforced(self):
        """
        When WTF_CSRF_ENABLED is True, submitting a form without valid CSRF token is rejected with HTTP 400.
        """
        app.app.config['WTF_CSRF_ENABLED'] = True
        valid_date = config.get_upcoming_working_days(1, is_admin=False)[0]
        try:
            res = self.client.post(
                '/booking',
                data={
                    'date': valid_date,
                    'time': '17:00',
                    'full_name': 'تست بدون توکن',
                    'phone': '09123333333',
                    'session_type': 'حضوری',
                }
            )
            self.assertEqual(res.status_code, 400)
        finally:
            app.app.config['WTF_CSRF_ENABLED'] = False

if __name__ == '__main__':
    unittest.main()
