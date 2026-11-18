"""Database persistence layer for Onboarding assistant using SQLite.

Manages schema initialization, audit logging, user progress tracking, and question logs.
"""

from __future__ import annotations

import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH_DEFAULT = Path(__file__).resolve().parent.parent / "data" / "onboarding.db"


def get_db_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Return an open SQLite connection with Row factory and WAL mode enabled."""
    target_path = Path(db_path) if db_path else DB_PATH_DEFAULT
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    """Initialize database tables if they do not already exist."""
    with get_db_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ordinal INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                handbook_ref TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL,
                start_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_progress (
                user_id TEXT NOT NULL,
                task_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'done')),
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, task_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS question_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answered_from TEXT NOT NULL CHECK(answered_from IN ('handbook', 'live', 'none')),
                resolved INTEGER NOT NULL CHECK(resolved IN (0, 1)),
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                tool TEXT NOT NULL,
                args_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                bytes_returned INTEGER NOT NULL,
                redactions INTEGER NOT NULL
            );
            """
        )
        conn.commit()


def record_audit(
    tool: str,
    args_sha256: str,
    status: str,
    bytes_returned: int,
    redactions: int,
    db_path: Path | str | None = None,
) -> None:
    """Record an entry in the audit_log table.

    Never logs actual argument payloads or return values, ensuring strict data governance.
    """
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with get_db_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_log (ts, tool, args_sha256, status, bytes_returned, redactions)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ts, tool, args_sha256, status, bytes_returned, redactions),
            )
            conn.commit()
    except Exception as exc:
        # Never crash the application on audit logging failure; log to stderr
        import sys
        print(f"ERROR: Failed to record audit log: {type(exc).__name__}: {exc}", file=sys.stderr)

