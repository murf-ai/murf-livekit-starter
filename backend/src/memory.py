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
    """Initialize SQLite database schema for caller memory persistence."""
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
