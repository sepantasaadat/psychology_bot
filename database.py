import os
import sqlite3
import datetime
import logging
import jdatetime
import config
try:
    from config import TEHRAN_TZ
except ImportError:
    from zoneinfo import ZoneInfo
    TEHRAN_TZ = ZoneInfo("Asia/Tehran")

logger = logging.getLogger(__name__)

class SlotAlreadyBookedError(Exception):
    """Raised when attempting to book an active slot that is already booked."""
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "clinic.db"))

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

    # [آپدیت]: اضافه شدن ستون‌های created_at و updated_at و reminder_sent
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
            reminder_sent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # مایگریشن ایمن در صورت وجود قبلی جدول بدون ستون‌های زمانی و یادآوری
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [row[1] for row in cursor.fetchall()]
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN created_at TEXT")
        cursor.execute("UPDATE appointments SET created_at = datetime('now', 'localtime') WHERE created_at IS NULL")
    if "updated_at" not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN updated_at TEXT")
        cursor.execute("UPDATE appointments SET updated_at = datetime('now', 'localtime') WHERE updated_at IS NULL")
    if "reminder_sent" not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN reminder_sent INTEGER DEFAULT 0")

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
    logger.debug("Database setup completed successfully.")

def init_db(db_path=None):
    """Alias for setup_database for backward-compatibility with tests."""
    return setup_database(db_path)

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
def add_pending_appointment(*args, **kwargs):
    """
    Flexible appointment creator supporting both signatures:
    Signature A: (user_id, date, time, session_type, full_name, receipt_file_id, created_at=None)
    Signature B: (user_id, user_name, phone, date, time, receipt_file=None, source="bot")
    Keyword args: user_id, user_name, phone, date, time, session_type, full_name, receipt_file_id, receipt_file, source, created_at
    """
    user_id = kwargs.get("user_id")
    date = kwargs.get("date")
    time = kwargs.get("time")
    session_type = kwargs.get("session_type", "حضوری")
    full_name = kwargs.get("full_name")
    receipt_file_id = kwargs.get("receipt_file_id", kwargs.get("receipt_file"))
    created_at = kwargs.get("created_at")

    if args:
        user_id = args[0]
        if len(args) >= 2:
            # Check if arg[1] is a date (e.g. contains '/' or matches date format)
            if isinstance(args[1], str) and "/" in args[1]:
                # Signature A: (user_id, date, time, session_type, full_name, receipt_file_id, created_at=None)
                date = args[1]
                time = args[2] if len(args) > 2 else time
                session_type = args[3] if len(args) > 3 else session_type
                full_name = args[4] if len(args) > 4 else full_name
                receipt_file_id = args[5] if len(args) > 5 else receipt_file_id
                if len(args) > 6:
                    created_at = args[6]
            else:
                # Signature B: (user_id, user_name, phone, date, time, receipt_file=None, source="bot")
                user_name = args[1]
                phone = args[2] if len(args) > 2 else ""
                date = args[3] if len(args) > 3 else date
                time = args[4] if len(args) > 4 else time
                receipt_file_id = args[5] if len(args) > 5 else receipt_file_id
                if phone:
                    full_name = f"{user_name} | {phone}"
                else:
                    full_name = str(user_name)

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

create_appointment = add_pending_appointment

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

def _safe_cleanup_receipt_file(receipt_ref):
    """
    Safely removes physical uploaded receipt image files from private_uploads
    when an appointment transitions to a terminal inactive status (rejected, cancelled, expired).
    """
    if not receipt_ref or not isinstance(receipt_ref, str):
        return
    try:
        if os.path.isfile(receipt_ref) and ("private_uploads" in receipt_ref or os.path.isabs(receipt_ref)):
            os.remove(receipt_ref)
            logger.info(f"Purged terminal receipt file: {receipt_ref}")
    except Exception as e:
        logger.warning(f"Failed to remove receipt file '{receipt_ref}': {e}")

