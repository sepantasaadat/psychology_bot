from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import jdatetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
# #برای امنیت سشن‌ها (Session) و انتقال موقت داده‌ها بین صفحات
app.secret_key = 'super_secret_psychology_key'

# #آدرس دیتابیس مشترک با ربات
DATABASE = 'clinic.db'

# #تابع اتصال به دیتابیس با قابلیت تایم‌اوت برای جلوگیری از تداخل با ربات
def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

# #این تابع یک بار هنگام اجرای سایت اجرا می‌شود تا کاربر پیش‌فرض سایت را در دیتابیس بسازد
def setup_web_user():
    conn = get_db_connection()
    cursor = conn.cursor()
    # #آیدی 0 را برای کاربران سایت در نظر می‌گیریم
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, first_name, username) 
        VALUES (?, ?, ?)
    ''', (0, 'کاربر سایت', 'Website_Booking'))
    conn.commit()
    conn.close()

setup_web_user()

# ==========================================
# #منطق تولید روزها و ساعت‌ها
# ==========================================

def get_1405_working_days():
    # #لیست روزهای کاری سال 1405 (از تاریخ فعلی تا 30 روز آینده برای جلوگیری از شلوغی لیست)
    # #چون سال 1405 هنوز نرسیده، برای تست، تاریخ شروع را اول فروردین 1405 می‌گذاریم
    start_date = jdatetime.date(1405, 1, 1)
    
    # #اگر در سال 1405 بودیم، تاریخ امروز را مبدا قرار می‌دهیم
    today = jdatetime.date.today()
    if today.year == 1405:
        start_date = today

    days = []
    current_date = start_date
    added = 0
    
    # #فقط 15 روز کاری آینده را نشان می‌دهیم که منو خیلی طولانی نشود
    while added < 15:
        # #متد weekday در jdatetime: 0=شنبه، 4=چهارشنبه
        if current_date.weekday() <= 4:
            days.append(current_date.strftime("%Y/%m/%d"))
            added += 1
        current_date = current_date + jdatetime.timedelta(days=1)
    
    return days

def get_available_hours(selected_date):
    # #ساعت‌های کاری کلینیک
    all_hours = ["17:00", "18:00", "19:00", "20:00", "21:00"]
    
    # #خواندن ساعت‌های رزرو شده از دیتابیس برای این تاریخ
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = ? AND status IN ('pending', 'confirmed')", (selected_date,))
    booked_times = [row['time'] for row in cursor.fetchall()]
    conn.close()
    
    # #فیلتر کردن ساعت‌های پر شده
    available_hours = [h for h in all_hours if h not in booked_times]
    return available_hours

# ==========================================
# #مسیرهای سایت (Routes)
# ==========================================

@app.route('/')
def home():
    # #اینجا بعدا فایل HTML صفحه اصلی را رندر می‌کنیم
    return render_template('index.html')


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'GET':
        # دریافت لیست روزهای کاری برای نمایش در منوی کشویی
        days = get_1405_working_days()
        # ارسال متغیر days به فایل HTML
        return render_template('booking.html', days=days)
    
    if request.method == 'POST':
        # گرفتن اطلاعاتی که کاربر در فرم وارد کرده است
        selected_date = request.form.get('date')
        selected_time = request.form.get('time')
        full_name = request.form.get('full_name')
        session_type = request.form.get('session_type')
        
        # منطق جلوگیری از تداخل: بررسی اینکه آیا این ساعت قبلا توسط ربات یا سایت رزرو شده؟
        available_hours = get_available_hours(selected_date)
        if selected_time not in available_hours:
            # اگر ساعت پر بود، با flash پیام خطا می‌فرستیم و صفحه را دوباره لود می‌کنیم
            flash(f"متاسفانه ساعت {selected_time} در تاریخ {selected_date} پر شده است. لطفاً ساعت دیگری انتخاب کنید.", "danger")
            return redirect(url_for('booking'))
        
        # اگر ساعت خالی بود، اطلاعات موقتاً در سشن ذخیره شده و شخص به درگاه پرداخت می‌رود
        session['selected_date'] = selected_date
        session['selected_time'] = selected_time
        session['full_name'] = full_name
        session['session_type'] = session_type
        
        return redirect(url_for('payment'))

@app.route('/payment')
def payment():
    # #خواندن اطلاعات از سشن
    data = session
    return f"انتقال به درگاه پرداخت برای {data.get('full_name')} در تاریخ {data.get('selected_date')}"

# #بعد از پرداخت موفق، این مسیر اجرا می‌شود
@app.route('/verify_payment')
def verify_payment():
    # #... (کدهای قبلی ذخیره در دیتابیس) ...
    
    # #آماده‌سازی اطلاعات برای ایمیل
    details = {
        'full_name': session.get('full_name'),
        'date': session.get('selected_date'),
        'time': session.get('selected_time'),
        'session_type': session.get('session_type')
    }
    
    # #ارسال ایمیل فوری
    send_booking_email(details)
    
    # #ارسال گزارش کامل هفته (هر بار که نوبتی ثبت می‌شود لیست جدید را بفرستد)
    send_weekly_report()
    
    session.clear()
    return "پرداخت موفق بود و اطلاعات برای مدیریت ایمیل شد."


# #تنظیمات فرستنده ایمیل (پیشنهاد می‌شود از یک جیمیل برای فرستادن استفاده کنی)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sepantasaadat2000@gmail.com" # #ایمیلی که با آن ارسال می‌کنی
SENDER_PASSWORD = "kjwr kvkz sppu fysh" # #رمز ۱۶ رقمی App Password
RECEIVER_EMAIL = "sepas54@yahoo.com"  # #ایمیل مقصد شما

def send_booking_email(appointment_details):
    """# #ارسال مشخصات نوبت بلافاصله پس از پرداخت"""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"نوبت جدید: {appointment_details['full_name']}"

    # #بدنه ایمیل به صورت HTML برای ظاهر بهتر
    body = f"""
    <html>
        <body dir="rtl">
            <h3>رزرو نوبت جدید در سایت کلینیک دکتر شفایی</h3>
            <p><b>نام مراجع:</b> {appointment_details['full_name']}</p>
            <p><b>تاریخ:</b> {appointment_details['date']}</p>
            <p><b>ساعت:</b> {appointment_details['time']}</p>
            <p><b>نوع جلسه:</b> {appointment_details['session_type']}</p>
            <hr>
            <p>این نوبت در دیتابیس مشترک با ربات نیز ثبت شده است.</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    try:
        # #اتصال به سرور ایمیل و ارسال
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # #امن‌سازی اتصال
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("ایمیل تایید با موفقیت ارسال شد.")
    except Exception as e:
        print(f"خطا در ارسال ایمیل: {e}")

def send_weekly_report():
    """# #استخراج جلسات هفته و ارسال به صورت جدول"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # #در اینجا تمام نوبت‌های تایید شده را می‌گیریم
    # #می‌توانی کوئری را محدود به تاریخ‌های ۷ روز آینده کنی
    cursor.execute("SELECT full_name, date, time, session_type FROM appointments WHERE status = 'confirmed' ORDER BY date")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return

    # #ساخت جدول HTML برای ایمیل
    table_rows = ""
    for row in rows:
        table_rows += f"<tr><td>{row['full_name']}</td><td>{row['date']}</td><td>{row['time']}</td><td>{row['session_type']}</td></tr>"

    html_report = f"""
    <html dir="rtl">
        <body>
            <h2>لیست جلسات ثبت شده (سایت و ربات)</h2>
            <table border="1" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f2f2f2;">
                    <th>نام مراجع</th><th>تاریخ</th><th>ساعت</th><th>نوع</th>
                </tr>
                {table_rows}
            </table>
        </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "گزارش هفتگی کلینیک دکتر شفایی"
    msg.attach(MIMEText(html_report, 'html'))

    # #کد ارسال مشابه تابع قبلی است...
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()
if __name__ == '__main__':
    app.run(debug=True, port=5000)