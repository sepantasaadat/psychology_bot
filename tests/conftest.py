import os
import sys
import gc
import sqlite3
import pytest
from unittest.mock import AsyncMock, MagicMock

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import database


class IsolatedDb(str):
    """
    Wrapper for isolated test database path, providing convenient
    connection and cursor helper methods.
    """
    @property
    def path(self) -> str:
        return str(self)

    def get_connection(self) -> sqlite3.Connection:
        return database.get_connection(str(self))

    def connect(self) -> sqlite3.Connection:
        return database.get_connection(str(self))

    def cursor(self) -> sqlite3.Cursor:
        conn = database.get_connection(str(self))
        return conn.cursor()


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """
    Configures a unique database file in tmp_path / 'clinic_test.db'.
    Patches database.DB_PATH and monkeypatches database.get_connection.
    Calls database.setup_database().
    Yields the database path/connection wrapper.
    Ensures clean cleanup.
    """
    test_db_file = tmp_path / "clinic_test.db"
    test_db_path = str(test_db_file)

    # Patch database DB_PATH
    monkeypatch.setattr(database, "DB_PATH", test_db_path)

    # Monkeypatch database.get_connection to always target test_db_path when called without args
    original_get_connection = database.get_connection

    def test_get_connection(db_path=None):
        target = db_path if db_path is not None else test_db_path
        return original_get_connection(target)

    monkeypatch.setattr(database, "get_connection", test_get_connection)

    # If app module is loaded, patch module-level DATABASE
    if "app" in sys.modules:
        monkeypatch.setattr(sys.modules["app"], "DATABASE", test_db_path)

    # Setup tables and indices
    database.setup_database(test_db_path)

    # Ensure default web user (user_id=0) exists for appointments foreign key
    with database.get_connection(test_db_path) as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
                     (0, "کاربر سایت", "Website_Booking"))
        conn.commit()

    wrapped_db = IsolatedDb(test_db_path)
    yield wrapped_db

    # Clean cleanup
    gc.collect()


@pytest.fixture
def flask_client(isolated_db, monkeypatch):
    """
    Imports from app import app, sets app.config['TESTING'] = True
    and app.config['WTF_CSRF_ENABLED'] = False, and returns app.test_client().
    """
    from app import app
    monkeypatch.setattr("app.DATABASE", str(isolated_db))
    monkeypatch.setattr("app.send_receipt_to_telegram", MagicMock())
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_telegram_bot():
    """
    Provides a MagicMock / AsyncMock simulating Telegram Bot and ContextTypes.DEFAULT_TYPE.
    """
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=12345))
    bot.send_photo = AsyncMock(return_value=MagicMock(message_id=12346))
    bot.edit_message_text = AsyncMock()
    bot.edit_message_reply_markup = AsyncMock()
    bot.delete_message = AsyncMock()
    bot.answer_callback_query = AsyncMock()

    context = MagicMock()
    context.bot = bot
    context.user_data = {}
    context.chat_data = {}
    context.bot_data = {}
    context.job_queue = MagicMock()

    bot.context = context
    return bot


@pytest.fixture
def mock_telegram_context(mock_telegram_bot):
    """Convenience fixture returning the mocked context object."""
    return mock_telegram_bot.context
