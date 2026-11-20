import unittest
import os
import datetime
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from flask import template_rendered
import config
import app as flask_app
import database


@contextmanager
def captured_templates(app_instance):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app_instance)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app_instance)


class TestWebRoutes(unittest.TestCase):
    def setUp(self):
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        self.original_db = database.get_connection
        database.get_connection = lambda: sqlite3.connect(self.test_db_path)
        database.setup_database()

        flask_app.app.config['TESTING'] = True
        flask_app.app.config['WTF_CSRF_ENABLED'] = False
        self.client = flask_app.app.test_client()

    def tearDown(self):
        database.get_connection = self.original_db
        try:
            os.close(self.test_db_fd)
        except OSError:
            pass
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_home_route_renders_index_html(self):
        """GET / must return HTTP 200 and render index.html, NOT about.html."""
        with captured_templates(flask_app.app) as templates:
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            rendered_template, _ = templates[0]
            self.assertEqual(rendered_template.name, 'index.html')
            
            # Content checks
            html = response.data.decode('utf-8')
            self.assertIn("همراه شما در مسیر آرامش", html)
            self.assertNotIn("درباره کلینیک دکتر شفائی", html)

    def test_about_route_renders_about_html(self):
        """GET /about must return HTTP 200 and render about.html."""
        with captured_templates(flask_app.app) as templates:
            response = self.client.get('/about')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            rendered_template, _ = templates[0]
            self.assertEqual(rendered_template.name, 'about.html')

            # Content checks
            html = response.data.decode('utf-8')
            self.assertIn("درباره کلینیک دکتر شفائی", html)
            self.assertNotIn("همراه شما در مسیر آرامش", html)

    def test_booking_route_renders_booking_html(self):
        """GET /booking must return HTTP 200 and render booking.html."""
        with captured_templates(flask_app.app) as templates:
            response = self.client.get('/booking')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            rendered_template, context = templates[0]
            self.assertEqual(rendered_template.name, 'booking.html')
            self.assertIn('days', context)
            self.assertEqual(context.get('card_number'), '5894-6318-0470-9814')

            html = response.data.decode('utf-8')
            self.assertIn("فرم رزرو آنلاین نوبت", html)
            self.assertIn("5894-6318-0470-9814", html)

    def test_reserve_alias_route_renders_booking_html(self):
        """GET /reserve must act as an alias to booking and return HTTP 200 rendering booking.html."""
        with captured_templates(flask_app.app) as templates:
            response = self.client.get('/reserve')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(templates), 1)
            rendered_template, _ = templates[0]
            self.assertEqual(rendered_template.name, 'booking.html')

    def test_articles_route(self):
        """GET /articles returns HTTP 200."""
        response = self.client.get('/articles')
        self.assertEqual(response.status_code, 200)

    def test_available_times_api_endpoints(self):
        """GET /get_times/<date> and /api/available-times/<date> return available times list."""
        valid_date = "1405/01/15"
        res1 = self.client.get(f'/get_times/{valid_date}')
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertIn("available_times", data1)
        self.assertIsInstance(data1["available_times"], list)
        self.assertIn("21:00", data1["available_times"])

        res2 = self.client.get(f'/api/available-times/{valid_date}')
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertIn("available_times", data2)
        self.assertEqual(data1["available_times"], data2["available_times"])

    def test_url_for_all_endpoints(self):
        """Verify url_for resolves home, about, articles, reserve, and booking without BuildError."""
        with flask_app.app.test_request_context():
            from flask import url_for
            self.assertEqual(url_for('home'), '/')
            self.assertEqual(url_for('about'), '/about')
            self.assertEqual(url_for('articles'), '/articles')
            self.assertIn(url_for('booking'), ['/booking', '/reserve'])
            self.assertIn(url_for('reserve'), ['/reserve', '/booking'])

    def test_security_headers_and_cookie_settings(self):
        """Verify HTTP security headers and session cookie protection flags."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')
        self.assertIn("default-src", response.headers.get('Content-Security-Policy', ''))
        self.assertTrue(flask_app.app.config.get('SESSION_COOKIE_HTTPONLY'))
        self.assertEqual(flask_app.app.config.get('SESSION_COOKIE_SAMESITE'), 'Lax')

    def test_booking_rate_limiter_logic(self):
        """Verify thread-safe sliding window rate limiter blocks requests exceeding limit."""
        ip = "192.168.1.100"
        flask_app._booking_rate_limit_records[ip] = []
        for _ in range(5):
            self.assertFalse(flask_app.is_booking_rate_limited(ip, max_requests=5, window_seconds=60))
        # 6th request should be rate-limited
        self.assertTrue(flask_app.is_booking_rate_limited(ip, max_requests=5, window_seconds=60))

    def test_admin_login_flow_and_dashboard_protection(self):
        """Admin dashboard must require login, and valid credentials grant access."""
        # Unauthenticated access to /admin redirects to login
        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

        # GET /login renders login form
        res_login_page = self.client.get('/login')
        self.assertEqual(res_login_page.status_code, 200)
        self.assertIn("ورود به پنل مدیریت", res_login_page.data.decode('utf-8'))

        # Invalid password returns 401
        res_bad_pw = self.client.post('/login', data={'password': 'wrong_password'})
        self.assertEqual(res_bad_pw.status_code, 401)

        # Valid password logs in and redirects to /admin
        admin_pw = getattr(flask_app.config, 'ADMIN_PASSWORD', 'admin123')
        res_login = self.client.post('/login', data={'password': admin_pw})
        self.assertEqual(res_login.status_code, 302)
        self.assertIn('/admin', res_login.headers.get('Location', ''))

        # Authenticated access to /admin succeeds
        res_dash = self.client.get('/admin')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn("پنل مدیریت کلینیک دکتر شفائی", res_dash.data.decode('utf-8'))

        # Logout clears session
        res_logout = self.client.get('/logout')
        self.assertEqual(res_logout.status_code, 302)
        res_dash_after = self.client.get('/admin')
        self.assertEqual(res_dash_after.status_code, 302)

    def test_admin_approve_and_reject_workflow(self):
        """Admin can approve and reject pending appointments from the dashboard."""
        # Insert a pending appointment
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (0, '1405/01/20', '18:00', 'حضوری', 'کاربر وب | 09121112233', 'pending', 'fake_receipt.jpg')
        ''')
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Log in as admin
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        # Check pending is in dashboard
        res_dash = self.client.get('/admin')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(f"#{app_id}", res_dash.data.decode('utf-8'))

        # Approve appointment
        res_approve = self.client.post(f'/admin/approve/{app_id}')
        self.assertEqual(res_approve.status_code, 302)
        app_info = database.get_appointment(app_id)
        self.assertEqual(app_info[5], 'confirmed')

        # Insert second pending appointment and reject it
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (0, '1405/01/21', '19:00', 'آنلاین', 'کاربر دیگر | 09123334455', 'pending', 'fake_receipt2.jpg')
        ''')
        app_id_2 = cursor.lastrowid
        conn.commit()
        conn.close()

        res_reject = self.client.post(f'/admin/reject/{app_id_2}')
        self.assertEqual(res_reject.status_code, 302)
        app_info_2 = database.get_appointment(app_id_2, include_cancelled=True)
        self.assertEqual(app_info_2[5], 'rejected')

    def test_booking_ajax_flow(self):
        """AJAX POST /booking returns JSON with success and appointment_id."""
        import io
        from PIL import Image

        # 1. Invalid input returns JSON 400
        res_bad = self.client.post(
            '/booking',
            data={'phone': 'invalid_num', 'is_ajax': '1'},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(res_bad.status_code, 400)
        data_bad = res_bad.get_json()
        self.assertFalse(data_bad['success'])
        self.assertIn('error', data_bad)

        # 2. Valid booking returns JSON 200
        bio = io.BytesIO()
        img = Image.new('RGB', (60, 60), color='green')
        img.save(bio, format='JPEG')
        bio.seek(0)

        upcoming_days = flask_app.config.get_upcoming_working_days(5, is_admin=False)
        target_date = upcoming_days[2]

        with patch.object(flask_app, 'send_receipt_to_telegram'):
            res_good = self.client.post(
                '/booking',
                data={
                    'full_name': 'سروش رضایی',
                    'phone': '09121234567',
                    'session_type': 'حضوری',
                    'date': target_date,
                    'time': '17:00',
                    'receipt': (bio, 'receipt.jpg'),
                    'is_ajax': '1'
                },
                headers={'X-Requested-With': 'XMLHttpRequest'}
            )
            self.assertEqual(res_good.status_code, 200)
            data_good = res_good.get_json()
            self.assertTrue(data_good['success'])
            self.assertIn('appointment_id', data_good)
            self.assertEqual(data_good['time'], '17:00')

    def test_admin_dashboard_past_and_future_appointments_view_and_cancel_restrictions(self):
        """Admin dashboard hides cancel button for past sessions and prevents their deletion."""
        # Insert one past confirmed appointment and one future confirmed appointment
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (10, '1405/01/01', '16:00', 'حضوری', 'کاربر قدیمی | 09121111111', 'confirmed', 'r_past.jpg')
        ''')
        past_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (11, '1405/12/25', '18:00', 'آنلاین', 'کاربر آینده | 09122222222', 'confirmed', 'r_future.jpg')
        ''')
        future_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Log in as admin
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        # View dashboard
        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Both appointments must be displayed in confirmed list
        self.assertIn(f"#{past_id}", html)
        self.assertIn(f"#{future_id}", html)
        self.assertIn("کاربر قدیمی", html)
        self.assertIn("کاربر آینده", html)

        # Past appointment must show 'برگزارشده' badge and NO cancel button form
        self.assertIn("برگزارشده", html)
        self.assertNotIn(f'action="/admin/cancel/{past_id}"', html)

        # Future appointment must show cancel button form
        self.assertIn(f'action="/admin/cancel/{future_id}"', html)

        # Attempt to cancel past appointment directly via POST -> Rejected, stays in DB
        res_cancel_past = self.client.post(f'/admin/cancel/{past_id}', follow_redirects=True)
        self.assertEqual(res_cancel_past.status_code, 200)
        past_app_db = database.get_appointment(past_id)
        self.assertIsNotNone(past_app_db)
        self.assertEqual(past_app_db[5], 'confirmed')
        self.assertIn("امکان لغو نوبت‌های برگزارشده", res_cancel_past.data.decode('utf-8'))

        # Cancel future appointment -> Allowed, deleted from DB
        res_cancel_future = self.client.post(f'/admin/cancel/{future_id}', follow_redirects=True)
        self.assertEqual(res_cancel_future.status_code, 200)
        future_app_db = database.get_appointment(future_id)
        self.assertIsNone(future_app_db)

    def test_get_available_hours_delegates_to_database_and_expires_stale(self):
        """get_available_hours delegates to database.get_available_times and expires stale pending slots."""
        from app import get_available_hours

        date = "1405/01/25"
        time = "16:00"

        # Insert a stale pending appointment created 3 hours ago
        three_hours_ago = (datetime.datetime.now(config.TEHRAN_TZ) - datetime.timedelta(hours=3)).isoformat()
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id, created_at, updated_at)
            VALUES (101, ?, ?, 'حضوری', 'کاربر معلق', 'pending', 'stale.jpg', ?, ?)
        ''', (date, time, three_hours_ago, three_hours_ago))
        conn.commit()
        conn.close()

        # get_available_hours should auto-expire the stale appointment and include the slot
        avail = get_available_hours(date)
        self.assertIn(time, avail)

    def test_admin_dashboard_receipt_badge_for_telegram_and_web(self):
        """Admin dashboard shows 'مشاهده فیش' link for web and 'فیش در تلگرام' badge for Telegram bookings."""
        conn = database.get_connection()
        cursor = conn.cursor()
        # 1. Web booking (user_id=0)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (0, '1405/01/26', '17:00', 'حضوری', 'کاربر وب | 09121112233', 'pending', 'private_uploads/receipt_web.jpg')
        ''')
        web_app_id = cursor.lastrowid

        # 2. Telegram booking (user_id=987654)
        cursor.execute('''
            INSERT INTO appointments (user_id, date, time, session_type, full_name, status, receipt_file_id)
            VALUES (987654, '1405/01/26', '18:00', 'آنلاین', 'کاربر تلگرام', 'pending', 'AgACAgIAAxkBAA...')
        ''')
        tg_app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Web booking has view receipt link
        self.assertIn(f'/admin/receipt/{web_app_id}', html)
        self.assertIn('مشاهده فیش', html)

        # Telegram booking has 'فیش در تلگرام' badge and NOT the /admin/receipt link
        self.assertIn('فیش در تلگرام', html)
        self.assertNotIn(f'/admin/receipt/{tg_app_id}', html)


if __name__ == '__main__':
    unittest.main()
