import sqlite3
import json
import logging
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from livekit.agents import function_tool, RunContext

logger = logging.getLogger("memory")

DB_PATH = Path(__file__).parent / "caller_memory.db"


def init_db(db_path: Path = DB_PATH) -> None:
    """Initialize SQLite database schema for caller memory and call outcome tracking."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caller_memory (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                language_preference TEXT,
                facts TEXT,
                last_interaction TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_outcomes (
                call_id TEXT PRIMARY KEY,
                timestamp TEXT,
                outcome TEXT,
                outcome_reason TEXT
            )
        """)
        conn.commit()


def sanitize_facts(fact_text: str) -> str:
    """
    Redacts sensitive financial data (full account numbers, card numbers, PINs, OTPs, CVVs, passwords).
    Hard rule: account numbers or full card numbers are NEVER persisted.
    """
    if not fact_text:
        return ""
    
    # 1. Redact 10-19 digit account or card numbers -> replace with ending in XXXX
    sanitized = re.sub(r'\b\d{10,19}\b', lambda m: f"ending in {m.group(0)[-4:]}", fact_text)
    
    # 2. Redact explicit PINs, OTPs, CVVs, Passwords
    sanitized = re.sub(r'(?i)\b(pin|otp|cvv|password)[:\s]+\d+\b', r'\1: [REDACTED]', sanitized)
    
    return sanitized


def lookup_caller(user_id: str, db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Look up caller record in SQLite database."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM caller_memory WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            try:
                facts_list = json.loads(row[3]) if row[3] else []
            except Exception:
                facts_list = [row[3]] if row[3] else []
                
            return {
                "exists": True,
                "user_id": row[0],
                "name": row[1] or "",
                "language_preference": row[2] or "English",
                "facts": facts_list,
                "last_interaction": row[4] or ""
            }
        return {"exists": False, "user_id": user_id, "facts": []}


def save_caller(
    user_id: str,
    name: Optional[str] = None,
    language_preference: Optional[str] = None,
    new_facts: Optional[List[str]] = None,
    db_path: Path = DB_PATH
) -> Dict[str, Any]:
    """Save or update caller facts in SQLite database with sensitive data redaction."""
    init_db(db_path)
    existing = lookup_caller(user_id, db_path=db_path)
    
    current_name = name if name else existing.get("name", "")
    current_lang = language_preference if language_preference else existing.get("language_preference", "English")
    
    existing_facts = existing.get("facts", [])
    
    if new_facts:
        for f in new_facts:
            sanitized = sanitize_facts(f)
            if sanitized and sanitized not in existing_facts:
                existing_facts.append(sanitized)
                
    now_str = datetime.now(timezone.utc).isoformat()
    facts_json = json.dumps(existing_facts)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO caller_memory (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction
        """, (user_id, current_name, current_lang, facts_json, now_str))
        conn.commit()
        
    return {
        "status": "saved",
        "user_id": user_id,
        "name": current_name,
        "language_preference": current_lang,
        "facts": existing_facts,
        "last_interaction": now_str
    }


@function_tool
async def lookup_caller_memory(
    self,
    context: RunContext,
    user_id: str
) -> Dict[str, Any]:
    """
    Looks up saved memory facts for a returning caller by user identity or phone number.
    Use this tool when you need to recall caller history, name, preferred language, or previous financial scheme checks.
    """
    logger.info(f"Looking up memory for user_id={user_id}")
    return lookup_caller(user_id)


@function_tool
async def save_caller_memory(
    self,
    context: RunContext,
    user_id: str,
    name: Optional[str] = None,
    language_preference: Optional[str] = None,
    facts_to_remember: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Saves caller information, scheme eligibility answers, or preferences to persistent storage.
    HARD RULE: MUST obtain caller explicit permission FIRST before calling this tool.
    NEVER pass account numbers, full card numbers, PINs, or passwords to this tool.
    """
    logger.info(f"Saving caller memory for user_id={user_id}")
    return save_caller(
        user_id=user_id,
        name=name,
        language_preference=language_preference,
        new_facts=facts_to_remember
    )


def log_call_outcome(
    call_id: str,
    outcome: str,
    outcome_reason: str,
    db_path: Path = DB_PATH
) -> None:
    """Logs call outcome metadata using INSERT OR REPLACE to prevent duplicate primary key crashes."""
    t_start = datetime.now(timezone.utc).isoformat()
    init_db(db_path)
    now_str = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO call_outcomes (call_id, timestamp, outcome, outcome_reason)
            VALUES (?, ?, ?, ?)
        """, (call_id, now_str, outcome, outcome_reason))
        conn.commit()
    t_written = datetime.now(timezone.utc).isoformat()
    logger.info(f"[TIMESTAMP DEBUG 1c] DB write completed at {t_written} (started at {t_start}) for {call_id}: outcome={outcome}, reason={outcome_reason}")
    try:
        from ws_server import broadcast_outcome
        broadcast_outcome({
            "call_id": call_id,
            "timestamp": now_str,
            "outcome": outcome,
            "outcome_reason": outcome_reason,
        })
    except Exception as e:
        logger.warning(f"WS broadcast error: {e}")
    logger.info(f"[TIMESTAMP DEBUG 1d] Broadcast event triggered at {t_written}")


def get_call_stats(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Retrieves call outcome stats (total_calls, successful_calls, failed_calls, details)."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM call_outcomes")
        total_calls = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM call_outcomes WHERE outcome = 'success'")
        successful_calls = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM call_outcomes WHERE outcome = 'failed'")
        failed_calls = cursor.fetchone()[0]

        cursor.execute("SELECT call_id, timestamp, outcome, outcome_reason FROM call_outcomes ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        records = [
            {"call_id": r[0], "timestamp": r[1], "outcome": r[2], "outcome_reason": r[3]}
            for r in rows
        ]

    return {
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
        "records": records,
    }
