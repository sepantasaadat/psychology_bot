import jdatetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database  

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
TOKEN = "YOUR-TOKEN-HERE"
THERAPIST_CHAT_ID = "56073956"  
# ==========================================

def get_upcoming_days(days_count=5):
    days = []
    current_date = jdatetime.date.today()
    if current_date.year < 1405:
        current_date = jdatetime.date(1405, 1, 1)

    added = 0
    while added < days_count:
        if current_date.weekday() <= 4:
            days.append(current_date)
            added += 1
        current_date = current_date + jdatetime.timedelta(days=1)
    return days

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📅 رزرو نوبت جدید", callback_data="book_appointment")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("سلام! برای مشاهده وقت‌های خالی و رزرو نوبت، کلیک کنید:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "book_appointment":
        upcoming_days = get_upcoming_days(5)
        keyboard = []
        for day in upcoming_days:
            date_str = day.strftime("%Y/%m/%d")
            keyboard.append([InlineKeyboardButton(f"🗓 {date_str}", callback_data=f"date_{date_str}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("لطفاً یکی از روزهای کاری را انتخاب کنید:", reply_markup=reply_markup)
        
    elif query.data.startswith("date_"):
        selected_date = query.data.split("_")[1]
        
        # [تغییر جدید]: بررسی دیتابیس برای پیدا کردن ساعت‌های رزرو شده
        booked_times = database.get_booked_times(selected_date)
        
        hours = ["17:00", "18:00", "19:00", "20:00", "21:00"]
        keyboard = []
        for hour in hours:
            # فقط ساعت‌هایی که در لیست رزرو شده‌ها نیستند را نشان می‌دهیم
            if hour not in booked_times:
                end_hour = int(hour.split(":")[0]) + 1
                button_text = f"⏰ {hour} تا {end_hour}:00"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"time_{selected_date}_{hour}")])
        
        if not keyboard: # اگر همه ساعت‌ها پر بود
            keyboard.append([InlineKeyboardButton("❌ تمام وقت‌های این روز پر است", callback_data="none")])
            
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به روزها", callback_data="book_appointment")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"روز: {selected_date}\nلطفاً ساعت را انتخاب کنید:", reply_markup=reply_markup)
        
    elif query.data.startswith("time_"):
        _, selected_date, selected_time = query.data.split("_")
        
        context.user_data['selected_date'] = selected_date
        context.user_data['selected_time'] = selected_time
        context.user_data['awaiting_receipt'] = True  
        
        await query.edit_message_text(
            f"✅ شما تاریخ {selected_date} ساعت {selected_time} را انتخاب کردید.\n\n"
            "💳 **مرحله الزامی:** لطفاً همین الان عکس فیش پرداختی خود را در همین چت ارسال کنید."
        )

    # ==========================================
    # [تغییر جدید]: هندل کردن دکمه‌های تایید و رد توسط تراپیست
    # ==========================================
    elif query.data.startswith("approve_") or query.data.startswith("reject_"):
        action, appointment_id = query.data.split("_")
        
        # گرفتن اطلاعات نوبت از دیتابیس
        appointment_info = database.get_appointment(appointment_id)
        if not appointment_info:
            await query.edit_message_caption(caption="⚠️ این نوبت در دیتابیس یافت نشد!")
            return
            
        user_id, date, time = appointment_info

        if action == "approve":
            database.update_appointment_status(appointment_id, "confirmed")
            # ویرایش پیام تراپیست تا دکمه‌ها حذف شوند
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ **تایید شد**")
            
            # ارسال پیام موفقیت به مراجع
            await context.bot.send_message(
                chat_id=user_id, 
                text=f"🎉 تبریک! فیش شما تایید شد.\n\n📅 تاریخ: {date}\n⏰ ساعت: {time}\nنوبت شما با موفقیت ثبت گردید."
            )
            
            # تولید و ارسال برنامه آپدیت شده برای تراپیست
            schedule = database.get_weekly_schedule()
            schedule_text = "📊 **برنامه آپدیت شده کلینیک:**\n\n"
            for row in schedule:
                # row: (date, time, first_name, username)
                username_str = f"(@{row[3]})" if row[3] else ""
                schedule_text += f"🔹 {row[0]} - ساعت {row[1]} : {row[2]} {username_str}\n"
            
            await context.bot.send_message(chat_id=THERAPIST_CHAT_ID, text=schedule_text)

        elif action == "reject":
            database.update_appointment_status(appointment_id, "rejected")
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ **رد شد**")
            
            # ارسال پیام به مراجع
            await context.bot.send_message(
                chat_id=user_id, 
                text=f"❌ متاسفانه فیش پرداختی شما برای نوبت {date} ساعت {time} تایید نشد. لطفاً در صورت بروز مشکل با پشتیبانی تماس بگیرید."
            )

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_receipt'):
        await update.message.reply_text("شما در حال حاضر نوبتی انتخاب نکرده‌اید. لطفاً از طریق منو اقدام کنید.")
        return

    photo_file_id = update.message.photo[-1].file_id
    user = update.effective_user
    
    date = context.user_data['selected_date']
    time = context.user_data['selected_time']

    database.add_user(user.id, user.first_name, user.username)
    appointment_id = database.add_pending_appointment(user.id, date, time, photo_file_id)

    context.user_data['awaiting_receipt'] = False

    await update.message.reply_text("✅ فیش شما با موفقیت دریافت شد و برای تراپیست ارسال گردید.\nمنتظر تایید باشید...")

    keyboard = [
        [
            InlineKeyboardButton("✅ تایید و ثبت", callback_data=f"approve_{appointment_id}"),
            InlineKeyboardButton("❌ رد فیش", callback_data=f"reject_{appointment_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = (
        f"🆕 درخواست نوبت جدید:\n\n"
        f"👤 مراجع: {user.first_name} (@{user.username})\n"
        f"📅 تاریخ: {date}\n"
        f"⏰ ساعت: {time}\n"
        f"🆔 شناسه: {appointment_id}"
    )
    
    await context.bot.send_photo(
        chat_id=THERAPIST_CHAT_ID,
        photo=photo_file_id,
        caption=caption,
        reply_markup=reply_markup
    )

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    
    print("Bot is ready for VPS Deployment...")
    app.run_polling()

if __name__ == '__main__':
    main()