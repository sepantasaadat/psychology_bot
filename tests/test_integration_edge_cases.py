import io
import os
import re
import gc
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image
import jdatetime
import datetime

import config
import database
from database import SlotAlreadyBookedError
import app as flask_app
import main
from security import process_and_save_receipt


def _create_dummy_image(fmt="PNG", size=(64, 64), color="blue") -> io.BytesIO:
    """Generate in-memory valid Pillow image stream."""
    bio = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(bio, format=fmt)
    bio.seek(0)
    return bio


class TestIntegrationEdgeCases(unittest.IsolatedAsyncioTestCase):
    """
    End-to-end integration and edge-case test suite covering:
      - Flow 1: Full Web Booking Integration Flow (Persian numerals, Pillow receipt, UUID storage, Telegram dispatch)
      - Flow 2: Telegram Admin Approval Integration Flow (Multi-admin receipt deletion, fallback, schedule/menu, client alert)
      - Flow 3: Temporal Edge Cases (Nowruz rollover, 48h cancellation boundaries 49h vs 47h, stale expiration)
      - Flow 4: Security Edge Cases (Spoofed uploads rejected, RBAC admin & user cancellation enforcement)
    Compatible with both standard unittest and pytest runners.
    """

    def setUp(self):
        # Create isolated temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="test_e2e_edge_cases_")
        self.test_db_path = os.path.join(self.temp_dir, "clinic_integration.db")
        self.test_upload_dir = os.path.join(self.temp_dir, "private_uploads")
        os.makedirs(self.test_upload_dir, exist_ok=True)

        # Preserve original references
        self.original_get_connection = database.get_connection
        self.original_db_path = database.DB_PATH
        self.original_flask_db = flask_app.DATABASE
        self.original_config_upload = getattr(config, "PRIVATE_UPLOADS_DIR", None)
        self.original_flask_upload = flask_app.PRIVATE_UPLOADS_FOLDER

        # Patch database target
        database.DB_PATH = self.test_db_path
        flask_app.DATABASE = self.test_db_path
        config.PRIVATE_UPLOADS_DIR = self.test_upload_dir
        flask_app.PRIVATE_UPLOADS_FOLDER = self.test_upload_dir

        self.open_connections = []

        def get_test_connection(path=None):
            target = path if path is not None else self.test_db_path
            conn = sqlite3.connect(target)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            self.open_connections.append(conn)
            return conn

        database.get_connection = get_test_connection
        database.setup_database(self.test_db_path)

        # Seed default web user and known test user IDs for FK integrity
        with database.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
                (0, "کاربر سایت", "Website_Booking")
            )
            for uid, name in [
                (123456789, "کاربر تستی ۱"),
                (555, "مراجع تستی ۵۵۵"),
                (777, "مالک نوبت ۷۷۷"),
                (888, "کاربر متفرقه ۸۸۸")
            ]:
                conn.execute(
                    "INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
                    (uid, name, f"user_{uid}")
                )
            conn.commit()

        # Configure Flask test client
        flask_app.app.config["TESTING"] = True
        flask_app.app.config["WTF_CSRF_ENABLED"] = False
        self.client = flask_app.app.test_client()

    def tearDown(self):
        database.get_connection = self.original_get_connection
        database.DB_PATH = self.original_db_path
        flask_app.DATABASE = self.original_flask_db
        if self.original_config_upload:
            config.PRIVATE_UPLOADS_DIR = self.original_config_upload
        flask_app.PRIVATE_UPLOADS_FOLDER = self.original_flask_upload

        for conn in getattr(self, "open_connections", []):
            try:
                conn.close()
            except Exception:
                pass
        self.open_connections.clear()

        gc.collect()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # Flow 1: Full Web Booking Integration Flow
    # -------------------------------------------------------------------------
    def test_flow1_web_booking_persian_numerals_and_image_receipt(self):
        """
        Flow 1:
          - Client loads GET /booking and GET /reserve (returns HTTP 200).
          - Submits valid booking with Persian numerals ('۰۹۱۲۳۴۵۶۷۸۹') and valid Pillow image receipt.
          - Asserts database records ASCII '09123456789', status 'pending', receipt in private_uploads/ with UUID filename.
          - Asserts send_receipt_to_telegram is called with the private file path.
        """
        # 1. Verify GET /booking and GET /reserve
        res_booking = self.client.get("/booking")
        self.assertEqual(res_booking.status_code, 200)
        self.assertIn("رزرو نوبت", res_booking.data.decode("utf-8"))

        res_reserve = self.client.get("/reserve")
        self.assertEqual(res_reserve.status_code, 200)
        self.assertIn("رزرو نوبت", res_reserve.data.decode("utf-8"))

        # 2. Prepare valid future date and Persian phone input
        valid_dates = config.get_upcoming_working_days(5, is_admin=False)
        target_date = valid_dates[2]
        target_time = "17:00"
        persian_phone = "۰۹۱۲۳۴۵۶۷۸۹"
        full_name = "سارا احمدی"

        valid_receipt = _create_dummy_image(fmt="PNG", size=(90, 90), color="green")

        # 3. Post to /booking with mocked Telegram forwarding
        with patch.object(flask_app, "send_receipt_to_telegram") as mock_send_telegram:
            response = self.client.post(
                "/booking",
                data={
                    "date": target_date,
                    "time": target_time,
                    "full_name": full_name,
                    "phone": persian_phone,
                    "session_type": "آنلاین",
                    "receipt": (valid_receipt, "user_receipt.png")
                },
                content_type="multipart/form-data",
                follow_redirects=False
            )

            # Redirects on success
            self.assertEqual(response.status_code, 302)
            mock_send_telegram.assert_called_once()

            # Verify arguments passed to send_receipt_to_telegram
            app_id, name_phone_arg, d_arg, t_arg, stype_arg, saved_filepath = mock_send_telegram.call_args[0]
            self.assertEqual(d_arg, target_date)
            self.assertEqual(t_arg, target_time)
            self.assertEqual(stype_arg, "آنلاین")
            self.assertIn("09123456789", name_phone_arg, "Phone sent to Telegram must be normalized ASCII")
            self.assertNotIn("۰۹۱۲۳۴۵۶۷۸۹", name_phone_arg)

        # 4. Verify database persistence
        app_record = database.get_appointment(app_id)
        self.assertIsNotNone(app_record, "Appointment must exist in database")
        # Record structure: (client_id, date, time, s_type, name, status, receipt_file_id, ...)
        client_id, saved_date, saved_time, saved_type, saved_name, saved_status = app_record[:6]
        saved_receipt_path = app_record[7] if len(app_record) > 7 else saved_filepath

        self.assertEqual(client_id, 0, "Web bookings must be anchored to web user_id=0")
        self.assertEqual(saved_date, target_date)
        self.assertEqual(saved_time, target_time)
        self.assertEqual(saved_type, "آنلاین")
        self.assertEqual(saved_status, "pending")
        self.assertIn("09123456789", saved_name, "Stored full_name must contain normalized ASCII digits")
        self.assertNotIn("۰۹۱۲۳۴۵۶۷۸۹", saved_name, "Stored full_name must not contain Persian numerals")

        # 5. Verify receipt storage security (UUID filename, in private_uploads/, verified image)
        self.assertTrue(os.path.exists(saved_filepath), f"File {saved_filepath} must exist on disk")
        self.assertTrue(saved_filepath.startswith(self.test_upload_dir), "Receipt must reside in private_uploads/")
        self.assertFalse("static" in saved_filepath, "Receipt must not be in public static directory")

        filename = os.path.basename(saved_filepath)
        self.assertRegex(filename, r"^[0-9a-f]{32}\.jpg$", "Filename must be 32-char UUID hex with .jpg extension")

        with Image.open(saved_filepath) as opened_img:
            self.assertEqual(opened_img.format, "JPEG")
            self.assertEqual(opened_img.size, (90, 90))

    # -------------------------------------------------------------------------
    # Flow 2: Telegram Admin Approval Integration Flow
    # -------------------------------------------------------------------------
    async def test_flow2_telegram_admin_approval_workflow_multi_admin_notifications(self):
        """
        Flow 2:
          - Pending appointment approved by Admin A ('approve_{app_id}').
          - Asserts status is updated to 'confirmed'.
          - Asserts other admins in ADMIN_IDS have their receipt message deleted and receive 7-day schedule & main menu.
          - Asserts client receives confirmation message.
          - Asserts admin_receipt_messages tracking rows are cleaned up.
        """
        client_id = 123456789
        client_name = "مهدی کریمی"
        app_date = "1405/03/15"
        app_time = "18:00"

        # Create pending appointment
        app_id = database.add_pending_appointment(
            user_id=client_id,
            date=app_date,
            time=app_time,
            session_type="حضوری",
            full_name=client_name,
            receipt_file_id="receipt_test.jpg"
        )

        admin_a = config.MAIN_ADMIN_ID
        other_admins = [a for a in config.ADMIN_IDS if a != admin_a]
        self.assertTrue(len(other_admins) >= 1, "Must have at least one other admin in ADMIN_IDS")

        # Record receipt messages sent to all admins
        database.save_admin_receipt_message(app_id, admin_a, 9001)
        for idx, other_admin_id in enumerate(other_admins, start=2):
            database.save_admin_receipt_message(app_id, other_admin_id, 9000 + idx)

        # Mock Admin A approving the appointment
        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        query.message.caption = "درخواست نوبت جدید"
        query.message.message_id = 9001
        query.message.chat_id = admin_a
        query.from_user.id = admin_a
        update.callback_query = query
        update.effective_user.id = admin_a
        update.effective_user.username = "clinic_admin_a"

        context = MagicMock()
        context.user_data = {"current_step": "reviewing"}
        context.bot.send_message = AsyncMock()
        context.bot.delete_message = AsyncMock()
        context.bot.edit_message_reply_markup = AsyncMock()

        # Execute handler
        await main.button_handler(update, context)

        # 1. Verify status updated to 'confirmed'
        app_info = database.get_appointment(app_id)
        self.assertEqual(app_info[5], "confirmed", "Appointment status must be confirmed in database")

        # 2. Verify Admin A caption updated and session reset
        query.edit_message_caption.assert_called_once()
        self.assertIn("تایید قطعی شد", query.edit_message_caption.call_args[1]["caption"])
        self.assertIsNone(query.edit_message_caption.call_args[1]["reply_markup"])
        self.assertEqual(context.user_data, {}, "Approving admin user_data must be cleared")

        # 3. Verify other admins had their receipt message deleted and received schedule & menu
        for other_admin_id in other_admins:
            msg_id = 9000 + other_admins.index(other_admin_id) + 2
            context.bot.delete_message.assert_any_call(chat_id=other_admin_id, message_id=msg_id)

            other_admin_messages = [
                call[1]["text"] for call in context.bot.send_message.call_args_list
                if call[1].get("chat_id") == other_admin_id
            ]
            self.assertTrue(
                any("برنامه کاری ۷ روز آینده" in t for t in other_admin_messages),
                f"Other admin {other_admin_id} must receive upcoming week schedule"
            )
            self.assertTrue(
                any("منوی اصلی" in t for t in other_admin_messages),
                f"Other admin {other_admin_id} must receive main menu"
            )

        # 4. Verify client received confirmation message
        client_calls = [
            call[1] for call in context.bot.send_message.call_args_list
            if call[1].get("chat_id") == client_id
        ]
        self.assertEqual(len(client_calls), 1, "Client must receive exactly one confirmation message")
        client_text = client_calls[0]["text"]
        self.assertIn("با موفقیت قطعی گردید", client_text)
        self.assertIn(app_date, client_text)
        self.assertIn(app_time, client_text)
        self.assertIn(client_name, client_text)

        # 5. Verify receipt message tracking deleted from DB
        self.assertEqual(database.get_admin_receipt_messages(app_id), [])

    async def test_flow2_telegram_admin_approval_fallback_when_delete_fails(self):
        """
        Flow 2 Edge Case:
          - If Telegram delete_message fails (e.g. message > 48h or deleted),
            system falls back to edit_message_reply_markup(reply_markup=None).
        """
        client_id = 123456789
        app_id = database.add_pending_appointment(
            user_id=client_id,
            date="1405/03/16",
            time="19:00",
            session_type="حضوری",
            full_name="مراجع تست فال‌بک",
            receipt_file_id="rec_fb.jpg"
        )

        admin_a = config.MAIN_ADMIN_ID
        admin_b = config.SECOND_ADMIN_ID
        database.save_admin_receipt_message(app_id, admin_a, 7001)
        database.save_admin_receipt_message(app_id, admin_b, 7002)

        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        query.message.caption = "رسید"
        query.message.message_id = 7001
        query.message.chat_id = admin_a
        update.callback_query = query
        update.effective_user.id = admin_a

        context = MagicMock()
        context.user_data = {}
        context.bot.send_message = AsyncMock()
        context.bot.delete_message = AsyncMock(side_effect=Exception("Telegram deleteMessage failed"))
        context.bot.edit_message_reply_markup = AsyncMock()

        await main.button_handler(update, context)

        # Verify fallback button stripping was attempted
        context.bot.edit_message_reply_markup.assert_any_call(
            chat_id=admin_b,
            message_id=7002,
            reply_markup=None
        )

        # Status still updated cleanly to confirmed
        self.assertEqual(database.get_appointment(app_id)[5], "confirmed")

    # -------------------------------------------------------------------------
    # Flow 3: Temporal Edge Cases
    # -------------------------------------------------------------------------
    def test_flow3_nowruz_boundary_rollover_and_cross_year_scheduling(self):
        """
        Flow 3:
          - Nowruz boundary rollover: verify appointments can be scheduled across year boundary (1405 to 1406+)
            without hardcoded year exceptions.
          - Verified with admin and regular user advance notice windows.
          - Verified arbitrary future year transition (1410 to 1411).
        """
        ref_esfand_end = "1405/12/28"  # Friday (weekday 6)

        # Admin gets today and tomorrow across the boundary
        admin_days = config.get_upcoming_working_days(5, is_admin=True, reference_date=ref_esfand_end)
        expected_admin = [
            "1405/12/29",  # Saturday
            "1406/01/01",  # Sunday
            "1406/01/02",  # Monday
            "1406/01/03",  # Tuesday
            "1406/01/04"   # Wednesday
        ]
        self.assertEqual(admin_days, expected_admin)

        # Regular user skips today and tomorrow (starts directly on 1406/01/01)
        user_days = config.get_upcoming_working_days(5, is_admin=False, reference_date=ref_esfand_end)
        expected_user = [
            "1406/01/01",
            "1406/01/02",
            "1406/01/03",
            "1406/01/04",
            "1406/01/07"   # Saturday next week
        ]
        self.assertEqual(user_days, expected_user)

        # Verify appointment scheduling on both sides of Nowruz boundary in DB
        app_esfand = database.add_confirmed_appointment(
            user_id=555,
            date="1405/12/29",
            time="16:00",
            session_type="حضوری",
            full_name="مراجع سال کهنه",
            receipt_file_id="rec_1405"
        )
        app_farvardin = database.add_confirmed_appointment(
            user_id=777,
            date="1406/01/01",
            time="16:00",
            session_type="آنلاین",
            full_name="مراجع سال نو",
            receipt_file_id="rec_1406"
        )

        self.assertIsNotNone(app_esfand)
        self.assertIsNotNone(app_farvardin)
        self.assertEqual(database.get_appointment(app_esfand)[1], "1405/12/29")
        self.assertEqual(database.get_appointment(app_farvardin)[1], "1406/01/01")

        # Double-booking the same Nowruz slot is prevented
        with self.assertRaises(SlotAlreadyBookedError):
            database.add_pending_appointment(
                user_id=888,
                date="1406/01/01",
                time="16:00",
                session_type="حضوری",
                full_name="مراجع متداخل",
                receipt_file_id="rec_conflict"
            )

        # Verify arbitrary future year transition (1410 to 1411) without hardcoding
        future_ref = "1410/12/28"
        future_days = config.get_upcoming_working_days(3, is_admin=True, reference_date=future_ref)
        self.assertTrue(all(d.startswith("1410/") or d.startswith("1411/") for d in future_days))

    async def test_flow3_48_hour_cancellation_threshold_exact_boundaries(self):
        """
        Flow 3:
          - 48-hour cancellation threshold:
            * Exactly 49 hours before: cancellation allowed (appointment deleted, admins notified).
            * Exactly 47 hours before: cancellation rejected (appointment remains confirmed, no admin alert).
        """
        ref_now = jdatetime.datetime(1405, 6, 15, 10, 0)

        # 1. Exactly 49 hours before: 1405/06/17 11:00
        eligible_49, reason_49 = main.can_cancel_appointment("1405/06/17", "11:00", now=ref_now)
        self.assertTrue(eligible_49, "49 hours before session must be eligible for cancellation")
        self.assertEqual(reason_49, "ok")

        app_id_49 = database.add_confirmed_appointment(
            user_id=555,
            date="1405/06/17",
            time="11:00",
            session_type="حضوری",
            full_name="مراجع ۴۹ ساعت",
            receipt_file_id="rec_49"
        )

        # Trigger user cancellation callback at 49h mark
        update_49 = MagicMock()
        query_49 = MagicMock()
        query_49.data = f"user_cancel_{app_id_49}"
        query_49.answer = AsyncMock()
        query_49.edit_message_text = AsyncMock()
        update_49.callback_query = query_49
        update_49.effective_user.id = 555

        context_49 = MagicMock()
        context_49.bot.send_message = AsyncMock()

        with patch("main.get_current_jalali_datetime", return_value=ref_now):
            await main.user_cancel_callback(update_49, context_49)

        # Appointment must be deleted
        self.assertIsNone(database.get_appointment(app_id_49), "Appointment must be deleted from DB")
        query_49.edit_message_text.assert_called_once()
        self.assertIn("با موفقیت لغو گردید", query_49.edit_message_text.call_args[0][0])
        # Admins must be notified
        self.assertTrue(context_49.bot.send_message.called)
        admin_recipients = [call[1]["chat_id"] for call in context_49.bot.send_message.call_args_list]
        for admin_id in config.ADMIN_IDS:
            self.assertIn(admin_id, admin_recipients)

        # 2. Exactly 47 hours before: 1405/06/17 09:00
        eligible_47, reason_47 = main.can_cancel_appointment("1405/06/17", "09:00", now=ref_now)
        self.assertFalse(eligible_47, "47 hours before session must be rejected (< 48 hours)")
        self.assertEqual(reason_47, "within_48_hours")

        app_id_47 = database.add_confirmed_appointment(
            user_id=555,
            date="1405/06/17",
            time="09:00",
            session_type="حضوری",
            full_name="مراجع ۴۷ ساعت",
            receipt_file_id="rec_47"
        )

        update_47 = MagicMock()
        query_47 = MagicMock()
        query_47.data = f"user_cancel_{app_id_47}"
        query_47.answer = AsyncMock()
        query_47.edit_message_text = AsyncMock()
        update_47.callback_query = query_47
        update_47.effective_user.id = 555

        context_47 = MagicMock()
        context_47.bot.send_message = AsyncMock()

        with patch("main.get_current_jalali_datetime", return_value=ref_now):
            await main.user_cancel_callback(update_47, context_47)

        # Appointment must remain confirmed and NOT deleted
        app_record_47 = database.get_appointment(app_id_47)
        self.assertIsNotNone(app_record_47)
        self.assertEqual(app_record_47[5], "confirmed", "Appointment status must remain confirmed")

        query_47.edit_message_text.assert_called_once()
        self.assertIn("حداکثر تا ۴۸ ساعت پیش از موعد", query_47.edit_message_text.call_args[0][0])
        # Admins must NOT receive cancellation alert
        context_47.bot.send_message.assert_not_called()

    def test_flow3_stale_pending_expiration_and_slot_release(self):
        """
        Flow 3:
          - Stale pending expiration: verified appointment is expired and slot immediately becomes available.
        """
        now_tehran = datetime.datetime.now(config.TEHRAN_TZ)
        stale_created = (now_tehran - datetime.timedelta(hours=3)).isoformat()
        fresh_created = (now_tehran - datetime.timedelta(minutes=25)).isoformat()

        target_date = "1405/07/20"
        target_time = "17:00"

        # Stale pending appointment occupying target_date target_time
        stale_id = database.add_pending_appointment(
            user_id=555,
            date=target_date,
            time=target_time,
            session_type="حضوری",
            full_name="مراجع معلق قدیمی",
            receipt_file_id="rec_stale.jpg",
            created_at=stale_created
        )

        # Fresh pending appointment on different slot
        fresh_id = database.add_pending_appointment(
            user_id=777,
            date=target_date,
            time="18:00",
            session_type="آنلاین",
            full_name="مراجع معلق جدید",
            receipt_file_id="rec_fresh.jpg",
            created_at=fresh_created
        )

        # Prior to expiration, re-booking target slot raises SlotAlreadyBookedError
        with self.assertRaises(SlotAlreadyBookedError):
            database.add_pending_appointment(
                user_id=888,
                date=target_date,
                time=target_time,
                session_type="آنلاین",
                full_name="مراجع متقاضی همزمان",
                receipt_file_id="rec_new.jpg"
            )

        # Expire stale appointments with 2-hour timeout
        expired_count = database.expire_stale_pending_appointments(timeout_hours=2)
        self.assertEqual(expired_count, 1)

        # Verify statuses
        self.assertEqual(database.get_appointment(stale_id)[5], "expired")
        self.assertEqual(database.get_appointment(fresh_id)[5], "pending")

        # Immediately after expiration, slot becomes rebookable
        new_app_id = database.add_pending_appointment(
            user_id=888,
            date=target_date,
            time=target_time,
            session_type="آنلاین",
            full_name="مراجع جدید پس از انقضا",
            receipt_file_id="rec_new.jpg"
        )
        self.assertIsNotNone(new_app_id)
        self.assertEqual(database.get_appointment(new_app_id)[5], "pending")

    # -------------------------------------------------------------------------
    # Flow 4: Security Edge Cases
    # -------------------------------------------------------------------------
    def test_flow4_spoofed_text_and_script_uploads_rejected_with_http_400(self):
        """
        Flow 4:
          - Uploading a text/script payload disguised as .png or .jpg via web receives HTTP 400
            with flash warning and writes no record.
        """
        valid_date = config.get_upcoming_working_days(5, is_admin=False)[2]
        valid_time = "18:00"

        spoofed_payloads = [
            (b"<?php system($_GET['cmd']); ?>", "shell.php.jpg"),
            (b"<html><script>alert('xss_attack')</script></html>", "exploit.png"),
            (b"MZ\x90\x00\x03\x00\x00\x00BinaryExeDisguisedAsPic", "trojan.jpg"),
            (b"Plain text note stating I paid the fee.", "receipt.png")
        ]

        for payload, fake_filename in spoofed_payloads:
            with self.subTest(filename=fake_filename):
                response = self.client.post(
                    "/booking",
                    data={
                        "date": valid_date,
                        "time": valid_time,
                        "full_name": "مهاجم تستی",
                        "phone": "09129998877",
                        "session_type": "حضوری",
                        "receipt": (io.BytesIO(payload), fake_filename)
                    },
                    content_type="multipart/form-data"
                )

                # HTTP 400 must be returned
                self.assertEqual(response.status_code, 400)
                resp_text = response.data.decode("utf-8")
                self.assertTrue(
                    "تصویر" in resp_text or "نامعتبر" in resp_text,
                    f"Expected flash warning regarding invalid image, got: {resp_text}"
                )

        # Verify zero records written to database for this applicant
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM appointments WHERE full_name LIKE '%مهاجم%'")
        count = cur.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0, "No appointment records must be stored for spoofed uploads")

        # Verify no files were stored in private_uploads
        stored_files = os.listdir(self.test_upload_dir)
        self.assertEqual(len(stored_files), 0, "No files should be written to private_uploads on rejection")

    async def test_flow4_unauthorized_admin_callback_blocked_and_state_preserved(self):
        """
        Flow 4:
          - Unauthorized admin callback attempts are blocked.
          - State in database remains pending; no notifications are dispatched.
        """
        app_id = database.add_pending_appointment(
            user_id=123456789,
            date="1405/04/10",
            time="17:00",
            session_type="آنلاین",
            full_name="مراجع تست امنیت",
            receipt_file_id="rec_sec.jpg"
        )

        intruder_id = 99999999
        self.assertNotIn(intruder_id, config.ADMIN_IDS)

        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        update.callback_query = query
        update.effective_user.id = intruder_id

        context = MagicMock()
        context.bot.send_message = AsyncMock()
        context.bot.delete_message = AsyncMock()

        # Attempt approve as intruder
        await main.button_handler(update, context)

        # Must be blocked with alert
        query.answer.assert_called_with("⛔ شما دسترسی مدیریت به این عملیات را ندارید.", show_alert=True)
        # DB status must remain 'pending'
        self.assertEqual(database.get_appointment(app_id)[5], "pending")
        # No messages sent or deleted
        context.bot.send_message.assert_not_called()
        context.bot.delete_message.assert_not_called()

        # Attempt reject as intruder
        query.data = f"reject_{app_id}"
        query.answer.reset_mock()
        await main.button_handler(update, context)

        query.answer.assert_called_with("⛔ شما دسترسی مدیریت به این عملیات را ندارید.", show_alert=True)
        self.assertEqual(database.get_appointment(app_id)[5], "pending")

    async def test_flow4_unauthorized_user_cancellation_of_others_appointment_blocked(self):
        """
        Flow 4:
          - User attempting to cancel another user's appointment is blocked with alert.
          - Appointment remains confirmed and admins are not alerted.
        """
        owner_id = 777
        intruder_id = 888

        app_id = database.add_confirmed_appointment(
            user_id=owner_id,
            date="1405/04/20",
            time="19:00",
            session_type="حضوری",
            full_name="مالک واقعی",
            receipt_file_id="rec_owner"
        )

        update = MagicMock()
        query = MagicMock()
        query.data = f"user_cancel_{app_id}"
        query.answer = AsyncMock()
        update.callback_query = query
        update.effective_user.id = intruder_id

        context = MagicMock()
        context.bot.send_message = AsyncMock()

        await main.user_cancel_callback(update, context)

        query.answer.assert_called_with("⛔ شما مجاز به لغو این نوبت نیستید.", show_alert=True)
        # Appointment remains intact in DB
        app_record = database.get_appointment(app_id)
        self.assertIsNotNone(app_record)
        self.assertEqual(app_record[5], "confirmed")
        context.bot.send_message.assert_not_called()


