import hashlib
import os
import sqlite3
from datetime import datetime

from flask import current_app


def _db_dir():
    path = current_app.config.get("PRIVATE_KEY_DB_DIR", "private_key_dbs")
    os.makedirs(path, exist_ok=True)
    return path


def _user_db_path(username: str):
    digest = hashlib.sha256(username.encode("utf-8")).hexdigest()
    return os.path.join(_db_dir(), f"user_{digest}.db")


def _ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS private_keys (
            username TEXT PRIMARY KEY,
            private_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def save_private_key(username: str, private_key: str):
    if not username:
        raise ValueError("username required")
    if not private_key:
        raise ValueError("private_key required")

    now = datetime.utcnow().isoformat()
    db_path = _user_db_path(username)
    with sqlite3.connect(db_path) as conn:
        _ensure_schema(conn)
        existing = conn.execute(
            "SELECT created_at FROM private_keys WHERE username = ?",
            (username,),
        ).fetchone()
        created_at = existing[0] if existing else now
        conn.execute(
            """
            INSERT OR REPLACE INTO private_keys (username, private_key, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, private_key, created_at, now),
        )
        conn.commit()


def get_private_key(username: str):
    if not username:
        raise ValueError("username required")

    db_path = _user_db_path(username)
    if not os.path.exists(db_path):
        raise LookupError("private key database not found")

    with sqlite3.connect(db_path) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT private_key FROM private_keys WHERE username = ?",
            (username,),
        ).fetchone()
    if not row:
        raise LookupError("private key not found")
    return row[0]
