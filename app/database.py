"""SQLite persistence layer.

Uses Python's built-in :mod:`sqlite3` (no external DB dependency) so the tool
is trivial to run and test. The database path can be overridden with the
``TRIAGEBOT_DB`` environment variable, which the test-suite uses to point at a
throwaway file.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "triagebot.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS issues (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    body        TEXT    NOT NULL DEFAULT '',
    severity    TEXT    NOT NULL,
    labels      TEXT    NOT NULL DEFAULT '',   -- comma-separated
    owner       TEXT    NOT NULL,
    reason      TEXT    NOT NULL DEFAULT '',
    status      TEXT    NOT NULL DEFAULT 'open', -- open | closed
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def _db_path() -> str:
    return os.environ.get("TRIAGEBOT_DB", DEFAULT_DB_PATH)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with row access by column name."""
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not already exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