# -----------------------------------------------------------------------------
# Pytest Fixture Verification Functions
# Executed specifically when running under pytest to assert fixture integration.
# -----------------------------------------------------------------------------

def test_pytest_fixture_web_booking_persian_flow(flask_client, isolated_db, monkeypatch):
    """
    Assert full web booking flow with Persian numerals using pytest conftest fixtures.
    """
    target_date = config.get_upcoming_working_days(5, is_admin=False)[3]
    target_time = "19:00"
    img_stream = _create_dummy_image(fmt="PNG", size=(50, 50), color="orange")

    mock_send = MagicMock()
    monkeypatch.setattr("app.send_receipt_to_telegram", mock_send)

    res = flask_client.post(
        "/booking",
        data={
            "date": target_date,
            "time": target_time,
            "full_name": "پریسا محمدی",
            "phone": "۰۹۱۲۷۷۷۸۸۹۹",
            "session_type": "حضوری",
            "receipt": (img_stream, "pytest_receipt.png")
        },
        content_type="multipart/form-data",
        follow_redirects=False
    )

    assert res.status_code == 302
    assert mock_send.called

    app_id = mock_send.call_args[0][0]
    app_record = database.get_appointment(app_id)
    assert app_record is not None
    assert app_record[5] == "pending"
    assert "09127778899" in app_record[4]
    assert "۰۹۱۲۷۷۷۸۸۹۹" not in app_record[4]


