import io
import logging
import os
import re
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sqlite3

class TestSecuritySecretsAndPII(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_stream = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.log_handler.setLevel(logging.DEBUG)
        
        # Attach to root and module loggers
        self.loggers_to_capture = [
            logging.getLogger(),
            logging.getLogger("main"),
            logging.getLogger("app"),
            logging.getLogger("database"),
            logging.getLogger("daily_report"),
            logging.getLogger("config"),
        ]
        for l in self.loggers_to_capture:
            l.addHandler(self.log_handler)

    def tearDown(self):
        for l in self.loggers_to_capture:
            l.removeHandler(self.log_handler)

    def test_no_hardcoded_secrets_in_source(self):
        target_files = ["daily_report.py", "app.py", "main.py", "config.py"]
        banned_patterns = [
            r"kjwr\s+kvkz\s+sppu\s+fysh",
            r"super_secret_psychology_key",
        ]
        
        for fname in target_files:
            fpath = os.path.join(self.base_dir, fname)
            self.assertTrue(os.path.exists(fpath), f"{fname} must exist")
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                for pattern in banned_patterns:
                    self.assertIsNone(
                        re.search(pattern, content, re.IGNORECASE),
                        f"Found hardcoded banned pattern '{pattern}' in {fname}!"
                    )

    def test_env_example_contains_all_required_keys(self):
        env_example_path = os.path.join(self.base_dir, ".env.example")
        self.assertTrue(os.path.exists(env_example_path), ".env.example must exist in project root")
        
        with open(env_example_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_keys = [
            "BOT_TOKEN",
            "FLASK_SECRET_KEY",
            "ADMIN_IDS",
            "ADMIN_USERNAME",
            "ADMIN_PHONE",
            "CLINIC_WEBSITE",
            "SMTP_SERVER",
            "SMTP_PORT",
            "SENDER_EMAIL",
            "SENDER_PASSWORD",
            "RECEIVER_EMAIL",
        ]
        
        for key in required_keys:
            self.assertIn(key, content, f"Key '{key}' is missing in .env.example")
            
        # Ensure example file does not expose live secrets
        self.assertNotIn("kjwr kvkz sppu fysh", content)
        self.assertNotIn("super_secret_psychology_key", content)

    def test_gitignore_protects_secrets_and_data(self):
        gitignore_path = os.path.join(self.base_dir, ".gitignore")
        self.assertTrue(os.path.exists(gitignore_path), ".gitignore must exist")
        
        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

        required_patterns = [
            ".env",
            ".env.*",
            "clinic.db*",
            "private_uploads/",
            "static/uploads/",
            "*.log",
            "__pycache__/",
        ]
        
        for pattern in required_patterns:
            self.assertIn(
                pattern,
                lines,
                f"Pattern '{pattern}' should be explicitly listed in .gitignore"
            )

    async def test_pii_not_in_logs(self):
        import main
        import database

        patient_name = "علی رضایی"
        patient_phone = "09123456789"

        # Ensure main.logger sends logs to our handler
        main.logger.addHandler(self.log_handler)
        main.logger.setLevel(logging.INFO)

        # 1. Simulate user sending text message in awaiting_name state
        update_name = MagicMock()
        update_name.effective_user.id = 123456789
        update_name.effective_user.first_name = "Ali"
        update_name.effective_user.username = "alireza"
        update_name.message.message_id = 4001
        update_name.message.text = patient_name
        update_name.message.reply_text = AsyncMock()

        context_name = MagicMock()
        context_name.user_data = {
            'state': 'awaiting_name',
            'selected_date': '1405/01/10',
            'selected_time': '17:00',
            'session_type': 'حضوری',
        }

        await main.handle_text(update_name, context_name)

        # 2. Simulate user sending text message outside booking containing name & phone
        update_outside = MagicMock()
        update_outside.effective_user.id = 123456789
        update_outside.effective_user.first_name = "Ali"
        update_outside.effective_user.username = "alireza"
        update_outside.message.message_id = 4002
        update_outside.message.text = f"سلام، من {patient_name} هستم و تلفن من {patient_phone} است"
        update_outside.message.reply_text = AsyncMock()

        context_outside = MagicMock()
        context_outside.user_data = {}

        await main.handle_text(update_outside, context_outside)

        # 3. Simulate button callback
        query_update = MagicMock()
        query_update.callback_query.data = "main_menu"
        query_update.callback_query.answer = AsyncMock()
        query_update.callback_query.edit_message_text = AsyncMock()
        query_update.callback_query.message.message_id = 4003
        query_update.effective_user.id = 123456789
        query_update.effective_user.username = "alireza"

        await main.button_handler(query_update, context_outside)

        # Inspect all captured logs
        captured_logs = self.log_stream.getvalue()
        
        # Verify that logs WERE captured (not an empty string test)
        self.assertTrue(len(captured_logs) > 0, "Log stream should have captured log events")
        
        self.assertNotIn(
            patient_name,
            captured_logs,
            f"PII Leak: Patient name '{patient_name}' was found in the logs:\n{captured_logs}"
        )
        self.assertNotIn(
            patient_phone,
            captured_logs,
            f"PII Leak: Patient phone '{patient_phone}' was found in the logs:\n{captured_logs}"
        )

    def test_external_loggers_suppressed(self):
        import main
        httpx_level = logging.getLogger("httpx").level
        telegram_level = logging.getLogger("telegram").level
        werkzeug_level = logging.getLogger("werkzeug").level

        self.assertGreaterEqual(httpx_level, logging.WARNING)
        self.assertGreaterEqual(telegram_level, logging.WARNING)
        self.assertGreaterEqual(werkzeug_level, logging.WARNING)

if __name__ == "__main__":
    unittest.main()
