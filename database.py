import os
import sqlite3
import datetime
try:
    from config import TEHRAN_TZ
except ImportError:
    from zoneinfo import ZoneInfo
    TEHRAN_TZ = ZoneInfo("Asia/Tehran")

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

    # [آپدیت]: اضافه شدن ستون‌های created_at و updated_at
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
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # مایگریشن ایمن در صورت وجود قبلی جدول بدون ستون‌های زمانی
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [row[1] for row in cursor.fetchall()]
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN created_at TEXT DEFAULT (datetime('now', 'localtime'))")
    if "updated_at" not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN updated_at TEXT DEFAULT (datetime('now', 'localtime'))")

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

# [آپدیت]: دریافت نوع جلسه و نام کامل برای ثبت اولیه به همراه زمان ثبت در تایم‌زون تهران
def add_pending_appointment(user_id, date, time, session_type, full_name, receipt_file_id, created_at=None):
    conn = get_connection()
    cursor = conn.cursor()
    now_tehran_iso = created_at if created_at is not None else datetime.datetime.now(TEHRAN_TZ).isoformat()
    try:
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        ''', (user_id, date, time, session_type, full_name, receipt_file_id, now_tehran_iso, now_tehran_iso))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        return appointment_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE" in str(e).upper():
            raise SlotAlreadyBookedError(f"Slot {date} {time} is already booked.") from e
        raise
    finally:
        conn.close()

# ثبت مستقیم و قطعی نوبت (ویژه رزرو توسط ادمین‌های کلینیک بدون نیاز به فیش)
def add_confirmed_appointment(user_id, date, time, session_type, full_name, receipt_file_id="admin_direct", created_at=None):
    conn = get_connection()
    cursor = conn.cursor()
    now_tehran_iso = created_at if created_at is not None else datetime.datetime.now(TEHRAN_TZ).isoformat()
    try:
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'confirmed', ?, ?, ?)
        ''', (user_id, date, time, session_type, full_name, receipt_file_id, now_tehran_iso, now_tehran_iso))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        return appointment_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE" in str(e).upper():
            raise SlotAlreadyBookedError(f"Slot {date} {time} is already booked.") from e
        raise
    finally:
        conn.close()

def update_appointment_status(appointment_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    now_tehran_iso = datetime.datetime.now(TEHRAN_TZ).isoformat()
    cursor.execute('UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?', (status, now_tehran_iso, appointment_id))
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

def expire_stale_pending_appointments(timeout_hours=2, now=None) -> int:
    """
    Queries pending appointments created more than timeout_hours ago,
    updates their status to 'expired', and sets updated_at.
    Because status='expired', the partial unique index idx_appointments_active_slot
    automatically frees the slot.
    Returns the number of expired records.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    current_time = now if now is not None else datetime.datetime.now(TEHRAN_TZ)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=TEHRAN_TZ)
    cutoff = current_time - datetime.timedelta(hours=timeout_hours)
    
    cursor.execute("SELECT id, created_at FROM appointments WHERE status = 'pending'")
    rows = cursor.fetchall()
    
    expired_ids = []
    for app_id, created_at_str in rows:
        if not created_at_str:
            continue
        try:
            created_dt = datetime.datetime.fromisoformat(created_at_str)
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=TEHRAN_TZ)
            else:
                created_dt = created_dt.astimezone(TEHRAN_TZ)
            
            if created_dt <= cutoff:
                expired_ids.append(app_id)
        except Exception:
            pass

    if expired_ids:
        now_tehran_iso = current_time.isoformat()
        placeholders = ','.join(['?'] * len(expired_ids))
        cursor.execute(
            f"UPDATE appointments SET status = 'expired', updated_at = ? WHERE id IN ({placeholders})",
            [now_tehran_iso] + expired_ids
        )
        conn.commit()
    
    conn.close()
    return len(expired_ids)

# اطمینان از مقداردهی اولیه جداول پایگاه داده در زمان بارگذاری ماژول
setup_database()

if __name__ == "__main__":
    setup_database()