from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, abort
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from pathlib import Path
import sqlite3
import jdatetime
import os
import time
import threading
import hmac
from collections import defaultdict
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
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or getattr(config, 'FLASK_SECRET_KEY', None) or os.urandom(32).hex()
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit
app.config.setdefault('WTF_CSRF_ENABLED', True)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
is_testing = app.config.get('TESTING', False) or os.environ.get("FLASK_DEBUG") == "1"
app.config['SESSION_COOKIE_SECURE'] = not is_testing
csrf = CSRFProtect(app)
DATABASE = database.DB_PATH

# Thread-safe in-memory rate limiting for booking submissions
_booking_rate_limit_lock = threading.Lock()
_booking_rate_limit_records = defaultdict(list)

def is_booking_rate_limited(ip_address: str, max_requests: int = 5, window_seconds: int = 60) -> bool:
    """Thread-safe sliding window rate limiter per IP address for booking submissions."""
    now = time.time()
    with _booking_rate_limit_lock:
        if len(_booking_rate_limit_records) > 5000:
            stale = [ip for ip, ts in _booking_rate_limit_records.items() if not ts or now - ts[-1] > window_seconds]
            for ip in stale:
                del _booking_rate_limit_records[ip]
        timestamps = _booking_rate_limit_records[ip_address]
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]
        if len(valid_timestamps) >= max_requests:
            _booking_rate_limit_records[ip_address] = valid_timestamps
            return True
        valid_timestamps.append(now)
        _booking_rate_limit_records[ip_address] = valid_timestamps
        return False

