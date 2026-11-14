import datetime
from zoneinfo import ZoneInfo
import jdatetime

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
    5: "پنج‌شنبه",
    6: "جمعه",
}

# Administrative User IDs
MAIN_ADMIN_ID = 56073956
SECOND_ADMIN_ID = 8034655716
SEPANTA_ADMIN_ID = 95033750
ADMIN_IDS = [MAIN_ADMIN_ID, SECOND_ADMIN_ID, SEPANTA_ADMIN_ID]

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
