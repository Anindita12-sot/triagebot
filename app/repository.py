"""Data-access functions for issues.

Thin wrappers around SQL so the route handlers stay small and the queries live
in one place. Labels are stored comma-separated and exposed as a list.
"""

from __future__ import annotations

import sqlite3

from app.database import get_connection


def _labels_to_str(labels: list[str]) -> str:
    return ",".join(labels)


def _row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    raw = data.get("labels") or ""
    data["labels"] = [label for label in raw.split(",") if label]
    return data


def create_issue(
    title: str, body: str, severity: str, labels: list[str], owner: str, reason: str
) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO issues (title, body, severity, labels, owner, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, body, severity, _labels_to_str(labels), owner, reason),
        )
        issue_id = cursor.lastrowid
    return get_issue(issue_id)  # type: ignore[return-value]


def list_issues() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM issues ORDER BY id DESC").fetchall()
    return [_row_to_dict(row) for row in rows]


def get_issue(issue_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    return _row_to_dict(row) if row else None


def update_issue(
    issue_id: int,
    *,
    title: str | None = None,
    body: str | None = None,
    severity: str | None = None,
    labels: list[str] | None = None,
    owner: str | None = None,
    reason: str | None = None,
    status: str | None = None,
) -> dict | None:
    fields: dict[str, object] = {}
    if title is not None:
        fields["title"] = title
    if body is not None:
        fields["body"] = body
    if severity is not None:
        fields["severity"] = severity
    if labels is not None:
        fields["labels"] = _labels_to_str(labels)
    if owner is not None:
        fields["owner"] = owner
    if reason is not None:
        fields["reason"] = reason
    if status is not None:
        fields["status"] = status

    if not fields:
        return get_issue(issue_id)

    assignments = ", ".join(f"{name} = ?" for name in fields)
    values = list(fields.values()) + [issue_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE issues SET {assignments} WHERE id = ?", values)
    return get_issue(issue_id)


def delete_issue(issue_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
        deleted = cursor.rowcount > 0
    return deleted
