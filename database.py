import os
import sqlite3

class SlotAlreadyBookedError(Exception):
    """Raised when attempting to book an active slot that is already booked."""
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "clinic.db")

def get_connection(db_path=None):
    target_path = db_path if db_path is not None else DB_PATH
    conn = sqlite3.connect(target_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def setup_database(db_path=None):
    conn = get_connection(db_path) if db_path else get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT
        )
    ''')

    # [آپدیت]: اضافه شدن دو ستون session_type (نوع جلسه) و full_name (نام کامل)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,          
            time TEXT,          
            session_type TEXT,  -- آنلاین یا حضوری
            full_name TEXT,     -- نام و نام خانوادگی دریافت شده از کاربر
            status TEXT,        
            receipt_file_id TEXT, 
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # ایندکس یکتا برای جلوگیری از ثبت تکراری نوبت در وضعیت‌های فعال (pending, approved, confirmed)
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_appointments_active_slot
        ON appointments(date, time)
        WHERE status IN ('pending', 'approved', 'confirmed')
    ''')

    # جدول نگهداری شناسه پیام‌های فیش واریزی ارسال شده به ادمین‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_receipt_messages (
            appointment_id INTEGER,
            admin_id INTEGER,
            message_id INTEGER,
            PRIMARY KEY (appointment_id, admin_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database updated successfully with new columns!")

def add_user(user_id, first_name, username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, first_name, username) 
        VALUES (?, ?, ?)
    ''', (user_id, first_name, username))
    conn.commit()
    conn.close()

# [آپدیت]: دریافت نوع جلسه و نام کامل برای ثبت اولیه
def add_pending_appointment(user_id, date, time, session_type, full_name, receipt_file_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
        ''', (user_id, date, time, session_type, full_name, receipt_file_id))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        return appointment_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise SlotAlreadyBookedError(f"Slot {date} {time} is already booked.") from e
    finally:
        conn.close()

# ثبت مستقیم و قطعی نوبت (ویژه رزرو توسط ادمین‌های کلینیک بدون نیاز به فیش)
def add_confirmed_appointment(user_id, date, time, session_type, full_name, receipt_file_id="admin_direct"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (?, ?, ?, ?, ?, 'confirmed', ?)
        ''', (user_id, date, time, session_type, full_name, receipt_file_id))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        return appointment_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise SlotAlreadyBookedError(f"Slot {date} {time} is already booked.") from e
    finally:
        conn.close()

def update_appointment_status(appointment_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE appointments SET status = ? WHERE id = ?', (status, appointment_id))
    conn.commit()
    conn.close()

# [آپدیت]: برگرداندن نام کامل و نوع جلسه برای پیام‌های ادمین
def get_appointment(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, date, time, session_type, full_name, status FROM appointments WHERE id = ?', (appointment_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_booked_times(date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = ? AND status IN ('pending', 'confirmed')", (date,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# [آپدیت ۹]: دریافت لیست تمام نوبت‌های تایید شده برای پنل مدیریت ادمین اصلی
def get_all_confirmed_appointments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, date, time, full_name, session_type 
        FROM appointments 
        WHERE status = 'confirmed' 
        ORDER BY date, time
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

# دریافت نوبت‌های تایید شده برای بازه زمانی مشخص (مانند ۷ روز آینده)
def get_upcoming_week_confirmed_appointments(start_date_str, end_date_str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, date, time, full_name, session_type 
        FROM appointments 
        WHERE status = 'confirmed' 
          AND date >= ? 
          AND date <= ?
        ORDER BY date, time
    ''', (start_date_str, end_date_str))
    rows = cursor.fetchall()
    conn.close()
    return rows

# دریافت نوبت‌های تایید شده یک کاربر خاص در بازه زمانی مشخص (جهت لغو نوبت توسط مراجع)
def get_user_confirmed_appointments_for_week(user_id, start_date_str, end_date_str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, date, time, full_name, session_type 
        FROM appointments 
        WHERE user_id = ? 
          AND status = 'confirmed' 
          AND date >= ? 
          AND date <= ?
        ORDER BY date, time
    ''', (user_id, start_date_str, end_date_str))
    rows = cursor.fetchall()
    conn.close()
    return rows

# [آپدیت ۹]: تابع حذف کامل یک نوبت برای آزاد شدن ساعت آن
def delete_appointment(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM appointments WHERE id = ?', (int(appointment_id),))
    cursor.execute('DELETE FROM admin_receipt_messages WHERE appointment_id = ?', (int(appointment_id),))
    conn.commit()
    conn.close()

def save_admin_receipt_message(appointment_id, admin_id, message_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO admin_receipt_messages (appointment_id, admin_id, message_id)
        VALUES (?, ?, ?)
    ''', (int(appointment_id), int(admin_id), int(message_id)))
    conn.commit()
    conn.close()

def get_admin_receipt_messages(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT admin_id, message_id
        FROM admin_receipt_messages
        WHERE appointment_id = ?
    ''', (int(appointment_id),))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_admin_receipt_messages(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admin_receipt_messages WHERE appointment_id = ?', (int(appointment_id),))
    conn.commit()
    conn.close()

# اطمینان از مقداردهی اولیه جداول پایگاه داده در زمان بارگذاری ماژول
setup_database()

if __name__ == "__main__":
    setup_database()