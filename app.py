from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
import sqlite3
import jdatetime
import os
import requests
import json
import logging
import config
import database
from security import process_and_save_receipt

# Suppress noisy external loggers
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Telegram settings for receipt forwarding
BOT_TOKEN = os.environ.get("BOT_TOKEN", config.BOT_TOKEN)
ADMIN_IDS = config.ADMIN_IDS

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', config.FLASK_SECRET_KEY)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB upload limit
app.config.setdefault('WTF_CSRF_ENABLED', True)
csrf = CSRFProtect(app)
DATABASE = database.DB_PATH

# Private folder for receipt uploads outside web root
PRIVATE_UPLOADS_FOLDER = getattr(config, 'PRIVATE_UPLOADS_DIR', os.path.join(config.BASE_DIR, 'private_uploads'))
os.makedirs(PRIVATE_UPLOADS_FOLDER, exist_ok=True)

def get_db_connection():
    conn = database.get_connection()
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
    return config.get_upcoming_working_days(15, is_admin=False)

def get_available_hours(selected_date):
    selected_date = config.normalize_digits(selected_date)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = ? AND status IN ('pending', 'confirmed')", (selected_date,))
    booked_times = [row['time'] for row in cursor.fetchall()]
    conn.close()
    return [h for h in config.WORKING_HOURS if h not in booked_times]

# Send appointment notification and inline buttons to admins via Telegram
def send_receipt_to_telegram(app_id, name_with_phone, date, time, session_type, filepath):
    caption = (
        "🌐 درخواست جدید وقت مشاوره از وب‌سایت:\n\n"
        f"👤 نام و تماس مراجع: {name_with_phone}\n"
        f"📅 تاریخ جلسه: {date}\n"
        f"⏰ ساعت جلسه: {time}\n"
        f"🩺 نوع جلسه: {session_type}\n"
        f"🆔 کد پیگیری: #{app_id}"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ تایید نوبت", "callback_data": f"approve_{app_id}"},
                {"text": "❌ رد رسید", "callback_data": f"reject_{app_id}"}
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
                res = requests.post(url, data=payload, files={"photo": photo})
                if res.status_code == 200:
                    res_data = res.json()
                    msg_id = res_data.get("result", {}).get("message_id")
                    if msg_id:
                        database.save_admin_receipt_message(app_id, admin, msg_id)
        except Exception as e:
            logger.error(f"Error sending receipt notification to admin {admin}: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/booking', methods=['GET', 'POST'])
@app.route('/reserve', methods=['GET', 'POST'])
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
        
        # Unified validation
        is_valid, error_code = config.validate_booking_request(
            date_str=selected_date,
            time_str=selected_time,
            full_name=full_name,
            phone=phone,
            is_admin=False
        )
        if not is_valid:
            error_messages = {
                "invalid_phone": "شماره موبایل وارد شده نامعتبر است. لطفاً شماره موبایل ۱۱ رقمی معتبر (مثال: 09123456789) وارد فرمایید.",
                "advance_notice_required": "رزرو نوبت برای امروز و فردا امکان‌پذیر نیست. لطفاً نوبت خود را حداقل از ۲ روز قبل انتخاب فرمایید.",
                "past_date": "امکان انتخاب تاریخ‌های سپری‌شده وجود ندارد. لطفاً یک تاریخ معتبر انتخاب فرمایید.",
                "non_working_day": "روز انتخابی خارج از روزهای کاری کلینیک (شنبه تا چهارشنبه) است.",
                "invalid_time": "ساعت انتخابی نامعتبر است. لطفاً از میان ساعت‌های مجاز کاری کلینیک انتخاب فرمایید.",
                "invalid_date": "فرمت یا مقدار تاریخ انتخابی نامعتبر است.",
                "invalid_name": "لطفاً نام و نام خانوادگی کامل مراجع (حداقل ۳ حرف) را وارد فرمایید."
            }
            msg = error_messages.get(error_code, "اطلاعات ارسالی نامعتبر است.")
            flash(msg, "danger")
            return render_template('booking.html', days=get_1405_working_days()), 400

        # Digits normalization
        selected_date = config.normalize_digits(selected_date).strip()
        selected_time = config.normalize_digits(selected_time).strip()
        phone = config.normalize_digits(phone).strip() if phone else ""
        full_name = full_name.strip() if full_name else ""

        available_hours = get_available_hours(selected_date)
        if selected_time not in available_hours:
            flash(f"متاسفانه ساعت {selected_time} در تاریخ {selected_date} پر شده است.", "danger")
            return render_template('booking.html', days=get_1405_working_days()), 400
            
        receipt_file = request.files.get('receipt')
        if not receipt_file or receipt_file.filename == '':
            flash("آپلود عکس رسید پرداخت الزامی است.", "danger")
            return render_template('booking.html', days=get_1405_working_days()), 400
            
        try:
            filepath = process_and_save_receipt(receipt_file, dest_dir=PRIVATE_UPLOADS_FOLDER)
        except ValueError as e:
            logger.warning(f"Rejected invalid receipt upload: {e}")
            flash("فایل ارسال شده نامعتبر یا فاقد فرمت تصویری مجاز است. لطفاً یک تصویر معتبر (JPG، PNG، WEBP) ارسال فرمایید.", "danger")
            return render_template('booking.html', days=get_1405_working_days()), 400
        
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
        
        logger.info(f"Web booking submitted successfully: appointment_id={app_id}")
        send_receipt_to_telegram(app_id, name_with_phone, selected_date, selected_time, session_type, filepath)
        
        flash("✅ رسید شما با موفقیت ثبت و برای بررسی ارسال شد. نتیجه از طریق تماس یا پیامک به شما اطلاع داده خواهد شد.", "success")
        return redirect(url_for('booking'))

if __name__ == '__main__':
    app.run(debug=False, port=5000)