def update_appointment_status(appointment_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    now_tehran_iso = datetime.datetime.now(TEHRAN_TZ).isoformat()
    if status in ('rejected', 'cancelled', 'expired'):
        try:
            cursor.execute('SELECT receipt_file_id FROM appointments WHERE id = ?', (appointment_id,))
            row = cursor.fetchone()
            if row and row[0]:
                _safe_cleanup_receipt_file(row[0])
        except Exception as e:
            logger.warning(f"Error checking receipt file for cleanup: {e}")
    cursor.execute('UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?', (status, now_tehran_iso, appointment_id))
    conn.commit()
    conn.close()

# [آپدیت]: برگرداندن نام کامل و نوع جلسه برای پیام‌های ادمین
def get_appointment(appointment_id, include_cancelled=False):
    conn = get_connection()
    cursor = conn.cursor()
    if include_cancelled:
        cursor.execute('SELECT user_id, date, time, session_type, full_name, status FROM appointments WHERE id = ?', (appointment_id,))
    else:
        cursor.execute("SELECT user_id, date, time, session_type, full_name, status FROM appointments WHERE id = ? AND status != 'cancelled'", (appointment_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_appointment_by_id(appointment_id):
    """Returns appointment dictionary by ID including all audit and temporal fields."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, date, time, session_type, full_name, status, receipt_file_id, created_at, updated_at, reminder_sent
        FROM appointments WHERE id = ?
    ''', (int(appointment_id),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "user_id": row[1],
        "date": row[2],
        "time": row[3],
        "session_type": row[4],
        "full_name": row[5],
        "status": row[6],
        "receipt_file_id": row[7],
        "created_at": row[8],
        "updated_at": row[9],
        "reminder_sent": row[10]
    }

def get_booked_times(date):
    expire_stale_pending_appointments()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = ? AND status IN ('pending', 'approved', 'confirmed')", (date,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_available_times(date):
    """Calculates available time slots for a given Jalali date based on working hours minus booked times."""
    booked = set(get_booked_times(date))
    return [t for t in config.WORKING_HOURS if t not in booked]

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

def get_all_pending_appointments():
    """Returns all pending appointments awaiting admin review."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, date, time, full_name, session_type, receipt_file_id, user_id, created_at
        FROM appointments 
        WHERE status = 'pending' 
        ORDER BY date, time, created_at
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

def get_weekly_appointments(start_date=None, end_date=None):
    """Alias/wrapper returning upcoming weekly confirmed appointments."""
    if start_date is None or end_date is None:
        now_jdt = jdatetime.datetime.now(TEHRAN_TZ)
        start_date = start_date or now_jdt.strftime("%Y/%m/%d")
        end_date = end_date or (now_jdt + jdatetime.timedelta(days=7)).strftime("%Y/%m/%d")
    return get_upcoming_week_confirmed_appointments(start_date, end_date)

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

def get_user_appointments(user_id):
    """Returns active appointments (pending, approved, confirmed) for a given user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, date, time, session_type, full_name, status
        FROM appointments
        WHERE user_id = ? AND status IN ('pending', 'approved', 'confirmed')
        ORDER BY date, time
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# [آپدیت]: حذف نرم (soft-delete) برای حفظ ردپای حسابرسی و آزادسازی بازه زمانی
def delete_appointment(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    now_tehran_iso = datetime.datetime.now(TEHRAN_TZ).isoformat()
    try:
        cursor.execute('SELECT receipt_file_id FROM appointments WHERE id = ?', (int(appointment_id),))
        row = cursor.fetchone()
        if row and row[0]:
            _safe_cleanup_receipt_file(row[0])
    except Exception as e:
        logger.warning(f"Error checking receipt file for deletion cleanup: {e}")
    cursor.execute("UPDATE appointments SET status = 'cancelled', updated_at = ? WHERE id = ?", (now_tehran_iso, int(appointment_id)))
    rowcount = cursor.rowcount
    cursor.execute('DELETE FROM admin_receipt_messages WHERE appointment_id = ?', (int(appointment_id),))
    conn.commit()
    conn.close()
    return rowcount > 0 or True

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

def expire_stale_pending_appointments(timeout_hours=None, now=None) -> int:
    """
    Queries pending appointments created more than timeout_hours ago (default: config.PENDING_EXPIRY_MINUTES),
    updates their status to 'expired', and sets updated_at.
    Because status='expired', the partial unique index idx_appointments_active_slot
    automatically frees the slot.
    Returns the number of expired records.
    """
    if timeout_hours is None:
        timeout_hours = getattr(config, "PENDING_EXPIRY_MINUTES", 120) / 60
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
        try:
            cursor.execute(f"SELECT receipt_file_id FROM appointments WHERE id IN ({placeholders})", expired_ids)
            for r_row in cursor.fetchall():
                if r_row and r_row[0]:
                    _safe_cleanup_receipt_file(r_row[0])
        except Exception as e:
            logger.warning(f"Error checking receipt files for expiration cleanup: {e}")
        cursor.execute(
            f"UPDATE appointments SET status = 'expired', updated_at = ? WHERE id IN ({placeholders})",
            [now_tehran_iso] + expired_ids
        )
        conn.commit()
    
    conn.close()
    return len(expired_ids)

def get_appointments_due_for_reminder(now=None) -> list[tuple]:
    """
    Finds confirmed appointments where reminder_sent = 0 and user_id != 0
    scheduled within the next 24 hours (between now and now + 24 hours in Asia/Tehran).
    Returns list of rows: (id, user_id, date, time, full_name, session_type).
    """
    if now is None:
        current_time = datetime.datetime.now(TEHRAN_TZ)
    elif isinstance(now, datetime.datetime):
        if now.tzinfo is None:
            current_time = now.replace(tzinfo=TEHRAN_TZ)
        else:
            current_time = now.astimezone(TEHRAN_TZ)
    elif isinstance(now, jdatetime.datetime):
        gdt = now.togregorian()
        if gdt.tzinfo is None:
            current_time = gdt.replace(tzinfo=TEHRAN_TZ)
        else:
            current_time = gdt.astimezone(TEHRAN_TZ)
    else:
        raise ValueError(f"Unsupported now type: {type(now)}")

    window_end = current_time + datetime.timedelta(hours=24)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, date, time, full_name, session_type
        FROM appointments
        WHERE status = 'confirmed'
          AND reminder_sent = 0
          AND user_id != 0
          AND user_id IS NOT NULL
        ORDER BY date, time
    ''')
    rows = cursor.fetchall()
    conn.close()

    due_appointments = []
    for row in rows:
        app_id, user_id, date_str, time_str, full_name, session_type = row
        if not date_str or not time_str:
            continue
        try:
            norm_date = config.normalize_digits(date_str).strip()
            norm_time = config.normalize_digits(time_str).strip()
            parts_date = norm_date.split('/')
            parts_time = norm_time.split(':')
            if len(parts_date) != 3 or len(parts_time) != 2:
                continue
            y, m, d = map(int, parts_date)
            h, mn = map(int, parts_time)
            appt_jdt = jdatetime.datetime(y, m, d, h, mn)
            appt_gdt = appt_jdt.togregorian().replace(tzinfo=TEHRAN_TZ)

            if current_time <= appt_gdt <= window_end:
                due_appointments.append(row)
        except Exception as e:
            logger.warning(f"Error parsing appointment {app_id} datetime ({date_str} {time_str}): {e}")
            continue

    return due_appointments

def mark_reminder_as_sent(appointment_id: int) -> None:
    """
    Updates reminder_sent = 1 and updated_at for the specified appointment.
    """
    conn = get_connection()
    cursor = conn.cursor()
    now_tehran_iso = datetime.datetime.now(TEHRAN_TZ).isoformat()
    cursor.execute('''
        UPDATE appointments
        SET reminder_sent = 1, updated_at = ?
        WHERE id = ?
    ''', (now_tehran_iso, int(appointment_id)))
    conn.commit()
    conn.close()

# اطمینان از مقداردهی اولیه جداول پایگاه داده در زمان بارگذاری ماژول
setup_database()

if __name__ == "__main__":
    setup_database()