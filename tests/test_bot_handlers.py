import unittest
import os
import re
import inspect
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock, AsyncMock
from telegram import Update
from telegram.ext import CallbackQueryHandler

import main
import database
import config


class TestBotModularHandlers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        self.original_db = database.get_connection
        database.get_connection = lambda: sqlite3.connect(self.test_db_path)
        database.setup_database()

    def tearDown(self):
        database.get_connection = self.original_db
        try:
            os.close(self.test_db_fd)
        except OSError:
            pass
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_modular_handlers_exist_and_are_async(self):
        """All 9 required modular callback handlers must exist in main and be coroutine functions."""
        required_handlers = [
            'menu_callback',
            'emergency_contact_callback',
            'admin_panel_callback',
            'book_appointment_callback',
            'date_callback',
            'time_callback',
            'type_callback',
            'user_cancel_callback',
            'admin_review_callback',
        ]
        for handler_name in required_handlers:
            self.assertTrue(
                hasattr(main, handler_name),
                f"Handler '{handler_name}' must be defined in main.py"
            )
            handler_func = getattr(main, handler_name)
            self.assertTrue(
                inspect.iscoroutinefunction(handler_func),
                f"Handler '{handler_name}' must be an async coroutine function"
            )

    def test_main_registers_modular_callback_handlers(self):
        """main() must register modular CallbackQueryHandler instances with designated regex patterns."""
        with patch('database.setup_database'), \
             patch('telegram.ext.Application.builder') as mock_builder:
            mock_app = MagicMock()
            mock_builder.return_value.token.return_value.build.return_value = mock_app

            main.main()

            # Inspect add_handler calls
            callback_handlers = []
            for call in mock_app.add_handler.call_args_list:
                handler = call.args[0] if call.args else None
                if isinstance(handler, CallbackQueryHandler):
                    pattern = getattr(handler.pattern, 'pattern', str(handler.pattern)) if handler.pattern else None
                    callback_handlers.append((handler.callback, pattern))

            # Expected handlers and patterns
            expected_patterns = {
                r"^main_menu$": getattr(main, 'menu_callback', None),
                r"^emergency_contact$": getattr(main, 'emergency_contact_callback', None),
                r"^admin_panel$": getattr(main, 'admin_panel_callback', None),
                r"^book_appointment$": getattr(main, 'book_appointment_callback', None),
                r"^date_": getattr(main, 'date_callback', None),
                r"^time_": getattr(main, 'time_callback', None),
                r"^type_": getattr(main, 'type_callback', None),
                r"^user_cancel_\d+$": getattr(main, 'user_cancel_callback', None),
                r"^(approve|reject)_\d+$": getattr(main, 'admin_review_callback', None),
            }

            registered_map = {pat: cb for cb, pat in callback_handlers}
            for exp_pattern, exp_callback in expected_patterns.items():
                self.assertIn(
                    exp_pattern,
                    registered_map,
                    f"Pattern '{exp_pattern}' must be registered as CallbackQueryHandler in main()"
                )
                if exp_callback:
                    self.assertEqual(
                        registered_map[exp_pattern],
                        exp_callback,
                        f"Pattern '{exp_pattern}' must map to callback {exp_callback.__name__}"
                    )

    def test_regex_patterns_matching(self):
        """Verify the regex patterns accurately match expected callback query strings."""
        patterns = {
            r"^main_menu$": ("main_menu", ["main_menu_extra", "menu"]),
            r"^emergency_contact$": ("emergency_contact", ["emergency", "emergency_contact_2"]),
            r"^admin_panel$": ("admin_panel", ["admin_panel_view", "panel"]),
            r"^book_appointment$": ("book_appointment", ["book", "appointment"]),
            r"^date_": ("date_1405/01/15", ["my_date_1405"]),
            r"^time_": ("time_1405/01/15_16:00", ["my_time_16:00"]),
            r"^type_": ("type_حضوری", ["my_type_حضوری"]),
            r"^user_cancel_\d+$": ("user_cancel_42", ["user_cancel_abc", "user_cancel_"]),
            r"^(approve|reject)_\d+$": ("approve_123", ["hold_123", "approve_abc"]),
        }

        for pat_str, (valid_sample, invalid_samples) in patterns.items():
            compiled = re.compile(pat_str)
            self.assertTrue(
                bool(compiled.match(valid_sample)),
                f"Pattern {pat_str} should match valid sample '{valid_sample}'"
            )
            for inv in invalid_samples:
                self.assertFalse(
                    bool(compiled.match(inv)),
                    f"Pattern {pat_str} should NOT match invalid sample '{inv}'"
                )

    async def test_button_handler_delegation_to_modular_handlers(self):
        """button_handler must act as a backward-compatible router delegating to modular handlers."""
        delegation_tests = [
            ("main_menu", "menu_callback"),
            ("emergency_contact", "emergency_contact_callback"),
            ("admin_panel", "admin_panel_callback"),
            ("book_appointment", "book_appointment_callback"),
            ("date_1405/01/15", "date_callback"),
            ("time_1405/01/15_16:00", "time_callback"),
            ("type_حضوری", "type_callback"),
            ("user_cancel_99", "user_cancel_callback"),
            ("approve_99", "admin_review_callback"),
            ("reject_99", "admin_review_callback"),
        ]

        for callback_data, handler_name in delegation_tests:
            if not hasattr(main, handler_name):
                self.fail(f"Handler '{handler_name}' is not yet implemented in main.py")

            with patch.object(main, handler_name, new_callable=AsyncMock) as mock_handler:
                update = MagicMock()
                query = MagicMock()
                query.data = callback_data
                query.answer = AsyncMock()
                update.callback_query = query
                update.effective_user.id = main.MAIN_ADMIN_ID

                context = MagicMock()
                context.user_data = {}

                await main.button_handler(update, context)
                mock_handler.assert_awaited_once_with(update, context)

    async def test_menu_callback_behavior(self):
        """menu_callback clears user_data and edits message with main menu keyboard."""
        update = MagicMock()
        query = MagicMock()
        query.data = "main_menu"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        user_id = 12345
        update.effective_user.id = user_id

        context = MagicMock()
        context.user_data = {'selected_date': '1405/01/15', 'state': 'awaiting_name'}

        await main.menu_callback(update, context)

        self.assertEqual(len(context.user_data), 0, "user_data must be cleared upon returning to main menu")
        query.answer.assert_awaited_once()
        query.edit_message_text.assert_awaited_once()
        call_args = query.edit_message_text.call_args[0]
        self.assertIn("منوی اصلی", call_args[0])

    async def test_emergency_contact_callback_behavior(self):
        """emergency_contact_callback renders contact numbers and support telegram link."""
        update = MagicMock()
        query = MagicMock()
        query.data = "emergency_contact"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 12345

        context = MagicMock()
        context.user_data = {}

        await main.emergency_contact_callback(update, context)

        query.answer.assert_awaited_once()
        query.edit_message_text.assert_awaited_once()
        call_args = query.edit_message_text.call_args[0]
        self.assertIn("ارتباط با پذیرش", call_args[0])
        self.assertIn(main.ADMIN_PHONE, call_args[0])

    async def test_admin_panel_callback_non_admin_blocked(self):
        """admin_panel_callback blocks non-admin users with an alert."""
        update = MagicMock()
        query = MagicMock()
        query.data = "admin_panel"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 99999999  # non-admin

        context = MagicMock()
        context.user_data = {}

        await main.admin_panel_callback(update, context)

        query.answer.assert_awaited_with("⛔ شما دسترسی مدیریت به این عملیات را ندارید.", show_alert=True)
        query.edit_message_text.assert_not_called()

    async def test_book_appointment_callback_behavior(self):
        """book_appointment_callback presents upcoming available days."""
        update = MagicMock()
        query = MagicMock()
        query.data = "book_appointment"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 12345

        context = MagicMock()
        context.user_data = {}

        await main.book_appointment_callback(update, context)

        query.answer.assert_awaited_once()
        query.edit_message_text.assert_awaited_once()
        call_args = query.edit_message_text.call_args[0]
        self.assertIn("گام اول: انتخاب تاریخ مشاوره", call_args[0])

    async def test_type_callback_behavior(self):
        """type_callback sets session_type and transitions state to awaiting_name."""
        update = MagicMock()
        query = MagicMock()
        query.data = "type_حضوری"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.effective_user.id = 12345

        context = MagicMock()
        context.user_data = {'selected_date': '1405/01/15', 'selected_time': '17:00'}

        await main.type_callback(update, context)

        query.answer.assert_awaited_once()
        self.assertEqual(context.user_data.get('session_type'), 'حضوری')
        self.assertEqual(context.user_data.get('state'), 'awaiting_name')
        query.edit_message_text.assert_awaited_once()
        call_args = query.edit_message_text.call_args[0]
        self.assertIn("گام چهارم: مشخصات مراجع ارجمند", call_args[0])


if __name__ == '__main__':
    unittest.main()
