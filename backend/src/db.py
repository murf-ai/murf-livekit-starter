"""SQLite database module for persistent caller memory and facts."""

import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("agent.db")

# Default DB location in backend root directory
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "caller_memory.db"

# Sensitive financial & identity keys that must NEVER be saved
FORBIDDEN_KEYS_RE = re.compile(
    r"(account|acc_num|bank_acc|aadhaar|adhar|pan|pin|otp|cvv|card|id_num|secret|password)",
    re.IGNORECASE,
)

# Patterns matching sensitive account/ID number formats
SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"\b[2-9]\d{11}\b"),  # 12-digit Aadhaar pattern
    re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),  # 10-digit PAN pattern
    re.compile(r"\b\d{9,18}\b"),  # 9-18 digit account/card number pattern
    re.compile(r"\b\d{4,6}\b"),  # 4-6 digit PIN/OTP pattern in numeric fields
]


def get_db_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open or return a sqlite3 connection."""
    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    """Initialize SQLite database table for caller memory."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS callers (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                language_preference TEXT,
                facts TEXT,
                consent_given INTEGER DEFAULT 0,
                last_interaction TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.commit()
    logger.info("Caller memory database initialized.")


def sanitize_facts(facts: dict | None) -> dict:
    """Sanitize facts dict by filtering out sensitive account or ID numbers.

    Hard Rule for Financial Services:
    Do not store account or ID numbers (Aadhaar, PAN, PIN, OTP, Account No).
    """
    if not facts:
        return {}

    sanitized = {}
    for key, value in facts.items():
        key_str = str(key)
        # Check key name against sensitive key terms
        if FORBIDDEN_KEYS_RE.search(key_str):
            logger.warning("Stripped forbidden sensitive key: %s", key_str)
            continue

        val_str = str(value).strip()

        # Check value against sensitive number patterns if purely numeric/alphanumeric code
        is_sensitive = False
        for pattern in SENSITIVE_VALUE_PATTERNS:
            if pattern.search(val_str) and (
                "account" in key_str.lower()
                or "card" in key_str.lower()
                or "pin" in key_str.lower()
                or "otp" in key_str.lower()
                or "number" in key_str.lower()
                or val_str.isdigit()
            ):
                is_sensitive = True
                break

        if is_sensitive:
            logger.warning(
                "Stripped sensitive value for key %s matching ID pattern", key_str
            )
            continue

        sanitized[key_str] = value

    return sanitized


def get_caller(identifier: str, db_path: Path | str | None = None) -> dict | None:
    """Retrieve a caller's memory record by user_id or name (case-insensitive)."""
    if not identifier:
        return None

    init_db(db_path)
    clean_id = identifier.strip()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, language_preference, facts, consent_given, last_interaction, created_at, updated_at
            FROM callers
            WHERE LOWER(user_id) = LOWER(?) OR LOWER(name) = LOWER(?)
            """,
            (clean_id, clean_id),
        )
        row = cursor.fetchone()
        if not row:
            return None

        facts_dict = {}
        if row["facts"]:
            try:
                facts_dict = json.loads(row["facts"])
            except json.JSONDecodeError:
                facts_dict = {}

        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "language_preference": row["language_preference"],
            "facts": facts_dict,
            "consent_given": bool(row["consent_given"]),
            "last_interaction": row["last_interaction"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def save_caller(
    user_id: str,
    name: str | None = None,
    language_preference: str | None = None,
    facts: dict | None = None,
    consent_given: bool = False,
    db_path: Path | str | None = None,
) -> dict:
    """Save or update caller memory.

    Hard Rule:
    If consent_given is False, no data will be saved to the database.
    """
    if not user_id:
        raise ValueError("user_id is required to save caller memory.")

    if not consent_given:
        logger.info("Consent not granted for user_id=%s. Refusing to save.", user_id)
        return {
            "status": "refused",
            "message": "Consent not granted by user. Caller memory was not saved.",
            "saved": False,
        }

    init_db(db_path)
    existing = get_caller(user_id, db_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Merge facts with existing caller facts if present
    merged_facts = {}
    if existing and existing.get("facts"):
        merged_facts.update(existing["facts"])

    if facts:
        clean_facts = sanitize_facts(facts)
        merged_facts.update(clean_facts)

    final_name = name or (existing.get("name") if existing else None)
    final_lang = language_preference or (
        existing.get("language_preference") if existing else None
    )
    facts_json = json.dumps(merged_facts)
    created_at = existing.get("created_at") if existing else now_iso

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO callers (user_id, name, language_preference, facts, consent_given, last_interaction, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = COALESCE(excluded.name, callers.name),
                language_preference = COALESCE(excluded.language_preference, callers.language_preference),
                facts = excluded.facts,
                consent_given = excluded.consent_given,
                last_interaction = excluded.last_interaction,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                final_name,
                final_lang,
                facts_json,
                1 if consent_given else 0,
                now_iso,
                created_at,
                now_iso,
            ),
        )
        conn.commit()

    logger.info("Saved memory for caller user_id=%s name=%s", user_id, final_name)
    return {
        "status": "success",
        "message": f"Caller memory successfully saved for {final_name or user_id}.",
        "saved": True,
        "record": {
            "user_id": user_id,
            "name": final_name,
            "language_preference": final_lang,
            "facts": merged_facts,
            "consent_given": True,
            "last_interaction": now_iso,
        },
    }
