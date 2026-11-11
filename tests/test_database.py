import unittest
import sqlite3
import os
import database

class TestDatabaseWeeklyAppointments(unittest.TestCase):
    def setUp(self):
        # Use an isolated test database
        self.original_db = database.get_connection
        self.test_db = "test_clinic.db"
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

if __name__ == '__main__':
    unittest.main()
