import sqlite3

# تابعی برای اتصال به دیتابیس
def get_connection():
    # اگر فایل clinic.db وجود نداشته باشد، آن را می‌سازد
    return sqlite3.connect("clinic.db")

# تابعی برای ساخت جداول اولیه
def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    # ساخت جدول کاربران (مراجعین)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT
        )
    ''')

    # ساخت جدول نوبت‌ها
    # وضعیت‌ها (status) می‌توانند این موارد باشند:
    # pending: منتظر تایید تراپیست
    # confirmed: تایید شده نهایی
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,          -- مثال: 1405/01/15
            time TEXT,          -- مثال: 17:00
            status TEXT,        -- pending یا confirmed
            receipt_file_id TEXT, -- آیدی عکس رسید در تلگرام
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database tables created successfully!")
# تابع برای ثبت کاربر در دیتابیس (اگر از قبل وجود نداشته باشد)
def add_user(user_id, first_name, username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, first_name, username) 
        VALUES (?, ?, ?)
    ''', (user_id, first_name, username))
    conn.commit()
    conn.close()

# تابع برای ثبت نوبت در انتظار تایید
def add_pending_appointment(user_id, date, time, receipt_file_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (user_id, date, time, status, receipt_file_id)
        VALUES (?, ?, ?, 'pending', ?)
    ''', (user_id, date, time, receipt_file_id))
    
    # گرفتن آیدی (ID) این نوبت که الان در دیتابیس ساخته شد
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return appointment_id

# تغییر وضعیت نوبت (تایید یا رد)
def update_appointment_status(appointment_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE appointments SET status = ? WHERE id = ?', (status, appointment_id))
    conn.commit()
    conn.close()

# دریافت اطلاعات یک نوبت خاص
def get_appointment(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, date, time FROM appointments WHERE id = ?', (appointment_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# پیدا کردن ساعت‌های پر شده در یک روز خاص
def get_booked_times(date):
    conn = get_connection()
    cursor = conn.cursor()
    # هم نوبت‌های تایید شده و هم در حال انتظار را پر فرض می‌کنیم تا تداخل نشود
    cursor.execute("SELECT time FROM appointments WHERE date = ? AND status IN ('pending', 'confirmed')", (date,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# دریافت کل برنامه هفتگی تراپیست
def get_weekly_schedule():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT appointments.date, appointments.time, users.first_name, users.username 
        FROM appointments 
        JOIN users ON appointments.user_id = users.user_id 
        WHERE status = 'confirmed' 
        ORDER BY appointments.date, appointments.time
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows
# اگر این فایل مستقیم اجرا شود، دیتابیس را می‌سازد
if __name__ == "__main__":
    setup_database()