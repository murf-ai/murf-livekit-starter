# db.py
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "caller_data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            ref_id TEXT PRIMARY KEY,
            caller_id TEXT,
            caller_name TEXT,
            reason TEXT,
            situation_summary TEXT,
            what_agent_checked TEXT,
            urgency TEXT,
            caller_language TEXT,
            preferred_followup TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            call_id          TEXT PRIMARY KEY,
            user_id          TEXT,
            call_type        TEXT,
            started_at       TEXT,
            ended_at         TEXT,
            outcome          TEXT DEFAULT 'in_progress',
            success_trigger  TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_caller(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM callers WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "language_preference": row["language_preference"],
            "facts": json.loads(row["facts"]) if row["facts"] else {},
            "last_interaction": row["last_interaction"]
        }
    return None

def save_caller(user_id: str, name: str, language_preference: str, facts: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    facts_str = json.dumps(facts)
    last_interaction = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            facts = excluded.facts,
            last_interaction = excluded.last_interaction
    """, (user_id, name, language_preference, facts_str, last_interaction))
    conn.commit()
    conn.close()

def get_user(user_id: str):
    return get_caller(user_id)

def save_user(user_id: str, name: str, language_preference: str, facts: dict):
    save_caller(user_id, name, language_preference, facts)

def create_escalation(
    caller_id: str,
    caller_name: str,
    situation: str,
    what_happened: str,
    checked_facts: dict,
    urgency: str,
    language: str,
    follow_up_method: str,
    contact_details: str
) -> str:
    import random
    import string
    ref_suffix = "".join(random.choices(string.digits, k=6))
    ref_id = f"REF-{ref_suffix}"
    
    save_escalation(
        ref_id=ref_id,
        caller_id=caller_id,
        caller_name=caller_name,
        reason=situation,
        situation_summary=what_happened,
        what_agent_checked=json.dumps(checked_facts),
        urgency=urgency,
        caller_language=language,
        preferred_followup=follow_up_method
    )
    return ref_id

def init_call_outcome(call_id: str, user_id: str, is_sip: bool):
    record_call_start(call_id, user_id, "sip" if is_sip else "browser")

def update_call_progress(call_id: str, status: str | None = None, outcome_type: str | None = None, failure_category: str | None = None):
    if status == "success" or outcome_type:
        record_call_end(call_id, "success", outcome_type)
    elif failure_category:
        record_call_end(call_id, "failed", failure_category)

def finalize_call_outcome(call_id: str, duration: int):
    pass

def add_latency_measurement(call_id: str, latency: float):
    # Log or store latency measurement
    print(f"Latency for {call_id}: {latency}s")

# Initialize DB on load
init_db()


# ---------------------------------------------------------------------------
# Escalation helpers
# ---------------------------------------------------------------------------

SENSITIVE_KEYWORDS = ["otp", "pin", "cvv", "password", "account number", "card number", "aadhaar", "pan"]

def _sanitize_text(text: str) -> str:
    """Return text with any line containing sensitive keywords redacted."""
    clean_lines = []
    for line in text.splitlines():
        lower = line.lower()
        if any(kw in lower for kw in SENSITIVE_KEYWORDS):
            clean_lines.append("[REDACTED – sensitive information removed]")
        else:
            clean_lines.append(line)
    return "\n".join(clean_lines)


def save_escalation(
    ref_id: str,
    caller_id: str,
    caller_name: str,
    reason: str,
    situation_summary: str,
    what_agent_checked: str,
    urgency: str,
    caller_language: str,
    preferred_followup: str,
) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO escalations
            (ref_id, caller_id, caller_name, reason, situation_summary,
             what_agent_checked, urgency, caller_language, preferred_followup,
             status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
    """, (
        ref_id,
        caller_id,
        _sanitize_text(caller_name),
        reason,
        _sanitize_text(situation_summary),
        _sanitize_text(what_agent_checked),
        urgency,
        caller_language,
        preferred_followup,
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()


def get_all_escalations() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM escalations ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_escalation_status(ref_id: str, status: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE escalations SET status = ? WHERE ref_id = ?",
        (status, ref_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


# ---------------------------------------------------------------------------
# Call-analytics helpers
# ---------------------------------------------------------------------------

def record_call_start(call_id: str, user_id: str, call_type: str) -> None:
    """Insert a new call row when a session begins."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO calls
            (call_id, user_id, call_type, started_at, outcome)
        VALUES (?, ?, ?, ?, 'in_progress')
    """, (call_id, user_id, call_type, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def record_call_end(
    call_id: str,
    outcome: str,
    success_trigger: str | None = None,
) -> None:
    """Update a call row when the session ends.

    Args:
        call_id: LiveKit room name (unique per session).
        outcome: 'success' or 'failed'.
        success_trigger: Name of the tool/event that caused success, if any.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE calls
        SET ended_at = ?, outcome = ?, success_trigger = ?
        WHERE call_id = ?
    """, (datetime.now().isoformat(), outcome, success_trigger, call_id))
    conn.commit()
    conn.close()


def get_call_stats() -> dict:
    """Return aggregate counts for the analytics dashboard."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT outcome, COUNT(*) FROM calls GROUP BY outcome")
    rows = cursor.fetchall()
    conn.close()
    counts = {row[0]: row[1] for row in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "successful": counts.get("success", 0),
        "failed": counts.get("failed", 0),
        "in_progress": counts.get("in_progress", 0),
    }


def get_recent_calls(limit: int = 50) -> list:
    """Return recent calls for display — no caller names or transcripts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT call_id, call_type, started_at, ended_at, outcome, success_trigger
        FROM calls
        ORDER BY started_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
