import io
import os
import sys
import gc
import shutil
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
from PIL import Image

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config
import database
import app as flask_app


def _create_test_image(size=(40, 40), color="blue") -> bytes:
    bio = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(bio, format="PNG")
    return bio.getvalue()


class TestConcurrencyDoubleBooking(unittest.TestCase):
    """
    Unit test suite asserting race condition prevention and single-booking guarantees
    under heavy multi-threaded concurrent attempts at database and web layer.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_concurrency_")
        self.test_db_path = os.path.join(self.test_dir, "clinic_concurrency.db")
        self.original_get_connection = database.get_connection
        self.original_db_path = database.DB_PATH

        database.DB_PATH = self.test_db_path

        def get_test_connection(db_path=None):
            target = db_path if db_path is not None else self.test_db_path
            return self.original_get_connection(target)

        database.get_connection = get_test_connection
        database.setup_database(self.test_db_path)

        # Setup web user (id=0) and test users (id=1..20)
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
                    (0, "Web User", "web_user"))
        for i in range(1, 25):
            cur.execute("INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
                        (i, f"User {i}", f"user_{i}"))
        conn.commit()
        conn.close()

        # Configure Flask app
        flask_app.app.config['TESTING'] = True
        flask_app.app.config['WTF_CSRF_ENABLED'] = False
        flask_app.DATABASE = self.test_db_path

    def tearDown(self):
        database.get_connection = self.original_get_connection
        database.DB_PATH = self.original_db_path
        gc.collect()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_threads_pending_slot_booking(self):
        """
        Simultaneously launch 10 threads attempting to book the exact same (date, time) slot.
        Assert that:
          1. Exactly 1 thread succeeds and returns a valid appointment ID.
          2. Exactly 9 threads raise database.SlotAlreadyBookedError.
          3. Exactly 1 record exists in the appointments table for that slot.
        """
        slot_date = "1405/01/10"
        slot_time = "18:00"
        num_workers = 10
        barrier = threading.Barrier(num_workers)

        def book_attempt(worker_idx):
            barrier.wait()
            return database.add_pending_appointment(
                user_id=worker_idx,
                date=slot_date,
                time=slot_time,
                session_type="حضوری",
                full_name=f"مراجع آزمایشی {worker_idx}",
                receipt_file_id=f"receipt_token_{worker_idx}"
            )

        successes = []
        slot_errors = []
        other_errors = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(book_attempt, i) for i in range(1, num_workers + 1)]
            for fut in as_completed(futures):
                try:
                    appt_id = fut.result()
                    successes.append(appt_id)
                except database.SlotAlreadyBookedError as e:
                    slot_errors.append(e)
                except Exception as ex:
                    other_errors.append(ex)

        # Assert no unexpected crashes/foreign key errors
        self.assertEqual(len(other_errors), 0, f"Unexpected exceptions occurred: {other_errors}")

        # Assert exactly 1 success and (N - 1) SlotAlreadyBookedError
        self.assertEqual(len(successes), 1, f"Expected 1 success, got {len(successes)}: {successes}")
        self.assertIsInstance(successes[0], int)
        self.assertGreater(successes[0], 0)
        self.assertEqual(len(slot_errors), num_workers - 1)

        # Assert database state has exactly 1 row for this slot
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, date, time, status FROM appointments WHERE date = ? AND time = ?",
                    (slot_date, slot_time))
        rows = cur.fetchall()
        conn.close()

        self.assertEqual(len(rows), 1, "Exactly one appointment must exist in the database for the contested slot")
        self.assertEqual(rows[0][0], successes[0])
        self.assertIn(rows[0][4], ("pending", "confirmed"))

    def test_concurrent_threads_confirmed_slot_booking(self):
        """
        Simultaneously launch 8 admin direct bookings on the exact same (date, time) slot.
        Assert that exactly 1 succeeds with confirmed status, and 7 fail with SlotAlreadyBookedError.
        """
        slot_date = "1405/01/11"
        slot_time = "16:00"
        num_workers = 8
        barrier = threading.Barrier(num_workers)

        def confirmed_attempt(worker_idx):
            barrier.wait()
            return database.add_confirmed_appointment(
                user_id=worker_idx,
                date=slot_date,
                time=slot_time,
                session_type="آنلاین",
                full_name=f"ادمین نوبت {worker_idx}",
                receipt_file_id="admin_direct"
            )

        successes = []
        slot_errors = []
        other_errors = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(confirmed_attempt, i) for i in range(1, num_workers + 1)]
            for fut in as_completed(futures):
                try:
                    appt_id = fut.result()
                    successes.append(appt_id)
                except database.SlotAlreadyBookedError as e:
                    slot_errors.append(e)
                except Exception as ex:
                    other_errors.append(ex)

        self.assertEqual(len(other_errors), 0, f"Unexpected exceptions: {other_errors}")
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(slot_errors), num_workers - 1)

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, status FROM appointments WHERE date = ? AND time = ?", (slot_date, slot_time))
        rows = cur.fetchall()
        conn.close()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "confirmed")

    def test_concurrent_web_booking_endpoint(self):
        """
        Simulate 6 concurrent POST requests to /booking on the exact same date and time.
        Assert that exactly 1 request successfully creates a booking (HTTP 302 redirect),
        while all other competing requests fail gracefully (HTTP 409 Conflict or 400),
        and exactly 1 appointment row exists in database.
        """
        upcoming_days = config.get_upcoming_working_days(5, is_admin=False)
        target_date = upcoming_days[2]
        target_time = "17:00"
        num_workers = 6
        barrier = threading.Barrier(num_workers)
        img_bytes = _create_test_image()

        def web_post_attempt(worker_idx):
            client = flask_app.app.test_client()
            form_data = {
                'date': target_date,
                'time': target_time,
                'full_name': f'مراجع همزمان {worker_idx}',
                'phone': f'091234567{worker_idx:02d}',
                'session_type': 'حضوری',
                'receipt': (io.BytesIO(img_bytes), f'receipt_{worker_idx}.png')
            }
            barrier.wait()
            response = client.post(
                '/booking',
                data=form_data,
                content_type='multipart/form-data',
                follow_redirects=False
            )
            return response.status_code

        with patch('app.send_receipt_to_telegram'):
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(web_post_attempt, i) for i in range(1, num_workers + 1)]
                status_codes = [fut.result() for fut in as_completed(futures)]

        # Exactly 1 request should receive HTTP 302 redirect (success)
        success_count = sum(1 for code in status_codes if code == 302)
        conflict_count = sum(1 for code in status_codes if code in (400, 409))

        self.assertEqual(
            success_count, 1,
            f"Expected exactly 1 HTTP 302, got status codes: {status_codes}"
        )
        self.assertEqual(
            conflict_count, num_workers - 1,
            f"Expected {num_workers - 1} 400/409 error responses, got: {status_codes}"
        )

        # Verify database has exactly 1 appointment for that slot
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM appointments WHERE date = ? AND time = ?", (target_date, target_time))
        count = cur.fetchone()[0]
        conn.close()

        self.assertEqual(count, 1, "Database must contain exactly 1 appointment for the contested slot")


# ==============================================================================
# Standalone pytest functions using conftest fixtures (isolated_db, flask_client)
# ==============================================================================

def test_pytest_fixture_concurrency_database(isolated_db):
    """
    Pytest verification of concurrency double-booking prevention using isolated_db fixture.
    """
    slot_date = "1405/01/15"
    slot_time = "19:00"
    num_workers = 8
    barrier = threading.Barrier(num_workers)

    # Insert test users
    conn = database.get_connection()
    cur = conn.cursor()
    for i in range(1, num_workers + 1):
        cur.execute("INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
                    (i + 100, f"PytestUser {i}", f"pytest_user_{i}"))
    conn.commit()
    conn.close()

    def attempt(idx):
        barrier.wait()
        return database.add_pending_appointment(
            user_id=idx + 100,
            date=slot_date,
            time=slot_time,
            session_type="آنلاین",
            full_name=f"Pytest Client {idx}",
            receipt_file_id=f"receipt_{idx}"
        )

    successes = []
    slot_errors = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(attempt, i) for i in range(1, num_workers + 1)]
        for fut in as_completed(futures):
            try:
                appt_id = fut.result()
                successes.append(appt_id)
            except database.SlotAlreadyBookedError as e:
                slot_errors.append(e)

    assert len(successes) == 1
    assert len(slot_errors) == num_workers - 1

    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM appointments WHERE date = ? AND time = ?", (slot_date, slot_time))
    total_in_db = cur.fetchone()[0]
    conn.close()

    assert total_in_db == 1


def test_pytest_fixture_concurrency_web(flask_client, isolated_db, monkeypatch):
    """
    Pytest verification of concurrent POST requests to /booking using flask_client fixture.
    """
    upcoming_days = config.get_upcoming_working_days(5, is_admin=False)
    target_date = upcoming_days[3]
    target_time = "18:00"
    num_workers = 6
    barrier = threading.Barrier(num_workers)
    img_bytes = _create_test_image()

    monkeypatch.setattr("app.send_receipt_to_telegram", MagicMock())

    def post_worker(idx):
        from app import app
        thread_client = app.test_client()
        barrier.wait()
        res = thread_client.post(
            '/booking',
            data={
                'date': target_date,
                'time': target_time,
                'full_name': f'مراجع وب {idx}',
                'phone': f'091211122{idx:02d}',
                'session_type': 'آنلاین',
                'receipt': (io.BytesIO(img_bytes), f'receipt_{idx}.png')
            },
            content_type='multipart/form-data',
            follow_redirects=False
        )
        return res.status_code

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(post_worker, i) for i in range(1, num_workers + 1)]
        codes = [fut.result() for fut in as_completed(futures)]

    success_count = sum(1 for c in codes if c == 302)
    failure_count = sum(1 for c in codes if c in (400, 409))

    assert success_count == 1
    assert failure_count == num_workers - 1

    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM appointments WHERE date = ? AND time = ?", (target_date, target_time))
    count = cur.fetchone()[0]
    conn.close()

    assert count == 1


if __name__ == '__main__':
    unittest.main()
