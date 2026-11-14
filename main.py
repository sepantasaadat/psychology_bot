import os
import jdatetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database  

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# استانداردهای نگارش و لحن پیام‌های کلینیک روان‌شناسی دکتر شفائی:
# ۱. لحن رسمی، محترمانه، آرامش‌بخش و مراجع‌محور (درود و احترام، مراجع ارجمند/گرامی).
# ۲. استفاده از ایموجی‌های ملایم و متناسب با روان‌شناسی و سلامت روان (🌱, 🌿, 🌸, 🧠, 🕊️, 📅, ⏰, 💳, 🏢, 💻, 🩺, 📋).
# ۳. پرهیز از ایموجی‌ها و واژه‌های اضطراب‌آور (مانند 🚨) در ارتباط با مراجعین.
# ==========================================
TOKEN = os.environ.get("BOT_TOKEN", "YOUR-BOT-TOKEN") # در سرور از متغیر محیطی خوانده می‌شود
BOT_USERNAME = "Drshafaeiclinic_bot"
BOT_NAME = "Drshafaei_clinic"
MAIN_ADMIN_ID = 56073956
SECOND_ADMIN_ID = 8034655716 # شناسه ادمین دوم کلینیک
SEPANTA_ADMIN_ID = 95033750 # شناسه دکتر سپنتا
ADMIN_IDS = [MAIN_ADMIN_ID, SECOND_ADMIN_ID, SEPANTA_ADMIN_ID] # لیست ادمین‌ها
ADMIN_USERNAME = "drshafaei_psychological_clinic" # آیدی تلگرام پذیرش کلینیک جهت هماهنگی و پشتیبانی
ADMIN_PHONE = "09213689461" # شماره تماس کلینیک
CLINIC_WEBSITE = "https://drshafaeiclinic.ir/" # آدرس وب‌سایت کلینیک
# ==========================================

# دیکشنری برای تبدیل شماره روز به نام روز فارسی [آپدیت ۳]
PERSIAN_WEEKDAYS = {
    0: "شنبه", 1: "یکشنبه", 2: "دوشنبه", 
    3: "سه‌شنبه", 4: "چهارشنبه"
}

def get_upcoming_days(days_count=5, is_admin=False, reference_date=None):
    days = []
    if reference_date is not None:
        start_date = reference_date
    else:
        start_date = jdatetime.date.today()
        if start_date.year < 1405:
            start_date = jdatetime.date(1405, 1, 1)

    # مراجعین عادی امکان رزرو برای امروز و فردا را ندارند
    if not is_admin:
        current_date = start_date + jdatetime.timedelta(days=2)
    else:
        current_date = start_date

    added = 0
    while added < days_count:
        if current_date.weekday() <= 4:
            # حالا به جای فقط تاریخ، نام روز را هم برمی‌گردانیم [آپدیت ۳]
            day_name = PERSIAN_WEEKDAYS[current_date.weekday()]
            days.append((current_date, day_name))
            added += 1
        current_date = current_date + jdatetime.timedelta(days=1)
    return days

# تابع گزارش نوبت‌های تایید شده ۷ روز آینده کلینیک
def format_upcoming_week_appointments(reference_date=None):
    if reference_date is not None:
        start_date = reference_date
    else:
        start_date = jdatetime.date.today()
        if start_date.year < 1405:
            start_date = jdatetime.date(1405, 1, 1)

    end_date = start_date + jdatetime.timedelta(days=6)
    start_str = start_date.strftime("%Y/%m/%d")
    end_str = end_date.strftime("%Y/%m/%d")

    appointments = database.get_upcoming_week_confirmed_appointments(start_str, end_str)
    if not appointments:
        return f"📋 برنامه کاری ۷ روز آینده (از {start_str} تا {end_str}):\nدر ۷ روز آینده هیچ نوبت قطعی ثبت نشده است. 🌱"

    lines = [f"📋 فهرست نوبت‌های تایید‌شده ۷ روز آینده (از {start_str} تا {end_str}):"]
    for appt in appointments:
        # appt: (id, date, time, full_name, session_type)
        _, d, t, name, stype = appt
        lines.append(f"• {d} | ساعت {t} | {name} ({stype})")

    return "\n".join(lines)

