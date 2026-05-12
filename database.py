import sqlite3

def get_connection():
    return sqlite3.connect("clinic.db")

def setup_database():
    conn = get_connection()
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
    cursor.execute('''
        INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
    ''', (user_id, date, time, session_type, full_name, receipt_file_id))
    
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return appointment_id

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

# [آپدیت ۹]: تابع حذف کامل یک نوبت برای آزاد شدن ساعت آن
def delete_appointment(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()