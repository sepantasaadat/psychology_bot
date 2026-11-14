import unittest
import sqlite3
import os
import database

class TestDatabaseWeeklyAppointments(unittest.TestCase):
    def setUp(self):
        # Use an isolated test database
        self.original_db = database.get_connection
        self.test_db = os.path.abspath("test_clinic.db")
        for f in [self.test_db, f"{self.test_db}-wal", f"{self.test_db}-shm"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
            
        def get_test_connection(db_path=None):
            return self.original_db(db_path or self.test_db)
            
        database.get_connection = get_test_connection
        database.setup_database()

        # Populate users for relational integrity with PRAGMA foreign_keys=ON
        conn = database.get_connection()
        cursor = conn.cursor()
        for uid, name in [
            (101, 'علی محمدی'), (102, 'سارا احمدی'), (103, 'رضا نوری'),
            (104, 'ناهید کمالی'), (105, 'مریم عباسی'), (201, 'کاربر اول'),
            (202, 'کاربر دوم'), (56073956, 'دکتر سپنتا'), (999, 'کاربر تست')
        ]:
            cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)', (uid, name))
        conn.commit()
        conn.close()
        
    def tearDown(self):
        database.get_connection = self.original_db
        for f in [self.test_db, f"{self.test_db}-wal", f"{self.test_db}-shm"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_get_upcoming_week_confirmed_appointments_empty(self):
        results = database.get_upcoming_week_confirmed_appointments("1405/01/01", "1405/01/07")
        self.assertEqual(results, [])

    def test_get_upcoming_week_confirmed_appointments_filtering(self):
        # Insert test records
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # 1. Confirmed and inside 7-day window
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (101, '1405/01/02', '18:00', 'حضوری', 'علی محمدی', 'confirmed', 'photo1')
        ''')
        # 2. Confirmed and inside window (another day)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (102, '1405/01/05', '17:00', 'آنلاین', 'سارا احمدی', 'confirmed', 'photo2')
        ''')
        # 3. Pending inside window (should be excluded)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (103, '1405/01/03', '19:00', 'حضوری', 'رضا نوری', 'pending', 'photo3')
        ''')
        # 4. Confirmed but before window (should be excluded)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (104, '1404/12/28', '17:00', 'حضوری', 'ناهید کمالی', 'confirmed', 'photo4')
        ''')
        # 5. Confirmed but after window (should be excluded)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (105, '1405/01/10', '20:00', 'آنلاین', 'مریم عباسی', 'confirmed', 'photo5')
        ''')
        conn.commit()
        conn.close()

        results = database.get_upcoming_week_confirmed_appointments("1405/01/01", "1405/01/07")
        self.assertEqual(len(results), 2)
        # Check order and fields: (id, date, time, full_name, session_type)
        self.assertEqual(results[0][1], '1405/01/02')
        self.assertEqual(results[0][2], '18:00')
        self.assertEqual(results[0][3], 'علی محمدی')
        self.assertEqual(results[0][4], 'حضوری')

        self.assertEqual(results[1][1], '1405/01/05')
        self.assertEqual(results[1][2], '17:00')
        self.assertEqual(results[1][3], 'سارا احمدی')
        self.assertEqual(results[1][4], 'آنلاین')

    def test_add_confirmed_appointment(self):
        app_id = database.add_confirmed_appointment(
            user_id=56073956,
            date='1405/01/05',
            time='19:00',
            session_type='حضوری',
            full_name='دکتر سپنتا',
            receipt_file_id='admin_direct'
        )
        self.assertIsInstance(app_id, int)

        app_info = database.get_appointment(app_id)
        # app_info: user_id, date, time, session_type, full_name, status
        self.assertEqual(app_info[0], 56073956)
        self.assertEqual(app_info[1], '1405/01/05')
        self.assertEqual(app_info[2], '19:00')
        self.assertEqual(app_info[3], 'حضوری')
        self.assertEqual(app_info[4], 'دکتر سپنتا')
        self.assertEqual(app_info[5], 'confirmed')

    def test_get_user_confirmed_appointments_for_week(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        # User 201: 2 confirmed inside week, 1 pending inside week, 1 confirmed outside week
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (201, '1405/01/02', '17:00', 'حضوری', 'کاربر اول', 'confirmed', 'r1')
        ''')
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (201, '1405/01/05', '18:00', 'آنلاین', 'کاربر اول', 'confirmed', 'r2')
        ''')
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (201, '1405/01/03', '19:00', 'حضوری', 'کاربر اول', 'pending', 'r3')
        ''')
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (201, '1405/01/15', '20:00', 'حضوری', 'کاربر اول', 'confirmed', 'r4')
        ''')
        # User 202: confirmed inside week
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (202, '1405/01/04', '18:00', 'حضوری', 'کاربر دوم', 'confirmed', 'r5')
        ''')
        conn.commit()
        conn.close()

        # Query for user 201
        res_201 = database.get_user_confirmed_appointments_for_week(201, '1405/01/01', '1405/01/07')
        self.assertEqual(len(res_201), 2)
        self.assertEqual(res_201[0][1], '1405/01/02')
        self.assertEqual(res_201[0][2], '17:00')
        self.assertEqual(res_201[1][1], '1405/01/05')
        self.assertEqual(res_201[1][2], '18:00')

        # Query for user 202
        res_202 = database.get_user_confirmed_appointments_for_week(202, '1405/01/01', '1405/01/07')
        self.assertEqual(len(res_202), 1)
        self.assertEqual(res_202[0][1], '1405/01/04')

    def test_admin_receipt_messages_crud(self):
        database.save_admin_receipt_message(10, 101, 501)
        database.save_admin_receipt_message(10, 102, 502)

        messages = database.get_admin_receipt_messages(10)
        self.assertEqual(len(messages), 2)
        self.assertIn((101, 501), messages)
        self.assertIn((102, 502), messages)

        # Test replace functionality
        database.save_admin_receipt_message(10, 101, 999)
        messages_updated = database.get_admin_receipt_messages(10)
        self.assertEqual(len(messages_updated), 2)
        self.assertIn((101, 999), messages_updated)

        # Test delete
        database.delete_admin_receipt_messages(10)
        self.assertEqual(database.get_admin_receipt_messages(10), [])

    def test_sqlite_pragmas(self):
        conn = database.get_connection()
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        busy_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        conn.close()

        self.assertEqual(journal_mode.lower(), "wal")
        self.assertEqual(busy_timeout, 30000)
        self.assertEqual(foreign_keys, 1)

    def test_double_booking_prevention(self):
        # 1. Book an initial pending appointment
        app_id_1 = database.add_pending_appointment(
            user_id=101,
            date="1405/02/01",
            time="10:00",
            session_type="حضوری",
            full_name="کاربر الف",
            receipt_file_id="receipt_1.jpg"
        )
        self.assertIsNotNone(app_id_1)

        # 2. Attempting to book the same slot again with pending should raise SlotAlreadyBookedError
        with self.assertRaises(database.SlotAlreadyBookedError) as ctx1:
            database.add_pending_appointment(
                user_id=102,
                date="1405/02/01",
                time="10:00",
                session_type="آنلاین",
                full_name="کاربر ب",
                receipt_file_id="receipt_2.jpg"
            )
        self.assertIn("1405/02/01", str(ctx1.exception))
        self.assertIn("10:00", str(ctx1.exception))

        # 3. Attempting to book the same slot with confirmed appointment should also raise SlotAlreadyBookedError
        with self.assertRaises(database.SlotAlreadyBookedError) as ctx2:
            database.add_confirmed_appointment(
                user_id=56073956,
                date="1405/02/01",
                time="10:00",
                session_type="حضوری",
                full_name="دکتر سپنتا"
            )
        self.assertIn("1405/02/01", str(ctx2.exception))
        self.assertIn("10:00", str(ctx2.exception))

    def test_booking_after_rejection_or_cancellation_allowed(self):
        # 1. Book an initial pending appointment
        app_id_1 = database.add_pending_appointment(
            user_id=101,
            date="1405/02/05",
            time="11:00",
            session_type="حضوری",
            full_name="کاربر تست",
            receipt_file_id="receipt_test.jpg"
        )
        self.assertIsNotNone(app_id_1)

        # 2. Reject the appointment
        database.update_appointment_status(app_id_1, "rejected")

        # 3. Slot should now be available to be booked again
        app_id_2 = database.add_pending_appointment(
            user_id=102,
            date="1405/02/05",
            time="11:00",
            session_type="آنلاین",
            full_name="کاربر دوم",
            receipt_file_id="receipt_test2.jpg"
        )
        self.assertIsNotNone(app_id_2)

        # 4. Cancel the second appointment
        database.update_appointment_status(app_id_2, "cancelled")

        # 5. Slot should be available again for confirmed booking
        app_id_3 = database.add_confirmed_appointment(
            user_id=56073956,
            date="1405/02/05",
            time="11:00",
            session_type="حضوری",
            full_name="دکتر سپنتا"
        )
        self.assertIsNotNone(app_id_3)

if __name__ == '__main__':
    unittest.main()