def test_pytest_fixture_admin_approval_and_multi_admin_dispatch(mock_telegram_bot, isolated_db):
    """
    Assert Telegram admin approval and multi-admin message dispatch using pytest fixtures.
    """
    import asyncio

    async def _run():
        client_id = 999111
        # Ensure client exists in DB for foreign key constraint
        with isolated_db.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
                (client_id, "کاربر تست پای‌تست", "pytest_user")
            )
            conn.commit()

        app_id = database.add_pending_appointment(
            user_id=client_id,
            date="1405/05/10",
            time="16:00",
            session_type="آنلاین",
            full_name="کاربر تست پای‌تست",
            receipt_file_id="pytest_rec.jpg"
        )

        admin_a = config.MAIN_ADMIN_ID
        admin_b = config.SECOND_ADMIN_ID
        database.save_admin_receipt_message(app_id, admin_a, 4001)
        database.save_admin_receipt_message(app_id, admin_b, 4002)

        update = MagicMock()
        query = MagicMock()
        query.data = f"approve_{app_id}"
        query.answer = AsyncMock()
        query.edit_message_caption = AsyncMock()
        query.message.caption = "درخواست نوبت"
        query.message.message_id = 4001
        query.message.chat_id = admin_a
        update.callback_query = query
        update.effective_user.id = admin_a

        context = mock_telegram_bot.context

        await main.button_handler(update, context)

        # Database updated
        app_info = database.get_appointment(app_id)
        assert app_info[5] == "confirmed"

        # Message deleted for other admin
        context.bot.delete_message.assert_called_with(chat_id=admin_b, message_id=4002)

        # Client notified
        client_calls = [
            call for call in context.bot.send_message.call_args_list
            if call[1].get("chat_id") == client_id
        ]
        assert len(client_calls) == 1
        assert "با موفقیت قطعی گردید" in client_calls[0][1]["text"]

    asyncio.run(_run())


def test_pytest_fixture_temporal_and_security(flask_client, isolated_db):
    """
    Assert spoofed file rejection and Nowruz rollover under pytest conftest fixtures.
    """
    valid_date = config.get_upcoming_working_days(5, is_admin=False)[2]

    # Spoofed upload
    res = flask_client.post(
        "/booking",
        data={
            "date": valid_date,
            "time": "17:00",
            "full_name": "مهاجم پای‌تست",
            "phone": "09121112233",
            "session_type": "حضوری",
            "receipt": (io.BytesIO(b"<script>alert(1)</script>"), "script.jpg")
        },
        content_type="multipart/form-data"
    )
    assert res.status_code == 400

    with isolated_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM appointments WHERE full_name LIKE '%مهاجم پای‌تست%'")
        assert cur.fetchone()[0] == 0

    # Nowruz boundary
    days = config.get_upcoming_working_days(4, is_admin=True, reference_date="1405/12/28")
    assert days[0] == "1405/12/29"
    assert days[1] == "1406/01/01"


if __name__ == "__main__":
    unittest.main()
