import os
import sqlite3
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import jdatetime
import config
import database

logger = logging.getLogger(__name__)

# Load configurations from environment or config
SMTP_SERVER = os.environ.get("SMTP_SERVER", config.SMTP_SERVER)
try:
    SMTP_PORT = int(os.environ.get("SMTP_PORT", str(config.SMTP_PORT)))
except ValueError:
    SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", config.SENDER_EMAIL)
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", config.SENDER_PASSWORD)
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", config.RECEIVER_EMAIL)
BOT_TOKEN = os.environ.get("BOT_TOKEN", config.BOT_TOKEN)
ADMIN_IDS = config.ADMIN_IDS
DATABASE = database.DB_PATH

def get_upcoming_week_appointments():
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    today = jdatetime.date.today()
    next_week = today + jdatetime.timedelta(days=7)
    
    today_str = today.strftime("%Y/%m/%d")
    next_week_str = next_week.strftime("%Y/%m/%d")
    
    cursor.execute('''
        SELECT full_name, date, time, session_type 
        FROM appointments 
        WHERE status = 'confirmed' AND date >= ? AND date <= ?
        ORDER BY date, time
    ''', (today_str, next_week_str))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def send_email(rows=None):
    """
    Channel 1: Sends formatted HTML table of upcoming appointments via SMTP.
    """
    sender = SENDER_EMAIL
    password = SENDER_PASSWORD
    receiver = RECEIVER_EMAIL
    server_host = SMTP_SERVER
    server_port = SMTP_PORT

    if not sender or not password or not receiver:
        logger.warning("SMTP email credentials are not fully configured. Email report skipped.")
        return False

    if rows is None:
        rows = get_upcoming_week_appointments()
    
    if not rows:
        logger.info("No confirmed appointments for the upcoming week. Email not sent.")
        return False

    table_rows = ""
    for row in rows:
        name = row['full_name'] if isinstance(row, (dict, sqlite3.Row)) else row[0]
        d = row['date'] if isinstance(row, (dict, sqlite3.Row)) else row[1]
        t = row['time'] if isinstance(row, (dict, sqlite3.Row)) else row[2]
        stype = row['session_type'] if isinstance(row, (dict, sqlite3.Row)) else row[3]
        table_rows += f"<tr><td>{name}</td><td>{d}</td><td>{t}</td><td>{stype}</td></tr>"

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
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = "گزارش خودکار شبانه: نوبت‌های هفته آینده"
    msg.attach(MIMEText(html_report, 'html'))

    try:
        server = smtplib.SMTP(server_host, server_port)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        logger.info("Nightly report successfully emailed.")
        return True
    except Exception as e:
        logger.error(f"Error sending email report: {e}")
        return False

def send_telegram_broadcast(rows=None) -> int:
    """
    Channel 2: Sends formatted text summary to all ADMIN_IDS via Telegram sendMessage API.
    Returns the count of successfully notified administrators.
    """
    token = BOT_TOKEN
    admin_list = ADMIN_IDS

    if not token:
        logger.warning("BOT_TOKEN is not configured. Telegram broadcast skipped.")
        return 0

    if not admin_list:
        logger.warning("ADMIN_IDS is empty. Telegram broadcast skipped.")
        return 0

    if rows is None:
        rows = get_upcoming_week_appointments()

    today = jdatetime.date.today()
    next_week = today + jdatetime.timedelta(days=7)
    today_str = today.strftime("%Y/%m/%d")
    next_week_str = next_week.strftime("%Y/%m/%d")

    if rows:
        lines = [f"📋 گزارش نوبت‌های ۷ روز آینده کلینیک (از {today_str} تا {next_week_str}):\n"]
        for row in rows:
            name = row['full_name'] if isinstance(row, (dict, sqlite3.Row)) else row[0]
            d = row['date'] if isinstance(row, (dict, sqlite3.Row)) else row[1]
            t = row['time'] if isinstance(row, (dict, sqlite3.Row)) else row[2]
            stype = row['session_type'] if isinstance(row, (dict, sqlite3.Row)) else row[3]
            lines.append(f"• {name} | {d} ساعت {t} ({stype})")
        lines.append(f"\n🌱 مجموع نوبت‌های تایید‌شده: {len(rows)} جلسه")
        telegram_text = "\n".join(lines)
    else:
        telegram_text = (
            f"📋 گزارش نوبت‌های ۷ روز آینده کلینیک (از {today_str} تا {next_week_str}):\n\n"
            "در حال حاضر هیچ نوبت قطعی ثبت‌شده‌ای برای هفته آینده وجود ندارد. 🌱"
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    delivered = 0

    for admin_id in admin_list:
        try:
            payload = {
                "chat_id": admin_id,
                "text": telegram_text,
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                delivered += 1
                logger.info(f"Daily report sent via Telegram to admin {admin_id}")
            else:
                logger.error(f"Failed to send Telegram report to admin {admin_id}: HTTP {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram report to admin {admin_id}: {e}")

    return delivered

def send_daily_report():
    """
    Dual-channel daily reporting dispatcher:
    Channel 1: SMTP Email (HTML table)
    Channel 2: Telegram Admin Broadcast (formatted text)
    Failures in one channel do not block the other.
    """
    logger.info("Initiating dual-channel daily clinic report...")
    rows = get_upcoming_week_appointments()

    # Channel 1: SMTP Email
    try:
        send_email(rows)
    except Exception as e:
        logger.error(f"SMTP daily report channel exception: {e}")

    # Channel 2: Telegram Admin Broadcast
    try:
        send_telegram_broadcast(rows)
    except Exception as e:
        logger.error(f"Telegram broadcast daily report channel exception: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    send_daily_report()
