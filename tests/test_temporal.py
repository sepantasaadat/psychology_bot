import unittest
import os
import sqlite3
import datetime
from zoneinfo import ZoneInfo
import jdatetime

import config
import database
from database import SlotAlreadyBookedError

class TestTemporalJalaliCalendar(unittest.TestCase):
    def test_tehran_tz_defined(self):
        self.assertEqual(config.TEHRAN_TZ.key, "Asia/Tehran")

    def test_working_constants_defined(self):
        self.assertEqual(config.WORKING_WEEKDAYS, [0, 1, 2, 3, 4])
        self.assertEqual(config.WORKING_HOURS, ["16:00", "17:00", "18:00", "19:00", "20:00", "21:00"])

    def test_rolling_window_nowruz_boundary_admin(self):
        # 1405/12/28 is Friday (weekday 6)
        # 1405/12/29 is Saturday (weekday 0)
        # 1406/01/01 is Sunday (weekday 1)
        # 1406/01/02 is Monday (weekday 2)
        # 1406/01/03 is Tuesday (weekday 3)
        # 1406/01/04 is Wednesday (weekday 4)
        days = config.get_upcoming_working_days(days_count=5, is_admin=True, reference_date="1405/12/28")
        expected = [
            "1405/12/29",
            "1406/01/01",
            "1406/01/02",
            "1406/01/03",
            "1406/01/04"
        ]
        self.assertEqual(days, expected)

    def test_rolling_window_nowruz_boundary_regular_user(self):
        # 1405/12/28 is Friday (weekday 6)
        # Regular user skips today (1405/12/28) and tomorrow (1405/12/29)
        # Starting point is 1406/01/01 (Sunday, weekday 1)
        # 1406/01/05 (Thursday) and 1406/01/06 (Friday) are skipped
        # 5th working day is 1406/01/07 (Saturday, weekday 0)
        days = config.get_upcoming_working_days(days_count=5, is_admin=False, reference_date="1405/12/28")
        expected = [
            "1406/01/01",
            "1406/01/02",
            "1406/01/03",
            "1406/01/04",
            "1406/01/07"
        ]
        self.assertEqual(days, expected)

    def test_arbitrary_future_year_without_hardcoding(self):
        # Test year 1410 (far future) to guarantee no hardcoded year limits
        days = config.get_upcoming_working_days(days_count=3, is_admin=True, reference_date="1410/05/01")
        self.assertEqual(len(days), 3)
        self.assertTrue(all(d.startswith("1410/") for d in days))

    def test_default_reference_date_anchored_to_tehran(self):
        days = config.get_upcoming_working_days(days_count=5)
        self.assertEqual(len(days), 5)
        # Each item should be in YYYY/MM/DD format
        for d in days:
            parts = d.split('/')
            self.assertEqual(len(parts), 3)
            self.assertEqual(len(parts[0]), 4)
            self.assertEqual(len(parts[1]), 2)
            self.assertEqual(len(parts[2]), 2)

    def test_admin_vs_regular_user_advance_notice(self):
        # Saturday 1405/08/23
        ref = "1405/08/23"
        admin_days = config.get_upcoming_working_days(days_count=5, is_admin=True, reference_date=ref)
        user_days = config.get_upcoming_working_days(days_count=5, is_admin=False, reference_date=ref)

        # Admin gets today (1405/08/23) and tomorrow (1405/08/24)
        self.assertEqual(admin_days[0], "1405/08/23")
        self.assertEqual(admin_days[1], "1405/08/24")

        # Regular user skips today and tomorrow
        self.assertNotIn("1405/08/23", user_days)
        self.assertNotIn("1405/08/24", user_days)
        self.assertEqual(user_days[0], "1405/08/25")


