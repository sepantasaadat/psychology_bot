import unittest
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from flask import template_rendered
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
            self.assertNotIn("درباره کلینیک دکتر شفایی", html)

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
            self.assertIn("درباره کلینیک دکتر شفایی", html)
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

            html = response.data.decode('utf-8')
            self.assertIn("فرم رزرو آنلاین نوبت", html)

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


if __name__ == '__main__':
    unittest.main()
