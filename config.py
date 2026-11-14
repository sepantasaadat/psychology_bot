import os
import re
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import jdatetime

# Base directory and storage paths
BASE_DIR = Path(__file__).resolve().parent
PRIVATE_UPLOADS_DIR = BASE_DIR / 'private_uploads'

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Timezone & Calendar Configurations
TEHRAN_TZ = ZoneInfo("Asia/Tehran")

WORKING_WEEKDAYS = [0, 1, 2, 3, 4]  # 0: Saturday (شنبه) to 4: Wednesday (چهارشنبه)
WORKING_HOURS = ["16:00", "17:00", "18:00", "19:00", "20:00"]
MIN_ADVANCE_DAYS = 2
CANCELLATION_HOURS_LIMIT = 48

PERSIAN_WEEKDAYS = {
    0: "شنبه",
    1: "یکشنبه",
    2: "دوشنبه",
    3: "سه‌شنبه",
    4: "چهارشنبه",
}

# Administrative User IDs and Access Control
def _parse_admin_ids(env_val):
    if not env_val:
        return [56073956, 8034655716, 95033750]
    try:
        return [int(x.strip()) for x in env_val.split(",") if x.strip()]
    except Exception:
        return [56073956, 8034655716, 95033750]

ADMIN_IDS = _parse_admin_ids(os.environ.get("ADMIN_IDS"))
MAIN_ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 56073956
SECOND_ADMIN_ID = ADMIN_IDS[1] if len(ADMIN_IDS) > 1 else 8034655716
SEPANTA_ADMIN_ID = ADMIN_IDS[2] if len(ADMIN_IDS) > 2 else 95033750

# Clinic Reception Contact Details
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "drshafaei_psychological_clinic")
ADMIN_PHONE = os.environ.get("ADMIN_PHONE", "09213689461")
CLINIC_WEBSITE = os.environ.get("CLINIC_WEBSITE", "https://drshafaeiclinic.ir/")

# Bot & Web Application Credentials
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-insecure-secret-key-change-in-production")

# SMTP / Email Notification Configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
try:
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
except ValueError:
    SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "")

# Numeral normalization mapping
_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_ASCII_DIGITS = "0123456789"
_DIGIT_MAP = str.maketrans(_PERSIAN_DIGITS + _ARABIC_DIGITS, _ASCII_DIGITS + _ASCII_DIGITS)

def normalize_digits(text: str) -> str:
    """
    Converts Persian (۰-۹) and Arabic (٠-٩) numerals to ASCII digits (0-9).
    Safely handles None, non-string types, and strings without digits.
    """
    if text is None:
        return ""
    return str(text).translate(_DIGIT_MAP)

def validate_booking_request(
    date_str: str,
    time_str: str,
    full_name: str,
    phone: str = "",
    is_admin: bool = False,
    now=None
) -> tuple[bool, str]:
    """
    Unified booking validation rule set for both Web and Telegram Bot.
    
    Validates:
      1. full_name: non-empty, stripped length >= 3 -> (False, "invalid_name")
      2. phone (if provided): matches Iranian mobile ^09\\d{9}$ -> (False, "invalid_phone")
      3. time_str: in WORKING_HOURS -> (False, "invalid_time")
      4. date_str: valid Jalali date -> (False, "invalid_date")
      5. weekday: in WORKING_WEEKDAYS (0..4) -> (False, "non_working_day")
      6. advance notice:
         - date < today -> (False, "past_date")
         - not is_admin and date < today + timedelta(days=2) -> (False, "advance_notice_required")
      
    Returns:
      (True, "ok") on success.
    """
    # 1. Full name validation
    if not full_name or len(str(full_name).strip()) < 3:
        return (False, "invalid_name")

    # 2. Phone validation (if provided)
    if phone is not None and str(phone).strip():
        phone_norm = normalize_digits(phone).strip()
        if not re.match(r"^09\d{9}$", phone_norm):
            return (False, "invalid_phone")

    # 3. Time validation
    time_norm = normalize_digits(time_str).strip() if time_str else ""
    if time_norm not in WORKING_HOURS:
        return (False, "invalid_time")

    # 4. Date parsing validation
    date_norm = normalize_digits(date_str).strip() if date_str else ""
    try:
        parts = date_norm.split('/')
        if len(parts) != 3:
            return (False, "invalid_date")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        target_date = jdatetime.date(year, month, day)
    except Exception:
        return (False, "invalid_date")

    # 5. Weekday validation
    if target_date.weekday() not in WORKING_WEEKDAYS:
        return (False, "non_working_day")

    # 6. Advance notice & date range validation
    if now is None:
        now_tehran = datetime.datetime.now(TEHRAN_TZ)
        today = jdatetime.date.fromgregorian(date=now_tehran.date())
    elif isinstance(now, str):
        now_norm = normalize_digits(now)
        parts = [int(p) for p in now_norm.split('/')]
        today = jdatetime.date(parts[0], parts[1], parts[2])
    elif isinstance(now, jdatetime.datetime):
        today = now.date()
    elif isinstance(now, jdatetime.date):
        today = now
    elif isinstance(now, datetime.datetime):
        today = jdatetime.date.fromgregorian(date=now.date())
    elif isinstance(now, datetime.date):
        today = jdatetime.date.fromgregorian(date=now)
    else:
        raise ValueError(f"Unsupported now type: {type(now)}")

    if target_date < today:
        return (False, "past_date")

    if not is_admin and target_date < today + jdatetime.timedelta(days=MIN_ADVANCE_DAYS):
        return (False, "advance_notice_required")

    return (True, "ok")

def get_upcoming_working_days(days_count=5, is_admin=False, reference_date=None):
    """
    Generate dynamic rolling-window working days in Jalali calendar.
    
    Anchored to Asia/Tehran timezone when reference_date is None.
    Smoothly transitions across month and Nowruz year boundaries without hardcoded years.
    Regular users skip today and tomorrow (MIN_ADVANCE_DAYS = 2).
    Admins can reserve starting from reference_date.
    
    Returns a list of date strings in 'YYYY/MM/DD' format.
    """
    if reference_date is None:
        now_tehran = datetime.datetime.now(TEHRAN_TZ)
        start_date = jdatetime.date.fromgregorian(date=now_tehran.date())
    elif isinstance(reference_date, str):
        parts = [int(p) for p in reference_date.split('/')]
        start_date = jdatetime.date(parts[0], parts[1], parts[2])
    elif isinstance(reference_date, jdatetime.datetime):
        start_date = reference_date.date()
    elif isinstance(reference_date, jdatetime.date):
        start_date = reference_date
    elif isinstance(reference_date, datetime.datetime):
        start_date = jdatetime.date.fromgregorian(date=reference_date.date())
    elif isinstance(reference_date, datetime.date):
        start_date = jdatetime.date.fromgregorian(date=reference_date)
    else:
        raise ValueError(f"Unsupported reference_date type: {type(reference_date)}")

    if not is_admin:
        current_date = start_date + jdatetime.timedelta(days=MIN_ADVANCE_DAYS)
    else:
        current_date = start_date

    days = []
    while len(days) < days_count:
        if current_date.weekday() in WORKING_WEEKDAYS:
            days.append(current_date.strftime("%Y/%m/%d"))
        current_date = current_date + jdatetime.timedelta(days=1)

    return days