# توابع کمکی برای تحلیل زمان و اعمال قوانین لغو نوبت
def parse_appointment_datetime(date_str, time_str):
    y, m, d = map(int, date_str.split('/'))
    h, mn = map(int, time_str.split(':'))
    return jdatetime.datetime(y, m, d, h, mn)

def get_current_jalali_datetime(now=None):
    if now is not None:
        return now
    current = jdatetime.datetime.now()
    if current.year < 1405:
        current = current.replace(year=1405)
    return current

def can_cancel_appointment(date_str, time_str, now=None):
    appt_dt = parse_appointment_datetime(date_str, time_str)
    current_dt = get_current_jalali_datetime(now)
    diff_seconds = (appt_dt - current_dt).total_seconds()
    
    if diff_seconds <= 0:
        return False, "expired"
    if diff_seconds < 48 * 3600:
        return False, "within_48_hours"
    return True, "ok"

# تابع کمکی برای ساخت دکمه‌های منوی اصلی
def get_main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("🌱 رزرو وقت مشاوره جدید", callback_data="book_appointment")],
    ]

    # تولید داینامیک دکمه‌های لغو نوبت‌های تایید شده همین هفته (منحصراً برای مراجعین عادی و نه ادمین‌ها)
    if user_id not in ADMIN_IDS:
        start_date = jdatetime.date.today()
        if start_date.year < 1405:
            start_date = jdatetime.date(1405, 1, 1)
        end_date = start_date + jdatetime.timedelta(days=6)
        start_str = start_date.strftime("%Y/%m/%d")
        end_str = end_date.strftime("%Y/%m/%d")

        user_appts = database.get_user_confirmed_appointments_for_week(user_id, start_str, end_str)
        current_dt = get_current_jalali_datetime()
        for appt in user_appts:
            # appt: (id, date, time, full_name, session_type)
            app_id, d, t, _, _ = appt
            # حذف خودکار دکمه نوبت‌هایی که تاریخ و ساعت آن‌ها سپری شده است
            if parse_appointment_datetime(d, t) > current_dt:
                keyboard.append([InlineKeyboardButton(f"❌ لغو نوبت: {d} ساعت {t}", callback_data=f"user_cancel_{app_id}")])

    keyboard.extend([
        [InlineKeyboardButton("🤝 ارتباط با پذیرش و پشتیبانی", callback_data="emergency_contact")],
        [InlineKeyboardButton("🌐 وب‌سایت رسمی کلینیک", url=CLINIC_WEBSITE)],
    ])

    # نمایش پنل اختصاصی برای ادمین‌های مجاز
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ پنل مدیریت نوبت‌ها", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # پاک کردن حافظه موقت کاربر جهت شروع فرآیند تازه
    context.user_data.clear()
    user_id = update.effective_user.id
    username = update.effective_user.username or "None"
    logger.info(f"Command /start received from user {user_id} (@{username})")
    
    welcome_text = (
        "درود و احترام؛\n"
        "به سامانه رسمی نوبت‌دهی کلینیک روان‌شناسی دکتر شفائی خوش آمدید. 🌱\n\n"
        "ما متعهد به حفظ محرمانگی و همراهی شایسته شما در مسیر آرامش و سلامت روان هستیم.\n"
        "لطفاً جهت آغاز فرآیند رزرو نوبت یا هماهنگی با پذیرش، از منوی زیر استفاده فرمایید:"
    )
    await update.message.reply_text(
        welcome_text, 
        reply_markup=get_main_menu_keyboard(user_id)
    )

