from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import sqlite3
import jdatetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests
import json

# تنظیمات تلگرام برای ارسال عکس رسید
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [56073956, 77236438]

app = Flask(__name__)
app.secret_key = 'super_secret_psychology_key'
DATABASE = 'clinic.db'

# ساخت پوشه برای ذخیره موقت رسیدهای سایت
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

def setup_web_user():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, first_name, username) 
        VALUES (?, ?, ?)
    ''', (0, 'کاربر سایت', 'Website_Booking'))
    conn.commit()
    conn.close()

setup_web_user()

def get_1405_working_days():
    start_date = jdatetime.date(1405, 1, 1)
    today = jdatetime.date.today()
    if today.year == 1405:
        start_date = today

    days = []
    current_date = start_date
    added = 0
    while added < 15:
        if current_date.weekday() <= 4:
            days.append(current_date.strftime("%Y/%m/%d"))
            added += 1
        current_date = current_date + jdatetime.timedelta(days=1)
    return days

def get_available_hours(selected_date):
    all_hours = ["17:00", "18:00", "19:00", "20:00", "21:00"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = ? AND status IN ('pending', 'confirmed')", (selected_date,))
    booked_times = [row['time'] for row in cursor.fetchall()]
    conn.close()
    return [h for h in all_hours if h not in booked_times]

# ارسال درخواست و دکمه شیشه‌ای به تلگرام
def send_receipt_to_telegram(app_id, name_with_phone, date, time, session_type, filepath):
    caption = (
        f"🌐 درخواست نوبت جدید از **سایت**:\n\n"
        f"👤 نام و موبایل: {name_with_phone}\n"
        f"📅 تاریخ: {date}\n"
        f"⏰ ساعت: {time}\n"
        f"🩺 نوع جلسه: {session_type}\n"
        f"🆔 شناسه: {app_id}"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ تایید قطعی", "callback_data": f"approve_{app_id}"},
                {"text": "❌ رد فیش", "callback_data": f"reject_{app_id}"}
            ]
        ]
    }
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    for admin in ADMIN_IDS:
        try:
            with open(filepath, 'rb') as photo:
                payload = {
                    "chat_id": admin,
                    "caption": caption,
                    "reply_markup": json.dumps(reply_markup)
                }
                requests.post(url, data=payload, files={"photo": photo})
        except Exception as e:
            print(f"Error sending to telegram admin: {e}")

@app.route('/')

@app.route('/about')
def about():
    return render_template('about.html')

def home():
    return render_template('index.html')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'GET':
        days = get_1405_working_days()
        return render_template('booking.html', days=days)
    
    if request.method == 'POST':
        selected_date = request.form.get('date')
        selected_time = request.form.get('time')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        session_type = request.form.get('session_type')
        
        available_hours = get_available_hours(selected_date)
        if selected_time not in available_hours:
            flash(f"متاسفانه ساعت {selected_time} در تاریخ {selected_date} پر شده است.", "danger")
            return redirect(url_for('booking'))
            
        receipt_file = request.files.get('receipt')
        if not receipt_file or receipt_file.filename == '':
            flash("آپلود عکس رسید پرداخت الزامی است.", "danger")
            return redirect(url_for('booking'))
            
        filename = secure_filename(receipt_file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        receipt_file.save(filepath)
        
        # ترکیب نام و شماره تماس برای جلوگیری از تغییر دیتابیس
        name_with_phone = f"{full_name} | {phone}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
        ''', (0, selected_date, selected_time, session_type, name_with_phone, filepath))
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        send_receipt_to_telegram(app_id, name_with_phone, selected_date, selected_time, session_type, filepath)
        
        flash("✅ رسید شما با موفقیت ثبت و برای بررسی ارسال شد. نتیجه از طریق تماس یا پیامک به شما اطلاع داده خواهد شد.", "success")
        return redirect(url_for('booking'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

