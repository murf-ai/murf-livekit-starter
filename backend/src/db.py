import sqlite3
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("finsafe_db")

DB_PATH = Path(__file__).parent.parent / "finsafe_memory.db"

SENSITIVE_KEYWORDS = [
    "aadhaar", "pan", "otp", "password", "passcode", "pin", "cvv",
    "card_number", "account_number", "bank_account", "secret", "ssn"
]

# Regex patterns for sensitive data
AADHAAR_PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PAN_PATTERN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]{1}\b", re.IGNORECASE)
CARD_PATTERN = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
ACCOUNT_NUM_PATTERN = re.compile(r"\b\d{9,18}\b")


def is_sensitive(key: str, value: str) -> bool:
    """Check if fact key or value contains prohibited sensitive financial data."""
    combined = f"{key} {value}".lower()
    
    # Check keywords
    for kw in SENSITIVE_KEYWORDS:
        if kw in combined:
            logger.warning(f"Security Filter: Blocked sensitive keyword '{kw}' in memory save attempt.")
            return True
            
    # Check regexes
    if AADHAAR_PATTERN.search(value):
        logger.warning("Security Filter: Blocked potential Aadhaar number.")
        return True
    if PAN_PATTERN.search(value):
        logger.warning("Security Filter: Blocked potential PAN number.")
        return True
    if CARD_PATTERN.search(value):
        logger.warning("Security Filter: Blocked potential Card number.")
        return True
        
    return False


def get_db_connection():
    """Create and return a SQLite database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the SQLite database schema if tables do not exist."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS callers (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    language_preference TEXT,
                    last_interaction TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS caller_facts (
                    user_id TEXT,
                    fact_key TEXT,
                    fact_value TEXT,
                    updated_at TEXT,
                    PRIMARY KEY (user_id, fact_key),
                    FOREIGN KEY (user_id) REFERENCES callers (user_id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            logger.info(f"SQLite Database initialized successfully at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database: {e}", exc_info=True)


def lookup_caller(user_id: str) -> dict:
    """Lookup an existing caller record from SQLite.
    
    Returns a structured dictionary indicating caller existence, saved details, and facts.
    """
    if not user_id:
        return {"exists": False, "error": "No user_id provided"}

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, name, language_preference, last_interaction, created_at FROM callers WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "exists": False,
                    "user_id": user_id,
                    "message": "New caller. No prior memory record found."
                }

            cursor.execute(
                "SELECT fact_key, fact_value FROM caller_facts WHERE user_id = ?",
                (user_id,)
            )
            fact_rows = cursor.fetchall()
            facts = {r["fact_key"]: r["fact_value"] for r in fact_rows}

            return {
                "exists": True,
                "user_id": row["user_id"],
                "name": row["name"] or "",
                "language_preference": row["language_preference"] or "",
                "facts": facts,
                "last_interaction": row["last_interaction"] or "",
                "created_at": row["created_at"] or ""
            }
    except Exception as e:
        logger.error(f"SQLite lookup_caller error for user_id={user_id}: {e}", exc_info=True)
        return {
            "exists": False,
            "user_id": user_id,
            "error": f"Database unavailable: {str(e)}"
        }


def save_caller_memory_db(
    user_id: str,
    name: str = None,
    language_preference: str = None,
    facts: dict = None
) -> dict:
    """Save or update caller information and financial facts in SQLite.
    
    Security filters block sensitive numbers and credentials before writing.
    """
    if not user_id:
        return {"success": False, "error": "user_id is required"}

    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check existing record
            cursor.execute("SELECT name, language_preference FROM callers WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()

            if existing:
                updated_name = name.strip() if (name and name.strip()) else existing["name"]
                updated_lang = language_preference.strip() if (language_preference and language_preference.strip()) else existing["language_preference"]
                
                cursor.execute("""
                    UPDATE callers
                    SET name = ?, language_preference = ?, last_interaction = ?
                    WHERE user_id = ?
                """, (updated_name, updated_lang, now_iso, user_id))
            else:
                initial_name = name.strip() if name else ""
                initial_lang = language_preference.strip() if language_preference else ""
                cursor.execute("""
                    INSERT INTO callers (user_id, name, language_preference, last_interaction, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, initial_name, initial_lang, now_iso, now_iso))

            saved_facts_count = 0
            blocked_facts_count = 0

            if facts:
                for fk, fv in facts.items():
                    key_str = str(fk).strip()
                    val_str = str(fv).strip()
                    if not key_str or not val_str:
                        continue
                    
                    if is_sensitive(key_str, val_str):
                        blocked_facts_count += 1
                        continue

                    cursor.execute("""
                        INSERT INTO caller_facts (user_id, fact_key, fact_value, updated_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(user_id, fact_key) DO UPDATE SET
                            fact_value = excluded.fact_value,
                            updated_at = excluded.updated_at
                    """, (user_id, key_str, val_str, now_iso))
                    saved_facts_count += 1

            conn.commit()
            
            # Retrieve updated full record
            return lookup_caller(user_id)

    except Exception as e:
        logger.error(f"SQLite save_caller_memory_db error for user_id={user_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Database unavailable: {str(e)}"
        }


# Initialize DB on module import
init_db()
