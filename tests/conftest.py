"""Shared pytest fixtures.

Points TriageBot at a throwaway SQLite file per test session so the real
``triagebot.db`` is never touched, and provides a FastAPI ``TestClient``.
"""

from __future__ import annotations

import importlib
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    """A TestClient backed by an isolated temporary database."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("TRIAGEBOT_DB", str(db_file))

    # Re-import modules so they pick up the patched DB path cleanly.
    import app.database as database
    import app.main as main

    importlib.reload(database)
    importlib.reload(main)

    with TestClient(main.app) as test_client:
        yield test_client

    if os.path.exists(db_file):
        os.remove(db_file)
