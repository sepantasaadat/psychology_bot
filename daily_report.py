import os
import sqlite3
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jdatetime
import config
import database

logger = logging.getLogger(__name__)

# Load email configurations from environment or config
SMTP_SERVER = os.environ.get("SMTP_SERVER", config.SMTP_SERVER)
SMTP_PORT = int(os.environ.get("SMTP_PORT", str(config.SMTP_PORT)))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", config.SENDER_EMAIL)
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", config.SENDER_PASSWORD)
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", config.RECEIVER_EMAIL)
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

def send_email():
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        logger.warning("SMTP email credentials are not fully configured. Email report skipped.")
        return

    rows = get_upcoming_week_appointments()
    
    if not rows:
        logger.info("No confirmed appointments for the upcoming week. Email not sent.")
        return

    table_rows = ""
    for row in rows:
        table_rows += f"<tr><td>{row['full_name']}</td><td>{row['date']}</td><td>{row['time']}</td><td>{row['session_type']}</td></tr>"

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
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "گزارش خودکار شبانه: نوبت‌های هفته آینده"
    msg.attach(MIMEText(html_report, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info("Nightly report successfully emailed.")
    except Exception as e:
        logger.error(f"Error sending email report: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    send_email()
