import jdatetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database  

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
TOKEN = "YOUR-BOT-TOKEN" # (همان توکنی که در سرور گذاشتید را اینجا قرار دهید)
MAIN_ADMIN_ID = 56073956
SECOND_ADMIN_ID = 77236438
ADMIN_IDS = [MAIN_ADMIN_ID, SECOND_ADMIN_ID] # [آپدیت ۱]: لیست ادمین‌ها
CLINIC_WEBSITE = "https://example.com" # [آپدیت ۵]: آدرس سایت کلینیک را اینجا جایگزین کنید
# ==========================================

# دیکشنری برای تبدیل شماره روز به نام روز فارسی [آپدیت ۳]
PERSIAN_WEEKDAYS = {
    0: "شنبه", 1: "یکشنبه", 2: "دوشنبه", 
    3: "سه‌شنبه", 4: "چهارشنبه"
}

def get_upcoming_days(days_count=5):
    days = []
    current_date = jdatetime.date.today()
    if current_date.year < 1405:
        current_date = jdatetime.date(1405, 1, 1)

    added = 0
    while added < days_count:
        if current_date.weekday() <= 4:
            # حالا به جای فقط تاریخ، نام روز را هم برمی‌گردانیم [آپدیت ۳]
            day_name = PERSIAN_WEEKDAYS[current_date.weekday()]
            days.append((current_date, day_name))
            added += 1
        current_date = current_date + jdatetime.timedelta(days=1)
    return days

