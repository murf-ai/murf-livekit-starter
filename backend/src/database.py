"""
database.py — Persistent caller memory for BharatPay Pooja Voice Agent
Uses SQLite (stdlib) so there are zero extra dependencies.

Schema
------
callers
  user_id           TEXT  PRIMARY KEY   — phone / room participant SID or any stable ID
  name              TEXT                — caller's preferred name
  language_pref     TEXT                — "hi", "en", "hi-en" (Hinglish)
  schemes_checked   TEXT                — JSON list of government / BharatPay schemes discussed
  eligibility_notes TEXT                — JSON object with eligibility answers (NO account/ID numbers)
  last_interaction  TEXT                — ISO-8601 timestamp of last call
  consent_given     INTEGER             — 1 if user explicitly gave consent, 0 otherwise
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("agent.db")

# Store DB next to the src package, inside backend/
_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(_DB_DIR, exist_ok=True)
DB_PATH = os.path.join(_DB_DIR, "callers.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS callers (
                user_id           TEXT PRIMARY KEY,
                name              TEXT,
                language_pref     TEXT,
                schemes_checked   TEXT DEFAULT '[]',
                eligibility_notes TEXT DEFAULT '{}',
                last_interaction  TEXT,
                consent_given     INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()
    logger.info("Database initialised at %s", DB_PATH)


# ---------------------------------------------------------------------------
# Public API — called by agent function_tools
# ---------------------------------------------------------------------------

def lookup_caller(user_id: str) -> dict[str, Any] | None:
    """
    Return the stored record for *user_id*, or None if unknown.
    The returned dict mirrors the DB schema with JSON fields already decoded.
    """
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM callers WHERE user_id = ?", (user_id,)
        ).fetchone()

    if row is None:
        return None

    record = dict(row)
    record["schemes_checked"] = json.loads(record.get("schemes_checked") or "[]")
    record["eligibility_notes"] = json.loads(record.get("eligibility_notes") or "{}")
    logger.info("Found existing caller: %s (name=%s)", user_id, record.get("name"))
    return record


def save_caller(
    user_id: str,
    name: str | None = None,
    language_pref: str | None = None,
    schemes_checked: list[str] | None = None,
    eligibility_notes: dict[str, Any] | None = None,
    consent_given: bool = True,
) -> dict[str, Any]:
    """
    Upsert a caller record.  Only fields passed as non-None are updated.
    Returns the full updated record.
    """
    now = datetime.now(timezone.utc).isoformat()

    existing = lookup_caller(user_id)

    if existing:
        # Merge rather than overwrite lists/dicts
        merged_schemes = existing.get("schemes_checked") or []
        if schemes_checked:
            for s in schemes_checked:
                if s not in merged_schemes:
                    merged_schemes.append(s)

        merged_eligibility = existing.get("eligibility_notes") or {}
        if eligibility_notes:
            merged_eligibility.update(eligibility_notes)

        with _get_conn() as conn:
            conn.execute(
                """
                UPDATE callers
                SET name              = COALESCE(?, name),
                    language_pref     = COALESCE(?, language_pref),
                    schemes_checked   = ?,
                    eligibility_notes = ?,
                    last_interaction  = ?,
                    consent_given     = ?
                WHERE user_id = ?
                """,
                (
                    name,
                    language_pref,
                    json.dumps(merged_schemes),
                    json.dumps(merged_eligibility),
                    now,
                    1 if consent_given else 0,
                    user_id,
                ),
            )
            conn.commit()
    else:
        with _get_conn() as conn:
            conn.execute(
                """
                INSERT INTO callers
                    (user_id, name, language_pref, schemes_checked,
                     eligibility_notes, last_interaction, consent_given)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    language_pref,
                    json.dumps(schemes_checked or []),
                    json.dumps(eligibility_notes or {}),
                    now,
                    1 if consent_given else 0,
                ),
            )
            conn.commit()

    logger.info("Saved caller record: user_id=%s  name=%s", user_id, name)
    return lookup_caller(user_id)  # type: ignore[return-value]