class TestStaleAppointmentExpiration(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_temporal_stale.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
        self.original_db = database.get_connection
        def get_test_connection(path=None):
            conn = sqlite3.connect(self.test_db)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            return conn
            
        database.get_connection = get_test_connection
        database.setup_database(self.test_db)
        database.add_user(101, "User1", "user1")
        database.add_user(102, "User2", "user2")
        database.add_user(103, "User3", "user3")

    def tearDown(self):
        database.get_connection = self.original_db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_created_and_updated_at_columns_exist(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(appointments)")
        cols = {row[1]: row for row in cursor.fetchall()}
        conn.close()
        self.assertIn("created_at", cols)
        self.assertIn("updated_at", cols)

    def test_expire_stale_pending_appointments(self):
        now_tehran = datetime.datetime.now(config.TEHRAN_TZ)
        stale_time = (now_tehran - datetime.timedelta(hours=3)).isoformat()
        recent_time = (now_tehran - datetime.timedelta(minutes=30)).isoformat()

        # Insert stale pending appointment (3 hours old)
        app1_id = database.add_pending_appointment(
            user_id=101,
            date="1405/09/01",
            time="16:00",
            session_type="حضوری",
            full_name="کاربر قدیمی",
            receipt_file_id="receipt_old.jpg",
            created_at=stale_time
        )

        # Insert fresh pending appointment (30 mins old)
        app2_id = database.add_pending_appointment(
            user_id=102,
            date="1405/09/01",
            time="17:00",
            session_type="آنلاین",
            full_name="کاربر جدید",
            receipt_file_id="receipt_new.jpg",
            created_at=recent_time
        )

        # Insert old confirmed appointment (3 hours old, should NOT expire)
        app3_id = database.add_confirmed_appointment(
            user_id=103,
            date="1405/09/01",
            time="18:00",
            session_type="حضوری",
            full_name="کاربر تایید شده",
            created_at=stale_time
        )

        # Run expiration with 2 hours timeout
        expired_count = database.expire_stale_pending_appointments(timeout_hours=2)
        self.assertEqual(expired_count, 1)

        app1 = database.get_appointment(app1_id)
        self.assertEqual(app1[5], "expired")

        app2 = database.get_appointment(app2_id)
        self.assertEqual(app2[5], "pending")

        app3 = database.get_appointment(app3_id)
        self.assertEqual(app3[5], "confirmed")

    def test_expired_slot_can_be_rebooked(self):
        now_tehran = datetime.datetime.now(config.TEHRAN_TZ)
        stale_time = (now_tehran - datetime.timedelta(hours=4)).isoformat()

        # Slot 1405/09/01 16:00 booked initially
        app1_id = database.add_pending_appointment(
            user_id=101,
            date="1405/09/01",
            time="16:00",
            session_type="حضوری",
            full_name="کاربر اول",
            receipt_file_id="receipt_1.jpg",
            created_at=stale_time
        )

        # Before expiration, booking the same slot fails
        with self.assertRaises(SlotAlreadyBookedError):
            database.add_pending_appointment(
                user_id=102,
                date="1405/09/01",
                time="16:00",
                session_type="آنلاین",
                full_name="کاربر دوم",
                receipt_file_id="receipt_2.jpg"
            )

        # Expire stale bookings
        expired_count = database.expire_stale_pending_appointments(timeout_hours=2)
        self.assertEqual(expired_count, 1)

        # After expiration, booking the same slot must SUCCEED
        new_app_id = database.add_pending_appointment(
            user_id=102,
            date="1405/09/01",
            time="16:00",
            session_type="آنلاین",
            full_name="کاربر دوم",
            receipt_file_id="receipt_2.jpg"
        )
        self.assertIsNotNone(new_app_id)
        new_app = database.get_appointment(new_app_id)
        self.assertEqual(new_app[5], "pending")

    def test_is_appointment_past_scenarios(self):
        ref_now = jdatetime.datetime(1405, 5, 10, 17, 30)

        # 1. Past date -> True
        self.assertTrue(config.is_appointment_past("1405/05/09", "18:00", now=ref_now))

        # 2. Same day, earlier hour -> True
        self.assertTrue(config.is_appointment_past("1405/05/10", "16:00", now=ref_now))

        # 3. Same day, exact minute -> True (arrived)
        self.assertTrue(config.is_appointment_past("1405/05/10", "17:30", now=ref_now))

        # 4. Same day, later hour -> False
        self.assertFalse(config.is_appointment_past("1405/05/10", "18:00", now=ref_now))

        # 5. Future date -> False
        self.assertFalse(config.is_appointment_past("1405/05/11", "16:00", now=ref_now))

        # 6. Persian/Arabic numerals normalized safely -> True
        self.assertTrue(config.is_appointment_past("۱۴۰۵/۰۵/۰۹", "۱۸:۰۰", now=ref_now))
        self.assertFalse(config.is_appointment_past("۱۴۰۵/۰۵/۱۱", "۱۶:۰۰", now=ref_now))

        # 7. Malformed inputs return False safely without raising exceptions
        self.assertFalse(config.is_appointment_past("invalid-date", "18:00", now=ref_now))
        self.assertFalse(config.is_appointment_past("1405/05/10", "bad-time", now=ref_now))
        self.assertFalse(config.is_appointment_past(None, None, now=ref_now))

    def test_main_tehran_timezone_anchoring(self):
        """Verifies now_tehran_jalali and today_tehran_jalali in main.py are strictly bound to Asia/Tehran."""
        import main
        from unittest.mock import patch

        # Simulate UTC time 2026-11-20 21:00:00 (which is 2026-11-21 00:30:00 in Asia/Tehran -> 1405-09-01 in Jalali)
        utc_dt = datetime.datetime(2026, 11, 20, 21, 0, 0, tzinfo=datetime.timezone.utc)
        tehran_dt = utc_dt.astimezone(config.TEHRAN_TZ)

        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.side_effect = lambda tz=None: tehran_dt if tz == config.TEHRAN_TZ else utc_dt

            j_now = main.now_tehran_jalali()
            j_today = main.today_tehran_jalali()

            self.assertEqual(j_today.year, 1405)
            self.assertEqual(j_today.month, 8)
            self.assertEqual(j_today.day, 30)  # In Tehran it is Aban 30; in UTC it is still Aban 29
            self.assertEqual(j_now.hour, 0)
            self.assertEqual(j_now.minute, 30)


if __name__ == "__main__":
    unittest.main()