# تابع کمکی برای ساخت دکمه‌های منوی اصلی (تا بتوانیم کاربر را دوباره به اینجا برگردانیم) [آپدیت ۲ و ۴ و ۵ و ۹]
def get_main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("📅 رزرو نوبت جدید", callback_data="book_appointment")],
        [
            # [آپدیت ۴]: لینک مستقیم به چت ادمین اول. (tg://user?id=...)
            InlineKeyboardButton("🚨 ارتباط اضطراری با ادمین", url=f"tg://user?id={MAIN_ADMIN_ID}"),
            # [آپدیت ۵]: لینک سایت کلینیک
            InlineKeyboardButton("🌐 سایت کلینیک دکتر شفایی", url=CLINIC_WEBSITE)
        ]
    ]
    # [آپدیت ۹]: اگر کاربر همان ادمین اصلی است، دکمه مدیریت را به او نشان بده
    if user_id == MAIN_ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ پنل مدیریت نوبت‌ها (مخصوص شما)", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # پاک کردن حافظه موقت کاربر تا از صفر شروع کند
    context.user_data.clear()
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "سلام! به سیستم نوبت‌دهی کلینیک دکتر شفایی خوش آمدید.\nلطفاً از منوی زیر انتخاب کنید:", 
        reply_markup=get_main_menu_keyboard(user_id)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    
    # ------------------ دکمه منوی اصلی ------------------
    if query.data == "main_menu":
        context.user_data.clear()
        await query.edit_message_text(
            "شما به منوی اصلی بازگشتید. لطفاً انتخاب کنید:", 
            reply_markup=get_main_menu_keyboard(user_id)
        )

    # ------------------ پنل مدیریت ادمین [آپدیت ۹] ------------------
    elif query.data == "admin_panel" and user_id == MAIN_ADMIN_ID:
        appointments = database.get_all_confirmed_appointments()
        if not appointments:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
            await query.edit_message_text("هیچ نوبت تایید شده‌ای برای حذف وجود ندارد.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        keyboard = []
        for appt in appointments:
            # appt: (id, date, time, full_name, session_type)
            app_id, d, t, name, stype = appt
            btn_text = f"❌ لغو: {d} {t} | {name} ({stype})"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"del_{app_id}")])
            
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
        await query.edit_message_text("لیست نوبت‌های تایید شده:\nبرای لغو و آزاد شدن ساعت، روی هر کدام کلیک کنید.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("del_") and user_id == MAIN_ADMIN_ID:
        app_id = query.data.split("_")[1]
        database.delete_appointment(app_id)
        # بعد از حذف یک نوبت، پنل ادمین را دوباره لود می‌کنیم تا لیست جدید نشان داده شود
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")]]
        await query.edit_message_text("✅ نوبت با موفقیت حذف شد و ساعت آن مجدداً آزاد گردید.", reply_markup=InlineKeyboardMarkup(keyboard))

    # ------------------ پروسه رزرو نوبت ------------------
    elif query.data == "book_appointment":
        upcoming_days = get_upcoming_days(5)
        keyboard = []
        for day_obj, day_name in upcoming_days: # [آپدیت ۳]: استفاده از نام روز
            date_str = day_obj.strftime("%Y/%m/%d")
            keyboard.append([InlineKeyboardButton(f"🗓 {day_name} - {date_str}", callback_data=f"date_{date_str}")])
        
        # [آپدیت ۶]: دکمه برگشت به منوی قبلی
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
        await query.edit_message_text("لطفاً یکی از روزهای کاری را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("date_"):
        selected_date = query.data.split("_")[1]
        booked_times = database.get_booked_times(selected_date)
        
        hours = ["17:00", "18:00", "19:00", "20:00", "21:00"]
        keyboard = []
        for hour in hours:
            if hour not in booked_times:
                end_hour = int(hour.split(":")[0]) + 1
                button_text = f"⏰ {hour} تا {end_hour}:00"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"time_{selected_date}_{hour}")])
        
        if not keyboard:
            keyboard.append([InlineKeyboardButton("❌ تمام وقت‌های این روز پر است", callback_data="none")])
            
        # [آپدیت ۶]: دکمه برگشت به روزها
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به لیست روزها", callback_data="book_appointment")])
        await query.edit_message_text(f"روز انتخاب شده: {selected_date}\nلطفاً ساعت را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("time_"):
        _, selected_date, selected_time = query.data.split("_")
        
        context.user_data['selected_date'] = selected_date
        context.user_data['selected_time'] = selected_time
        
        # [آپدیت ۸]: پرسیدن نوع جلسه (حضوری/آنلاین)
        keyboard = [
            [InlineKeyboardButton("🖥 آنلاین (غیرحضوری)", callback_data="type_آنلاین")],
            [InlineKeyboardButton("🏢 حضوری (در کلینیک)", callback_data="type_حضوری")],
            [InlineKeyboardButton("🔙 بازگشت به ساعت‌ها", callback_data=f"date_{selected_date}")]
        ]
        await query.edit_message_text(
            f"✅ تاریخ: {selected_date} | ساعت: {selected_time}\n\n"
            "لطفاً نوع جلسه مورد نظر خود را انتخاب کنید:", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("type_"):
        session_type = query.data.split("_")[1]
        context.user_data['session_type'] = session_type
        
        # [آپدیت ۷]: درخواست نام و نام خانوادگی (تغییر State ربات)
        context.user_data['state'] = 'awaiting_name'
        
        # در اینجا چون منتظر تایپ متن هستیم، دکمه شیشه‌ای برای لغو می‌گذاریم
        keyboard = [[InlineKeyboardButton("❌ انصراف و بازگشت به منوی اصلی", callback_data="main_menu")]]
        await query.edit_message_text(
            f"نوع جلسه: {session_type}\n\n"
            "👤 **لطفاً نام و نام خانوادگی خود را در یک پیام تایپ کرده و ارسال کنید:**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ------------------ تایید / رد ادمین‌ها [آپدیت ۱ و ۲] ------------------
    elif query.data.startswith("approve_") or query.data.startswith("reject_"):
        action, appointment_id = query.data.split("_")
        
        app_info = database.get_appointment(appointment_id)
        if not app_info:
            await query.edit_message_caption(caption="⚠️ این نوبت در دیتابیس یافت نشد!")
            return
            
        client_id, date, time, s_type, name, current_status = app_info

        # جلوگیری از تداخل دو ادمین: اگر قبلاً تایید/رد شده، دیگر کاری نکن
        if current_status != "pending":
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n⚠️ این نوبت قبلاً توسط ادمین دیگری تعیین تکلیف شده است.")
            return

            if action == "approve":
                database.update_appointment_status(appointment_id, "confirmed")
                await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ **توسط شما تایید شد**")
            
            # اگر client_id صفر بود، یعنی کاربر از سایت آمده است
            if client_id != 0:
                await context.bot.send_message(
                    chat_id=client_id, 
                    text=f"🎉 تبریک {name} عزیز! فیش شما تایید شد.\n\n📅 تاریخ: {date}\n⏰ ساعت: {time}\nنوع جلسه: {s_type}\nنوبت شما قطعی شد.",
                    reply_markup=get_main_menu_keyboard(client_id)
                )
            else:
                # ارسال نوتیفیکیشن به ادمین برای تماس با مراجع سایت
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"📞 این نوبت از طریق سایت ثبت شده است. لطفاً برای تایید نوبت با شماره درج شده تماس بگیرید یا پیامک دهید:\n{name}"
                )

        elif action == "reject":
            database.update_appointment_status(appointment_id, "rejected")
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ **توسط شما رد شد**")
            
            if client_id != 0:
                await context.bot.send_message(
                    chat_id=client_id, 
                    text=f"❌ متاسفانه فیش شما برای نوبت {date} تایید نشد. لطفاً در صورت نیاز مجدداً اقدام کنید.",
                    reply_markup=get_main_menu_keyboard(client_id)
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"📞 این نوبت از طریق سایت بود و رد شد. در صورت نیاز با شماره درج شده تماس بگیرید:\n{name}"
                )


            
            # [آپدیت ۲]: پیام رد به کاربر + منوی اصلی
            await context.bot.send_message(
                chat_id=client_id, 
                text=f"❌ متاسفانه فیش شما برای نوبت {date} تایید نشد. لطفاً در صورت نیاز مجدداً از منو اقدام کنید.",
                reply_markup=get_main_menu_keyboard(client_id)
            )

# [آپدیت ۷]: هندلر جدید برای دریافت نام و نام خانوادگی به صورت متنی
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'awaiting_name':
        full_name = update.message.text
        context.user_data['full_name'] = full_name
        
        # تغییر وضعیت ربات به انتظار برای عکس فیش
        context.user_data['state'] = 'awaiting_receipt'
        
        keyboard = [[InlineKeyboardButton("❌ انصراف از رزرو", callback_data="main_menu")]]
        await update.message.reply_text(
            f"ممنون {full_name} عزیز.\n\n"
            "💳 **مرحله آخر:** لطفاً همین الان عکس فیش پرداختی خود را ارسال کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
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

    await update.message.reply_text(
        "✅ فیش شما با موفقیت دریافت شد و برای ادمین‌ها ارسال گردید.\n"
        "پس از بررسی، نتیجه همینجا به شما اعلام خواهد شد."
    )

    # [آپدیت ۱]: دکمه‌ها و کپشن برای ارسال به ادمین‌ها
    keyboard = [
        [
            InlineKeyboardButton("✅ تایید قطعی", callback_data=f"approve_{appointment_id}"),
            InlineKeyboardButton("❌ رد فیش", callback_data=f"reject_{appointment_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = (
        f"🆕 درخواست نوبت جدید:\n\n"
        f"👤 نام ثبت شده: {full_name}\n"
        f"🔗 آیدی تلگرام: @{user.username}\n"
        f"📅 تاریخ: {date}\n"
        f"⏰ ساعت: {time}\n"
        f"🩺 نوع جلسه: {session_type}\n"
        f"🆔 شناسه: {appointment_id}"
    )
    
    # [آپدیت ۱]: ارسال پیام تایید به صورت حلقه‌ای برای تمام ادمین‌های لیست شده
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin,
                photo=photo_file_id,
                caption=caption,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"خطا در ارسال برای ادمین {admin}: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)) # اضافه شدن هندلر متن برای دریافت نام
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    
    print("Bot version 2.0 is running on VPS...")
    app.run_polling()

if __name__ == '__main__':
    main()