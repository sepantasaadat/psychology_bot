import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import os
import sqlite3
import datetime
from zoneinfo import ZoneInfo
import jdatetime
import config
import database

TEHRAN_TZ = ZoneInfo("Asia/Tehran")

class TestRemindersAndReports(unittest.TestCase):
    def setUp(self):
        # Use an isolated test database
        self.original_get_conn = database.get_connection
        self.test_db = os.path.abspath("test_clinic_reminders.db")
        for f in [self.test_db, f"{self.test_db}-wal", f"{self.test_db}-shm"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
            
        def get_test_conn(db_path=None):
            return self.original_get_conn(db_path or self.test_db)
            
        database.get_connection = get_test_conn
        database.setup_database()

        # Insert test users
        conn = database.get_connection()
        cursor = conn.cursor()
        for uid, name in [
            (0, 'کاربر سایت'),
            (101, 'مراجع اول'),
            (102, 'مراجع دوم'),
            (103, 'مراجع سوم'),
            (104, 'مراجع چهارم'),
            (105, 'مراجع پنجم'),
            (106, 'مراجع ششم'),
        ]:
            cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)', (uid, name))
        conn.commit()
        conn.close()

    def tearDown(self):
        database.get_connection = self.original_get_conn
        for f in [self.test_db, f"{self.test_db}-wal", f"{self.test_db}-shm"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_setup_database_creates_reminder_sent_column(self):
        """Verifies that setup_database ensures appointments table has reminder_sent column."""
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(appointments)")
        columns = {row[1]: row for row in cursor.fetchall()}
        conn.close()

        self.assertIn("reminder_sent", columns)
        # Verify default is 0
        self.assertEqual(columns["reminder_sent"][4], "0")

    def test_get_appointments_due_for_reminder(self):
        """
        Verifies only confirmed appointments scheduled within the next 24 hours
        (between now and now + 24h in Asia/Tehran) with reminder_sent=0 and user_id != 0 are returned.
        """
        # Fixed reference point: 1405/01/01 12:00 (Gregorian: 2026-03-21 12:00:00 Asia/Tehran)
        ref_now = datetime.datetime(2026, 3, 21, 12, 0, 0, tzinfo=TEHRAN_TZ)

        conn = database.get_connection()
        cursor = conn.cursor()

        # 1. Confirmed, in 4 hours (1405/01/01 16:00), reminder_sent=0, user_id=101 -> DUE
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (101, '1405/01/01', '16:00', 'حضوری', 'مراجع اول', 'confirmed', 0)
        ''')
        app_id_due1 = cursor.lastrowid

        # 2. Confirmed, in 22 hours (1405/01/02 10:00), reminder_sent=0, user_id=102 -> DUE
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (102, '1405/01/02', '10:00', 'آنلاین', 'مراجع دوم', 'confirmed', 0)
        ''')
        app_id_due2 = cursor.lastrowid

        # 3. Confirmed, in 26 hours (1405/01/02 14:00) -> EXCLUDED (> 24h)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (103, '1405/01/02', '14:00', 'حضوری', 'مراجع سوم', 'confirmed', 0)
        ''')

        # 4. Confirmed, in 5 hours (1405/01/01 17:00), but reminder_sent=1 -> EXCLUDED (already sent)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (104, '1405/01/01', '17:00', 'آنلاین', 'مراجع چهارم', 'confirmed', 1)
        ''')

        # 5. Pending, in 6 hours (1405/01/01 18:00) -> EXCLUDED (status != confirmed)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (105, '1405/01/01', '18:00', 'حضوری', 'مراجع پنجم', 'pending', 0)
        ''')

        # 6. Confirmed, in 7 hours (1405/01/01 19:00), but user_id=0 (Web booking) -> EXCLUDED (user_id == 0)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (0, '1405/01/01', '19:00', 'حضوری', 'کاربر سایت 09121111111', 'confirmed', 0)
        ''')

        # 7. Confirmed, 2 hours in the past (1405/01/01 10:00) -> EXCLUDED (past appointment)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (106, '1405/01/01', '10:00', 'آنلاین', 'مراجع ششم', 'confirmed', 0)
        ''')

        conn.commit()
        conn.close()

        # Query due reminders
        due = database.get_appointments_due_for_reminder(now=ref_now)
        
        due_ids = [row[0] for row in due]
        self.assertEqual(len(due), 2)
        self.assertIn(app_id_due1, due_ids)
        self.assertIn(app_id_due2, due_ids)

        # Check tuple format: (id, user_id, date, time, full_name, session_type)
        row1 = next(r for r in due if r[0] == app_id_due1)
        self.assertEqual(row1[1], 101)
        self.assertEqual(row1[2], '1405/01/01')
        self.assertEqual(row1[3], '16:00')
        self.assertEqual(row1[4], 'مراجع اول')
        self.assertEqual(row1[5], 'حضوری')

    def test_mark_reminder_as_sent(self):
        """Verifies that mark_reminder_as_sent updates reminder_sent to 1 and refreshes updated_at."""
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (101, '1405/01/01', '18:00', 'حضوری', 'مراجع اول', 'confirmed', 0)
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        database.mark_reminder_as_sent(app_id)

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT reminder_sent, updated_at FROM appointments WHERE id = ?', (app_id,))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], 1)
        self.assertIsNotNone(row[1])

    def test_send_appointment_reminders_job(self):
        """Verifies send_appointment_reminders_job sends reminder message and marks reminder_sent=1."""
        import asyncio
        import main

        ref_now = datetime.datetime(2026, 3, 21, 12, 0, 0, tzinfo=TEHRAN_TZ)

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (101, '1405/01/01', '18:00', 'حضوری', 'دانیال اشراق', 'confirmed', 0)
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Mock context and bot
        mock_context = MagicMock()
        mock_context.bot.send_message = AsyncMock()

        with patch('database.get_appointments_due_for_reminder', return_value=[(app_id, 101, '1405/01/01', '18:00', 'دانیال اشراق', 'حضوری')]):
            asyncio.run(main.send_appointment_reminders_job(mock_context))

        # Check bot.send_message was called with appropriate text
        mock_context.bot.send_message.assert_called_once()
        call_kwargs = mock_context.bot.send_message.call_args.kwargs
        self.assertEqual(call_kwargs['chat_id'], 101)
        sent_text = call_kwargs['text']
        self.assertIn("دانیال اشراق", sent_text)
        self.assertIn("1405/01/01", sent_text)
        self.assertIn("18:00", sent_text)
        self.assertIn("حضوری", sent_text)
        self.assertIn("یادآوری وقت مشاوره شما", sent_text)

        # Check DB updated
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT reminder_sent FROM appointments WHERE id = ?', (app_id,))
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row[0], 1)

    def test_send_appointment_reminders_job_handles_exceptions_gracefully(self):
        """Verifies failure on one client doesn't prevent reminder delivery to another client."""
        import asyncio
        import main

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (101, '1405/01/01', '17:00', 'حضوری', 'کاربر اول', 'confirmed', 0)
        ''')
        app_id1 = cursor.lastrowid
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, reminder_sent)
            VALUES (102, '1405/01/01', '19:00', 'آنلاین', 'کاربر دوم', 'confirmed', 0)
        ''')
        app_id2 = cursor.lastrowid
        conn.commit()
        conn.close()

        mock_context = MagicMock()
        # First call fails (blocked bot), second call succeeds
        mock_context.bot.send_message = AsyncMock(side_effect=[
            Exception("Forbidden: bot was blocked by the user"),
            MagicMock()
        ])

        with patch('database.get_appointments_due_for_reminder', return_value=[
            (app_id1, 101, '1405/01/01', '17:00', 'کاربر اول', 'حضوری'),
            (app_id2, 102, '1405/01/01', '19:00', 'کاربر دوم', 'آنلاین')
        ]):
            asyncio.run(main.send_appointment_reminders_job(mock_context))

        self.assertEqual(mock_context.bot.send_message.call_count, 2)

        # User 2 must have reminder_sent = 1
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT reminder_sent FROM appointments WHERE id = ?', (app_id2,))
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()

    def test_daily_report_dual_channel(self):
        """Mocks SMTP and Telegram requests; asserts both email and Telegram messages are dispatched."""
        import daily_report

        # Ensure table has confirmed appointments for upcoming week
        today = jdatetime.date.today()
        d1 = (today + jdatetime.timedelta(days=1)).strftime("%Y/%m/%d")
        d2 = (today + jdatetime.timedelta(days=3)).strftime("%Y/%m/%d")

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status)
            VALUES (101, ?, '16:00', 'حضوری', 'سارا حسینی', 'confirmed')
        ''', (d1,))
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status)
            VALUES (102, ?, '18:00', 'آنلاین', 'مهدی صادقی', 'confirmed')
        ''', (d2,))
        conn.commit()
        conn.close()

        test_admins = [56073956, 8034655716, 95033750]

        with patch('daily_report.SENDER_EMAIL', 'clinic@gmail.com'), \
             patch('daily_report.SENDER_PASSWORD', 'secret123'), \
             patch('daily_report.RECEIVER_EMAIL', 'receiver@gmail.com'), \
             patch('daily_report.BOT_TOKEN', '123456:FAKE_TOKEN'), \
             patch('daily_report.ADMIN_IDS', test_admins), \
             patch('smtplib.SMTP') as mock_smtp_cls, \
             patch('requests.post') as mock_post:

            mock_smtp = MagicMock()
            mock_smtp_cls.return_value = mock_smtp

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = '{"ok": true}'
            mock_post.return_value = mock_resp

            daily_report.send_daily_report()

            # Channel 1: Assert SMTP was called
            mock_smtp_cls.assert_called_once()
            mock_smtp.send_message.assert_called_once()

            # Channel 2: Assert Telegram requests.post was called for each admin
            self.assertEqual(mock_post.call_count, len(test_admins))
            called_admin_ids = [call.kwargs['json']['chat_id'] for call in mock_post.call_args_list]
            for admin_id in test_admins:
                self.assertIn(admin_id, called_admin_ids)
                
            first_text = mock_post.call_args_list[0].kwargs['json']['text']
            self.assertIn("سارا حسینی", first_text)
            self.assertIn("مهدی صادقی", first_text)

    def test_daily_report_partial_failure_smtp_failure_allows_telegram(self):
        """Verifies SMTP failure does not abort Telegram administrative broadcast."""
        import daily_report

        today = jdatetime.date.today()
        d1 = (today + jdatetime.timedelta(days=2)).strftime("%Y/%m/%d")

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status)
            VALUES (101, ?, '17:00', 'حضوری', 'رویا شریفی', 'confirmed')
        ''', (d1,))
        conn.commit()
        conn.close()

        test_admins = [56073956]

        with patch('daily_report.SENDER_EMAIL', 'clinic@gmail.com'), \
             patch('daily_report.SENDER_PASSWORD', 'secret123'), \
             patch('daily_report.RECEIVER_EMAIL', 'receiver@gmail.com'), \
             patch('daily_report.BOT_TOKEN', '123456:FAKE_TOKEN'), \
             patch('daily_report.ADMIN_IDS', test_admins), \
             patch('smtplib.SMTP', side_effect=Exception("SMTP Connection refused")), \
             patch('requests.post') as mock_post:

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = '{"ok": true}'
            mock_post.return_value = mock_resp

            daily_report.send_daily_report()

            # Telegram broadcast still sent
            self.assertEqual(mock_post.call_count, 1)
            self.assertEqual(mock_post.call_args.kwargs['json']['chat_id'], 56073956)
            self.assertIn("رویا شریفی", mock_post.call_args.kwargs['json']['text'])

    def test_daily_report_partial_failure_telegram_failure_allows_smtp(self):
        """Verifies Telegram failure does not abort SMTP email sending."""
        import daily_report
        import requests

        today = jdatetime.date.today()
        d1 = (today + jdatetime.timedelta(days=2)).strftime("%Y/%m/%d")

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status)
            VALUES (101, ?, '17:00', 'حضوری', 'رویا شریفی', 'confirmed')
        ''', (d1,))
        conn.commit()
        conn.close()

        test_admins = [56073956]

        with patch('daily_report.SENDER_EMAIL', 'clinic@gmail.com'), \
             patch('daily_report.SENDER_PASSWORD', 'secret123'), \
             patch('daily_report.RECEIVER_EMAIL', 'receiver@gmail.com'), \
             patch('daily_report.BOT_TOKEN', '123456:FAKE_TOKEN'), \
             patch('daily_report.ADMIN_IDS', test_admins), \
             patch('smtplib.SMTP') as mock_smtp_cls, \
             patch('requests.post', side_effect=requests.RequestException("Network unreachable")):

            mock_smtp = MagicMock()
            mock_smtp_cls.return_value = mock_smtp

            daily_report.send_daily_report()

            # SMTP email was still sent
            mock_smtp_cls.assert_called_once()
            mock_smtp.send_message.assert_called_once()

if __name__ == '__main__':
    unittest.main()
