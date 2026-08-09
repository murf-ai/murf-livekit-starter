import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_FILE = Path(__file__).resolve().parents[1] / "caller_memory.db"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
        """
    )
    conn.commit()
    return conn


def _load_facts(facts_text: str | None) -> dict[str, str]:
    if not facts_text:
        return {}
    try:
        return json.loads(facts_text)
    except json.JSONDecodeError:
        return {}


def _serialize_facts(facts: dict[str, str] | None) -> str:
    return json.dumps(facts or {})


def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": _load_facts(row["facts"]),
        "last_interaction": row["last_interaction"],
    }


def lookup_caller(conn: sqlite3.Connection, user_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_record(row)


def save_caller(
    conn: sqlite3.Connection,
    user_id: str,
    name: str | None = None,
    language_preference: str | None = None,
    facts: dict[str, str] | None = None,
    last_interaction: str | None = None,
) -> dict[str, Any]:
    existing = lookup_caller(conn, user_id)
    if existing is None:
        existing = {
            "user_id": user_id,
            "name": name or "",
            "language_preference": language_preference or "",
            "facts": {},
            "last_interaction": last_interaction or _now_iso(),
        }
    else:
        if name:
            existing["name"] = name
        if language_preference:
            existing["language_preference"] = language_preference
        if facts:
            existing["facts"] = {**existing["facts"], **facts}
        existing["last_interaction"] = last_interaction or _now_iso()

    conn.execute(
        "REPLACE INTO callers (user_id, name, language_preference, facts, last_interaction) VALUES (?, ?, ?, ?, ?)",
        (
            existing["user_id"],
            existing["name"],
            existing["language_preference"],
            _serialize_facts(existing["facts"]),
            existing["last_interaction"],
        ),
    )
    conn.commit()
    return existing
