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


if __name__ == '__main__':
    unittest.main()