# تابع کمکی اتمام فرآیند بررسی ادمین: ریست نشست، ارسال برنامه هفتگی نوبت‌ها و بازگشت به منوی اصلی
async def complete_admin_review_session(query, context, user_id):
    context.user_data.clear()
    weekly_schedule = format_upcoming_week_appointments()
    await context.bot.send_message(chat_id=query.message.chat_id, text=weekly_schedule)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="منوی اصلی پذیرش و مدیریت کلینیک: 🌿",
        reply_markup=get_main_menu_keyboard(user_id)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    username = update.effective_user.username or "None"
    logger.info(f"Callback query '{query.data}' received from user {user_id} (@{username})")
    await query.answer()
    
    # ------------------ دکمه منوی اصلی ------------------
    if query.data == "main_menu":
        context.user_data.clear()
        await query.edit_message_text(
            "به منوی اصلی بازگشتید. لطفاً گزینه مورد نظر خود را انتخاب فرمایید: 🌿", 
            reply_markup=get_main_menu_keyboard(user_id)
        )

    # ------------------ ارتباط با پذیرش و پشتیبانی ------------------
    elif query.data == "emergency_contact":
        keyboard = [
            [InlineKeyboardButton("💬 گفت‌وگو با پذیرش در تلگرام", url=f"https://t.me/{ADMIN_USERNAME}")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        contact_text = (
            "🤝 ارتباط با پذیرش و پشتیبانی کلینیک روان‌شناسی دکتر شفائی:\n\n"
            "مراجع ارجمند، چنانچه پیش از رزرو نوبت نیاز به راهنمایی تخصصی، هماهنگی یا پاسخ به پرسش‌های خود دارید، از مسیرهای زیر پاسخگوی شما هستیم:\n\n"
            f"📞 تماس تلفنی با پذیرش: {ADMIN_PHONE}\n"
            f"💬 پشتیبانی تلگرام: @{ADMIN_USERNAME}\n\n"
            "ساعات پاسخگویی: شنبه تا چهارشنبه، هماهنگ با تقویم کاری کلینیک 🌱"
        )
        await query.edit_message_text(
            contact_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ------------------ پنل مدیریت نوبت‌ها (ویژه مدیریت) ------------------
    elif query.data == "admin_panel" and user_id in ADMIN_IDS:
        appointments = database.get_all_confirmed_appointments()
        if not appointments:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
            await query.edit_message_text(
                "در حال حاضر هیچ نوبت قطعی و تایید‌شده‌ای در سامانه ثبت نشده است. 📋", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
            
        keyboard = []
        for appt in appointments:
            # appt: (id, date, time, full_name, session_type)
            app_id, d, t, name, stype = appt
            btn_text = f"❌ لغو: {d} | ساعت {t} | {name}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"del_{app_id}")])
            
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
        await query.edit_message_text(
            "📋 فهرست نوبت‌های قطعی و تایید‌شده:\n\n"
            "جهت لغو نوبت و آزادسازی مجدد زمان مشاوره برای مراجعین، روی نوبت مورد نظر کلیک فرمایید:", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("del_") and user_id in ADMIN_IDS:
        app_id = query.data.split("_")[1]
        database.delete_appointment(app_id)
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")]]
        await query.edit_message_text(
            "✅ نوبت مشاوره با موفقیت لغو گردید و زمان آن مجدداً برای رزرو مراجعین آزاد شد. 🌱", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ------------------ لغو نوبت توسط مراجعین عادی ------------------
    elif query.data.startswith("user_cancel_"):
        app_id = query.data.split("_")[2]
        app_info = database.get_appointment(app_id)
        if not app_info:
            await query.edit_message_text(
                "⚠️ این نوبت قبلاً لغو شده یا یافت نشد.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return

        client_id, date, time, s_type, name, _ = app_info

        # بررسی ضوابط زمانی لغو نوبت (قانون ۴۸ ساعت و عدم انقضا)
        eligible, reason = can_cancel_appointment(date, time)
        if not eligible:
            if reason == "expired":
                await query.edit_message_text(
                    "⚠️ زمان این نوبت مشاوره سپری شده است و امکان لغو آن وجود ندارد. 🌱",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
            elif reason == "within_48_hours":
                apology_policy_text = (
                    "⚠️ مراجع گرامی؛\n"
                    "طبق ضوابط کلینیک، لغو نوبت مشاوره حداکثر تا ۴۸ ساعت پیش از موعد جلسه امکان‌پذیر می‌باشد.\n\n"
                    "با توجه به اینکه کمتر از ۴۸ ساعت تا زمان جلسه شما باقی مانده است، امکان لغو خودکار از طریق سامانه وجود ندارد.\n"
                    "در صورت نیاز اضطراری به هماهنگی، لطفاً مستقیماً با پذیرش کلینیک تماس حاصل فرمایید. 🌱"
                )
                await query.edit_message_text(
                    apology_policy_text,
                    reply_markup=get_main_menu_keyboard(user_id)
                )
            return

        # حذف مستقیم رکورد نوبت از پایگاه داده در صورت احراز شرایط لغو
        database.delete_appointment(app_id)

        # پیام تایید لغو به مراجع و بازسازی منوی اصلی مراجع بدون دکمه لغو شده
        cancel_ack_text = (
            f"✅ نوبت مشاوره شما مورخ {date} (ساعت {time}) با موفقیت لغو گردید. 🌱\n\n"
            "جهت رزرو نوبت جدید یا هماهنگی با پذیرش می‌توانید از منوی زیر استفاده فرمایید:"
        )
        await query.edit_message_text(
            cancel_ack_text,
            reply_markup=get_main_menu_keyboard(user_id)
        )

        # ارسال پیام اطلاع‌رسانی لغو نوبت به تمام ادمین‌ها و بازگرداندن نشست ادمین به منوی اصلی
        admin_alert_text = (
            "⚠️ گزارش لغو نوبت توسط مراجع:\n\n"
            f"👤 نام مراجع: {name}\n"
            f"📅 تاریخ جلسه: {date}\n"
            f"⏰ ساعت جلسه: {time}\n"
            f"🩺 نوع جلسه: {s_type}\n"
            f"🆔 شناسه نوبت: #{app_id}"
        )
        for admin in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin, text=admin_alert_text)
                await context.bot.send_message(
                    chat_id=admin,
                    text="منوی اصلی پذیرش و مدیریت کلینیک: 🌿",
                    reply_markup=get_main_menu_keyboard(admin)
                )
            except Exception as e:
                logger.error(f"Error sending cancellation alert to admin {admin}: {e}")

    # ------------------ فرآیند رزرو وقت مشاوره ------------------
    elif query.data == "book_appointment":
        is_admin = user_id in ADMIN_IDS
        upcoming_days = get_upcoming_days(5, is_admin=is_admin)
        keyboard = []
        for day_obj, day_name in upcoming_days:
            date_str = day_obj.strftime("%Y/%m/%d")
            keyboard.append([InlineKeyboardButton(f"🗓 {day_name} ({date_str})", callback_data=f"date_{date_str}")])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
        date_prompt_text = (
            "📅 گام اول: انتخاب تاریخ مشاوره\n\n"
            "لطفاً یکی از روزهای کاری کلینیک (شنبه تا چهارشنبه) را برای حضور یا برگزاری جلسه انتخاب فرمایید:"
        )
        await query.edit_message_text(date_prompt_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("date_"):
        selected_date = query.data.split("_")[1]
        
        # بررسی دسترسی نقش: مراجعین عادی مجاز به انتخاب تاریخ‌های گذشته، امروز یا فردا نیستند
        if user_id not in ADMIN_IDS:
            today_date = jdatetime.date.today()
            if today_date.year < 1405:
                today_date = jdatetime.date(1405, 1, 1)
            min_allowed_date = today_date + jdatetime.timedelta(days=2)
            min_allowed_str = min_allowed_date.strftime("%Y/%m/%d")
            
            if selected_date < min_allowed_str:
                keyboard = [[InlineKeyboardButton("🔙 بازگشت به انتخاب تاریخ", callback_data="book_appointment")]]
                await query.edit_message_text(
                    "⚠️ مراجع گرامی؛\n"
                    "رزرو نوبت برای امروز و فردا منحصراً از طریق تماس تلفنی با پذیرش کلینیک امکان‌پذیر می‌باشد.\n"
                    "لطفاً نوبت مورد نظر خود را از میان روزهای بعد انتخاب فرمایید. 🌱",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return

        booked_times = database.get_booked_times(selected_date)
        
        hours = ["17:00", "18:00", "19:00", "20:00", "21:00"]
        keyboard = []
        for hour in hours:
            if hour not in booked_times:
                end_hour = int(hour.split(":")[0]) + 1
                button_text = f"⏰ ساعت {hour} الی {end_hour}:00"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"time_{selected_date}_{hour}")])
        
        if not keyboard:
            keyboard.append([InlineKeyboardButton("⚠️ تمامی ساعت‌های این روز تکمیل است", callback_data="none")])
            
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به انتخاب تاریخ", callback_data="book_appointment")])
        time_prompt_text = (
            f"🗓 تاریخ انتخابی: {selected_date}\n\n"
            "⏰ گام دوم: انتخاب ساعت جلسه مشاوره\n"
            "لطفاً زمان مورد نظر خود را از میان ساعت‌های خالی زیر انتخاب فرمایید:"
        )
        await query.edit_message_text(time_prompt_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("time_"):
        _, selected_date, selected_time = query.data.split("_")
        
        # بررسی دسترسی نقش: مراجعین عادی مجاز به ثبت زمان برای تاریخ‌های گذشته، امروز یا فردا نیستند
        if user_id not in ADMIN_IDS:
            today_date = jdatetime.date.today()
            if today_date.year < 1405:
                today_date = jdatetime.date(1405, 1, 1)
            min_allowed_date = today_date + jdatetime.timedelta(days=2)
            min_allowed_str = min_allowed_date.strftime("%Y/%m/%d")
            
            if selected_date < min_allowed_str:
                keyboard = [[InlineKeyboardButton("🔙 بازگشت به انتخاب تاریخ", callback_data="book_appointment")]]
                await query.edit_message_text(
                    "⚠️ مراجع گرامی؛\n"
                    "رزرو نوبت برای امروز و فردا منحصراً از طریق تماس تلفنی با پذیرش کلینیک امکان‌پذیر می‌باشد.\n"
                    "لطفاً نوبت مورد نظر خود را از میان روزهای بعد انتخاب فرمایید. 🌱",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return

        context.user_data['selected_date'] = selected_date
        context.user_data['selected_time'] = selected_time
        
        keyboard = [
            [InlineKeyboardButton("💻 مشاوره آنلاین", callback_data="type_آنلاین")],
            [InlineKeyboardButton("🏢 مشاوره حضوری", callback_data="type_حضوری")],
            [InlineKeyboardButton("🔙 بازگشت به انتخاب ساعت", callback_data=f"date_{selected_date}")]
        ]
        type_prompt_text = (
            f"🗓 تاریخ: {selected_date} | ⏰ ساعت: {selected_time}\n\n"
            "🌿 گام سوم: شیوه برگزاری جلسه مشاوره\n"
            "لطفاً شیوه مورد نظر خود را تعیین فرمایید:"
        )
        await query.edit_message_text(type_prompt_text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("type_"):
        session_type = query.data.split("_")[1]
        context.user_data['session_type'] = session_type
        
        context.user_data['state'] = 'awaiting_name'
        
        keyboard = [[InlineKeyboardButton("❌ انصراف و بازگشت", callback_data="main_menu")]]
        name_prompt_text = (
            f"🌿 شیوه جلسه: {session_type}\n\n"
            "👤 گام چهارم: مشخصات مراجع ارجمند\n\n"
            "لطفاً نام و نام خانوادگی کامل خود را جهت ثبت پرونده و صدور نوبت ارسال فرمایید:"
        )
        await query.edit_message_text(name_prompt_text, reply_markup=InlineKeyboardMarkup(keyboard))

    # ------------------ تایید / رد ادمین‌ها [آپدیت ۱ و ۲] ------------------
    elif query.data.startswith("approve_") or query.data.startswith("reject_"):
        action, appointment_id = query.data.split("_")
        
        app_info = database.get_appointment(appointment_id)
        if not app_info:
            await query.edit_message_caption(
                caption="⚠️ این نوبت در دیتابیس یافت نشد!",
                reply_markup=None
            )
            await complete_admin_review_session(query, context, user_id)
            return
            
        client_id, date, time, s_type, name, current_status = app_info

        # جلوگیری از تداخل دو ادمین: اگر قبلاً تایید/رد شده، دیگر کاری نکن
        if current_status != "pending":
            base_caption = query.message.caption or ""
            await query.edit_message_caption(
                caption=f"{base_caption}\n\n⚠️ این نوبت قبلاً توسط ادمین دیگری تعیین تکلیف شده است.",
                reply_markup=None
            )
            await complete_admin_review_session(query, context, user_id)
            return

        if action == "approve":
            database.update_appointment_status(appointment_id, "confirmed")
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n✅ توسط شما تایید قطعی شد.",
                reply_markup=None
            )
            
            # ارسال تاییدیه قطعی به مراجع
            if client_id != 0:
                client_confirm_text = (
                    f"🌸 مراجع ارجمند، جناب/سرکار {name}؛\n\n"
                    "✅ رسید پرداخت شما بررسی و نوبت مشاوره شما با موفقیت قطعی گردید.\n\n"
                    "📋 مشخصات نوبت قطعی شما:\n"
                    f"📅 تاریخ جلسه: {date}\n"
                    f"⏰ ساعت جلسه: {time}\n"
                    f"🩺 نوع جلسه: {s_type}\n\n"
                    "📍 یادآوری مراجعین حضوری: لطفاً ۱۰ دقیقه پیش از موعد در کلینیک حضور داشته باشید.\n"
                    "💻 یادآوری مراجعین آنلاین: لینک ورود پیش از آغاز جلسه هماهنگ خواهد شد.\n\n"
                    "با آرزوی آرامش و تندرستی روان برای شما 🌱"
                )
                await context.bot.send_message(
                    chat_id=client_id, 
                    text=client_confirm_text,
                    reply_markup=get_main_menu_keyboard(client_id)
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"📞 این نوبت از طریق وب‌سایت ثبت شده است. لطفاً جهت هماهنگی نهایی با مراجع گرامی تماس حاصل فرمایید:\n{name}"
                )

            # حذف پیام رسید و دکمه‌ها برای سایر ادمین‌ها و ارسال برنامه به‌روزشده هفتگی + منوی اصلی
            other_receipt_msgs = database.get_admin_receipt_messages(appointment_id)
            weekly_schedule_text = format_upcoming_week_appointments()
            for admin_id, msg_id in other_receipt_msgs:
                if admin_id != user_id:
                    try:
                        await context.bot.delete_message(chat_id=admin_id, message_id=msg_id)
                    except Exception as e:
                        logger.error(f"Error deleting receipt message for admin {admin_id}: {e}")
                    
                    try:
                        await context.bot.send_message(chat_id=admin_id, text=weekly_schedule_text)
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text="منوی اصلی پذیرش و مدیریت کلینیک: 🌿",
                            reply_markup=get_main_menu_keyboard(admin_id)
                        )
                    except Exception as e:
                        logger.error(f"Error sending schedule/menu to admin {admin_id}: {e}")
            
            database.delete_admin_receipt_messages(appointment_id)

        elif action == "reject":
            database.update_appointment_status(appointment_id, "rejected")
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n❌ توسط شما رد شد.",
                reply_markup=None
            )
            
            if client_id != 0:
                client_reject_text = (
                    f"مراجع ارجمند، جناب/سرکار {name}؛\n\n"
                    f"⚠️ متأسفانه رسید واریزی ارسالی برای وقت مشاوره مورخ {date} (ساعت {time}) مورد تایید قرار نگرفت (به‌دلیل عدم انطباق یا ناخوانا بودن رسید).\n\n"
                    "در صورت تمایل به پیگیری، با پذیرش کلینیک تماس حاصل فرمایید یا از طریق منو مجدداً اقدام کنید. 🌿"
                )
                await context.bot.send_message(
                    chat_id=client_id, 
                    text=client_reject_text,
                    reply_markup=get_main_menu_keyboard(client_id)
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"📞 این نوبت از طریق وب‌سایت بود و رد شد. در صورت نیاز با شماره درج شده تماس بگیرید:\n{name}"
                )

            database.delete_admin_receipt_messages(appointment_id)

        # ریست خودکار نشست ادمین، ارسال برنامه هفتگی نوبت‌ها و بازگشت به منوی اصلی
        await complete_admin_review_session(query, context, user_id)

# هندلر دریافت پیام‌های متنی (نام مراجع و پاسخ عمومی)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'awaiting_name':
        full_name = update.message.text.strip()
        user = update.effective_user
        user_id = user.id

        # در صورتی که رزروکننده یکی از ادمین‌های کلینیک باشد، مرحله ارسال فیش و تایید ادمین بایپس شده و نوبت مستقیماً ثبت قطعی می‌گردد
        if user_id in ADMIN_IDS:
            date = context.user_data.get('selected_date')
            time = context.user_data.get('selected_time')
            session_type = context.user_data.get('session_type')

            database.add_user(user.id, user.first_name, user.username)
            appointment_id = database.add_confirmed_appointment(
                user_id=user.id,
                date=date,
                time=time,
                session_type=session_type,
                full_name=full_name,
                receipt_file_id="admin_direct"
            )

            context.user_data.clear()

            confirm_msg = (
                "✅ وقت مشاوره با موفقیت به‌صورت مستقیم ثبت قطعی شد. 🌱\n\n"
                "📋 مشخصات نوبت ثبت‌شده:\n"
                f"👤 نام مراجع: {full_name}\n"
                f"📅 تاریخ جلسه: {date}\n"
                f"⏰ ساعت جلسه: {time}\n"
                f"🩺 نوع جلسه: {session_type}\n"
                f"🆔 کد پیگیری: #{appointment_id}"
            )
            await update.message.reply_text(confirm_msg)

            # ارسال برنامه هفتگی نوبت‌ها و بازگشت به منوی اصلی
            weekly_schedule = format_upcoming_week_appointments()
            await update.message.reply_text(weekly_schedule)
            await update.message.reply_text(
                "منوی اصلی پذیرش و مدیریت کلینیک: 🌿",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return

        context.user_data['full_name'] = full_name
        
        # تغییر وضعیت به انتظار برای دریافت فیش واریزی
        context.user_data['state'] = 'awaiting_receipt'
        
        keyboard = [[InlineKeyboardButton("❌ انصراف و بازگشت", callback_data="main_menu")]]
        receipt_request_text = (
            f"سپاسگزاریم، مراجع گرامی جناب/سرکار {full_name} 🌸\n\n"
            "💳 گام نهایی: بارگذاری رسید پرداخت حق‌المشاوره\n\n"
            "جهت نهایی‌سازی درخواست رزرو، لطفاً تصویر واضح فیش واریزی خود را در همین گفتگو ارسال فرمایید.\n\n"
            "⏳ پس از ارسال تصویر، اطلاعات نوبت جهت بررسی و ثبت قطعی در اختیار پذیرش کلینیک قرار خواهد گرفت."
        )
        await update.message.reply_text(
            receipt_request_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        user_id = update.effective_user.id
        username = update.effective_user.username or "None"
        logger.info(f"Text message received outside booking from user {user_id} (@{username}): {update.message.text}")
        general_prompt_text = (
            "درود و احترام؛ 🌱\n"
            "به سامانه نوبت‌دهی کلینیک روان‌شناسی دکتر شفائی خوش آمدید.\n"
            "لطفاً جهت رزرو وقت مشاوره، ارتباط با پذیرش یا مشاهده وب‌سایت کلینیک، از گزینه‌های زیر استفاده فرمایید:"
        )
        await update.message.reply_text(
            general_prompt_text, 
            reply_markup=get_main_menu_keyboard(user_id)
        )

# تابع دریافت عکس فیش
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'awaiting_receipt':
        # اگر کاربر در مرحله فیش نیست و عکسی فرستاد
        return

    photo_file_id = update.message.photo[-1].file_id
    user = update.effective_user
    
    date = context.user_data['selected_date']
    time = context.user_data['selected_time']
    session_type = context.user_data['session_type']
    full_name = context.user_data['full_name']

    database.add_user(user.id, user.first_name, user.username)
    # [آپدیت ۷ و ۸]: ارسال دیتای جدید به دیتابیس
    appointment_id = database.add_pending_appointment(user.id, date, time, session_type, full_name, photo_file_id)

    # پایان پروسه برای این کاربر
    context.user_data.clear()

    user_receipt_ack = (
        "✅ رسید پرداخت شما با موفقیت دریافت و ثبت اولیه گردید. 🌱\n\n"
        "درخواست رزرو نوبت شما در اختیار همکاران پذیرش کلینیک قرار گرفت.\n"
        "به محض بررسی و تایید، تاییدیه قطعی نوبت در همین گفتگو به اطلاع شما خواهد رسید.\n\n"
        "با سپاس از صبوری و همراهی ارزشمند شما 🌿"
    )
    await update.message.reply_text(user_receipt_ack)

    # دکمه‌ها و مشخصات ارسالی برای ادمین‌های کلینیک (اندازه متناسب با صفحه نمایش)
    keyboard = [
        [
            InlineKeyboardButton("✅ تایید نوبت", callback_data=f"approve_{appointment_id}"),
            InlineKeyboardButton("❌ رد رسید", callback_data=f"reject_{appointment_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_handle = f"@{user.username}" if user.username else "ندارد"
    caption = (
        "📋 درخواست جدید رزرو وقت مشاوره:\n\n"
        f"👤 نام مراجع: {full_name}\n"
        f"🔗 شناسه تلگرام: {user_handle}\n"
        f"📅 تاریخ جلسه: {date}\n"
        f"⏰ ساعت جلسه: {time}\n"
        f"🩺 نوع جلسه: {session_type}\n"
        f"🆔 کد پیگیری: #{appointment_id}"
    )
    
    # [آپدیت ۱]: ارسال پیام تایید به صورت حلقه‌ای برای تمام ادمین‌های لیست شده
    for admin in ADMIN_IDS:
        try:
            sent_msg = await context.bot.send_photo(
                chat_id=admin,
                photo=photo_file_id,
                caption=caption,
                reply_markup=reply_markup
            )
            database.save_admin_receipt_message(appointment_id, admin, sent_msg.message_id)
        except Exception as e:
            logger.error(f"خطا در ارسال برای ادمین {admin}: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

def main():
    database.setup_database()
    app = Application.builder().token(TOKEN).build()
    
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)) # اضافه شدن هندلر متن برای دریافت نام و شروع
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    
    print(f"Bot {BOT_NAME} (@{BOT_USERNAME}) version 2.0 is running on VPS...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()