@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp
    if not app.config.get('TESTING') and (os.environ.get("FLASK_ENV") == "production" or os.environ.get("ENABLE_HSTS", "1") == "1"):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

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
    token = os.environ.get("BOT_TOKEN") or getattr(config, "BOT_TOKEN", "") or "dummy_token"

    admin_ids = config.ADMIN_IDS
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
    
    photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
    msg_url = f"https://api.telegram.org/bot{token}/sendMessage"

    for admin in admin_ids:
        photo_sent = False
        try:
            with open(filepath, 'rb') as photo:
                payload = {
                    "chat_id": admin,
                    "caption": caption,
                    "reply_markup": json.dumps(reply_markup)
                }
                res = requests.post(photo_url, data=payload, files={"photo": photo}, timeout=10)
                if res.status_code == 200:
                    res_data = res.json()
                    msg_id = res_data.get("result", {}).get("message_id")
                    if msg_id:
                        database.save_admin_receipt_message(app_id, admin, msg_id)
                    photo_sent = True
                    logger.info(f"Telegram receipt photo sent successfully to admin {admin} for app_id={app_id}")
                else:
                    logger.warning(f"Telegram sendPhoto returned HTTP {res.status_code} for admin {admin}: {res.text}")
        except Exception as e:
            logger.error(f"Error sending receipt photo to admin {admin}: {e}")

        # Fallback to plain text message if photo failed
        if not photo_sent:
            try:
                fallback_payload = {
                    "chat_id": admin,
                    "text": f"{caption}\n\n⚠️ تصویر فیش در سرور ذخیره شد اما ارسال مستقیم عکس به تلگرام ناموفق بود. لطفاً از پنل مدیریت وب یا ربات اقدام فرمایید.",
                    "reply_markup": json.dumps(reply_markup)
                }
                res_msg = requests.post(msg_url, json=fallback_payload, timeout=10)
                if res_msg.status_code == 200:
                    res_data = res_msg.json()
                    msg_id = res_data.get("result", {}).get("message_id")
                    if msg_id:
                        database.save_admin_receipt_message(app_id, admin, msg_id)
                    logger.info(f"Fallback text receipt sent to admin {admin} for app_id={app_id}")
                else:
                    logger.error(f"Telegram sendMessage fallback returned HTTP {res_msg.status_code} for admin {admin}: {res_msg.text}")
            except Exception as e_msg:
                logger.error(f"Error sending fallback text to admin {admin}: {e_msg}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('index.html')

@app.route('/get_times/<path:date>')
@app.route('/api/available-times/<path:date>')
def get_available_times_api(date):
    norm_date = config.normalize_digits(date).strip()
    available = database.get_available_times(norm_date)
    return {"available_times": available, "date": norm_date}

@app.route('/booking', methods=['GET', 'POST'], endpoint='booking')
@app.route('/reserve', methods=['GET', 'POST'], endpoint='reserve')
def booking():
    if request.method == 'GET':
        days = get_1405_working_days()
        return render_template('booking.html', days=days, card_number=config.CARD_NUMBER)
    
    if request.method == 'POST':
        is_ajax = (
            request.headers.get("X-Requested-With") == "XMLHttpRequest" or
            request.form.get("is_ajax") == "1" or
            request.accept_mimetypes.best == "application/json"
        )
        client_ip = request.remote_addr or "127.0.0.1"
        if not app.config.get('TESTING') and is_booking_rate_limited(client_ip, max_requests=10, window_seconds=60):
            logger.warning(f"Rate limit exceeded for booking requests from client_ip={client_ip}")
            error_msg = "تعداد درخواست‌های ارسالی شما بیش از حد مجاز است. لطفاً چند دقیقه دیگر مجدداً تلاش فرمایید."
            if is_ajax:
                return {"success": False, "error": error_msg}, 429
            flash(error_msg, "danger")
            return render_template('booking.html', days=get_1405_working_days(), card_number=config.CARD_NUMBER), 429

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
            if is_ajax:
                return {"success": False, "error": msg}, 400
            flash(msg, "danger")
            return render_template('booking.html', days=get_1405_working_days(), card_number=config.CARD_NUMBER), 400

        # Digits normalization
        selected_date = config.normalize_digits(selected_date).strip()
        selected_time = config.normalize_digits(selected_time).strip()
        phone = config.normalize_digits(phone).strip() if phone else ""
        full_name = full_name.strip() if full_name else ""

        available_hours = get_available_hours(selected_date)
        if selected_time not in available_hours:
            msg = f"متاسفانه ساعت {selected_time} در تاریخ {selected_date} پر شده است."
            if is_ajax:
                return {"success": False, "error": msg}, 400
            flash(msg, "danger")
            return render_template('booking.html', days=get_1405_working_days(), card_number=config.CARD_NUMBER), 400
            
        receipt_file = request.files.get('receipt')
        if not receipt_file or receipt_file.filename == '':
            msg = "آپلود عکس رسید پرداخت الزامی است."
            if is_ajax:
                return {"success": False, "error": msg}, 400
            flash(msg, "danger")
            return render_template('booking.html', days=get_1405_working_days(), card_number=config.CARD_NUMBER), 400
            
        try:
            filepath = process_and_save_receipt(receipt_file, dest_dir=PRIVATE_UPLOADS_FOLDER)
        except ValueError as e:
            logger.warning(f"Rejected invalid receipt upload: {e}")
            msg = "فایل ارسال شده نامعتبر یا فاقد فرمت تصویری مجاز است. لطفاً یک تصویر معتبر (JPG، PNG، WEBP) ارسال فرمایید."
            if is_ajax:
                return {"success": False, "error": msg}, 400
            flash(msg, "danger")
            return render_template('booking.html', days=get_1405_working_days(), card_number=config.CARD_NUMBER), 400
        
        name_with_phone = f"{full_name} | {phone}"
        
        try:
            app_id = database.add_pending_appointment(
                user_id=0,
                date=selected_date,
                time=selected_time,
                session_type=session_type,
                full_name=name_with_phone,
                receipt_file_id=filepath
            )
        except (database.SlotAlreadyBookedError, sqlite3.IntegrityError):
            logger.warning(f"Concurrent double booking prevented on web for slot {selected_date} {selected_time}")
            msg = f"متاسفانه ساعت {selected_time} در تاریخ {selected_date} لحظاتی پیش توسط مراجع دیگری رزرو شد."
            if is_ajax:
                return {"success": False, "error": msg}, 409
            flash(msg, "danger")
            return render_template('booking.html', days=get_1405_working_days(), card_number=config.CARD_NUMBER), 409
        
        logger.info(f"Web booking submitted successfully: appointment_id={app_id}")
        if app.config.get('TESTING'):
            send_receipt_to_telegram(app_id, name_with_phone, selected_date, selected_time, session_type, filepath)
        else:
            threading.Thread(
                target=send_receipt_to_telegram,
                args=(app_id, name_with_phone, selected_date, selected_time, session_type, filepath),
                daemon=True
            ).start()
        
        success_msg = "رسید شما با موفقیت ثبت و برای بررسی ارسال شد. نتیجه از طریق تماس یا پیامک به شما اطلاع داده خواهد شد."
        if is_ajax:
            return {
                "success": True,
                "message": success_msg,
                "appointment_id": app_id,
                "date": selected_date,
                "time": selected_time,
                "full_name": full_name,
                "session_type": session_type
            }, 200

        flash(f"✅ {success_msg}", "success")
        return redirect(url_for('booking', _external=True, _scheme='https'))

# Thread-safe in-memory rate limiting for admin login attempts
_login_rate_limit_lock = threading.Lock()
_login_rate_limit_records = defaultdict(list)

def is_login_rate_limited(ip_address: str, max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """Thread-safe sliding window rate limiter per IP address for login attempts."""
    now = time.time()
    with _login_rate_limit_lock:
        if len(_login_rate_limit_records) > 5000:
            stale = [ip for ip, ts in _login_rate_limit_records.items() if not ts or now - ts[-1] > window_seconds]
            for ip in stale:
                del _login_rate_limit_records[ip]
        timestamps = _login_rate_limit_records[ip_address]
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]
        if len(valid_timestamps) >= max_attempts:
            _login_rate_limit_records[ip_address] = valid_timestamps
            return True
        valid_timestamps.append(now)
        _login_rate_limit_records[ip_address] = valid_timestamps
        return False

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'], endpoint='admin_login')
@app.route('/admin/login', methods=['GET', 'POST'], endpoint='admin_login_alias')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        client_ip = request.remote_addr or "127.0.0.1"
        if not app.config.get('TESTING') and is_login_rate_limited(client_ip):
            flash("تعداد دفعات ورود ناموفق بیش از حد مجاز است. لطفاً ۵ دقیقه بعد مجدداً تلاش فرمایید.", "danger")
            return render_template('admin_login.html'), 429

        password = request.form.get('password', '')
        admin_pwd = getattr(config, 'ADMIN_PASSWORD', '')
        admin_hash = getattr(config, 'ADMIN_PASSWORD_HASH', '')

        authenticated = False
        if admin_hash and admin_hash.startswith(('pbkdf2:', 'scrypt:')):
            authenticated = check_password_hash(admin_hash, password)
        elif admin_pwd:
            authenticated = hmac.compare_digest(password, admin_pwd)

        if authenticated:
            session['admin_logged_in'] = True
            session.permanent = False
            flash("با موفقیت وارد پنل مدیریت شدید.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("رمز عبور مدیر کلینیک نادرست است.", "danger")
            return render_template('admin_login.html'), 401

    return render_template('admin_login.html')

@app.route('/logout', endpoint='admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("از پنل مدیریت خارج شدید.", "info")
    return redirect(url_for('admin_login'))

@app.context_processor
def inject_admin_helpers():
    return {
        'is_appointment_past': config.is_appointment_past
    }

@app.template_filter('is_past')
def is_past_filter(appt):
    if len(appt) > 5:
        return bool(appt[5])
    return config.is_appointment_past(appt[1], appt[2])

@app.route('/admin', endpoint='admin_dashboard')
@app.route('/admin/dashboard', endpoint='admin_dashboard_alias')
@admin_required
def admin_dashboard():
    pending_appointments = database.get_all_pending_appointments()
    confirmed_appointments = database.get_all_confirmed_appointments()
    confirmed_with_past_flag = [
        (*appt, config.is_appointment_past(appt[1], appt[2]))
        for appt in confirmed_appointments
    ]
    return render_template(
        'admin_dashboard.html',
        pending=pending_appointments,
        confirmed=confirmed_with_past_flag
    )

@app.route('/admin/receipt/<int:appointment_id>', endpoint='admin_view_receipt')
@admin_required
def admin_view_receipt(appointment_id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT receipt_file_id FROM appointments WHERE id = ?", (appointment_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        abort(404)

    receipt_path = row[0]
    if not os.path.isabs(receipt_path):
        receipt_path = os.path.join(PRIVATE_UPLOADS_FOLDER, os.path.basename(receipt_path))

    real_folder = Path(PRIVATE_UPLOADS_FOLDER).resolve()
    real_file = Path(receipt_path).resolve()

    try:
        if not real_file.is_relative_to(real_folder) or not real_file.is_file():
            abort(404)
    except AttributeError:
        if os.path.commonpath([str(real_folder)]) != os.path.commonpath([str(real_folder), str(real_file)]) or not real_file.is_file():
            abort(404)

    return send_file(str(real_file))

@app.route('/admin/approve/<int:appointment_id>', methods=['POST'], endpoint='admin_approve')
@admin_required
def admin_approve(appointment_id):
    database.update_appointment_status(appointment_id, 'confirmed')
    flash(f"نوبت شماره #{appointment_id} با موفقیت تایید و قطعی گردید.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:appointment_id>', methods=['POST'], endpoint='admin_reject')
@admin_required
def admin_reject(appointment_id):
    database.update_appointment_status(appointment_id, 'rejected')
    flash(f"نوبت شماره #{appointment_id} رد شد و زمان آن مجدداً آزاد گردید.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/cancel/<int:appointment_id>', methods=['POST'], endpoint='admin_cancel')
@admin_required
def admin_cancel(appointment_id):
    appt = database.get_appointment(appointment_id)
    if not appt:
        flash("نوبت مورد نظر یافت نشد.", "warning")
        return redirect(url_for('admin_dashboard'))

    # appt is (user_id, date, time, session_type, full_name, status)
    if config.is_appointment_past(appt[1], appt[2]):
        flash("امکان لغو نوبت‌های برگزارشده (سپری‌شده) وجود ندارد.", "warning")
        return redirect(url_for('admin_dashboard'))

    database.delete_appointment(appointment_id)
    flash(f"نوبت شماره #{appointment_id} لغو و حذف گردید.", "info")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, port=5000)
