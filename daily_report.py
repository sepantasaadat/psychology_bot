import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jdatetime

# تنظیمات ایمیل خود را اینجا وارد کنید
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sepantasaadat2000@gmail.com" # ایمیل فرستنده (ترجیحا جیمیل)
SENDER_PASSWORD = "kjwr kvkz sppu fysh" # رمز عبور App Password
RECEIVER_EMAIL = "sepas54@yahoo.com"  # ایمیل گیرنده
DATABASE = 'clinic.db'

def get_upcoming_week_appointments():
    # اتصال به دیتابیس
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # محاسبه تاریخ امروز و ۷ روز آینده
    today = jdatetime.date.today()
    next_week = today + jdatetime.timedelta(days=7)
    
    # تبدیل به فرمت رشته‌ای برای مقایسه با دیتابیس (مثال: 1405/02/15)
    today_str = today.strftime("%Y/%m/%d")
    next_week_str = next_week.strftime("%Y/%m/%d")
    
    # دریافت نوبت‌هایی که در بازه امروز تا هفته آینده هستند
    cursor.execute('''
        SELECT full_name, date, time, session_type 
        FROM appointments 
        WHERE status = 'confirmed' AND date >= ? AND date <= ?
        ORDER BY date, time
    ''', (today_str, next_week_str))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def send_email():
    rows = get_upcoming_week_appointments()
    
    if not rows:
        print("هیچ نوبتی برای هفته آینده ثبت نشده است. ایمیل ارسال نشد.")
        return

    # ساخت ردیف‌های جدول
    table_rows = ""
    for row in rows:
        table_rows += f"<tr><td>{row['full_name']}</td><td>{row['date']}</td><td>{row['time']}</td><td>{row['session_type']}</td></tr>"

    # ظاهر ایمیل با HTML و استایل‌های درون‌خطی
    html_report = f"""
    <html dir="rtl">
        <body style="font-family: Tahoma, Arial, sans-serif;">
            <h2 style="color: #2c3e50; text-align: center;">گزارش نوبت‌های یک هفته آینده کلینیک</h2>
            <table border="1" cellpadding="10" style="border-collapse: collapse; width: 100%; text-align: center; margin-top: 20px;">
                <tr style="background-color: #1abc9c; color: white;">
                    <th>نام مراجع</th><th>تاریخ</th><th>ساعت</th><th>نوع جلسه</th>
                </tr>
                {table_rows}
            </table>
        </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "گزارش خودکار شبانه: نوبت‌های هفته آینده"
    msg.attach(MIMEText(html_report, 'html'))

    # ارسال ایمیل
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("گزارش شبانه با موفقیت ایمیل شد.")
    except Exception as e:
        print(f"خطا در ارسال ایمیل: {e}")

if __name__ == "__main__":
    send_email()