import contextlib
import json
import os
import random
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "caller_data.db",
)


def init_db():
    """Initializes SQLite DB with users and escalations tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id TEXT UNIQUE,
            caller_id TEXT,
            caller_name TEXT,
            situation TEXT,
            what_happened TEXT,
            checked_facts TEXT,
            urgency TEXT,
            language TEXT,
            follow_up_method TEXT,
            contact_details TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'open'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT,
            participant_identity TEXT,
            status TEXT DEFAULT 'started',
            created_at TEXT,
            ended_at TEXT,
            error_message TEXT,
            duration INTEGER DEFAULT 0,
            avg_latency REAL DEFAULT 0.0,
            channel TEXT DEFAULT 'Browser',
            language TEXT DEFAULT 'English',
            failure_type TEXT DEFAULT 'none',
            outcome_type TEXT DEFAULT 'none'
        )
    """)
    alterations = [
        "ALTER TABLE calls ADD COLUMN duration INTEGER DEFAULT 0",
        "ALTER TABLE calls ADD COLUMN avg_latency REAL DEFAULT 0.0",
        "ALTER TABLE calls ADD COLUMN channel TEXT DEFAULT 'Browser'",
        "ALTER TABLE calls ADD COLUMN language TEXT DEFAULT 'English'",
        "ALTER TABLE calls ADD COLUMN failure_type TEXT DEFAULT 'none'",
        "ALTER TABLE calls ADD COLUMN outcome_type TEXT DEFAULT 'none'",
    ]
    for alt in alterations:
        with contextlib.suppress(sqlite3.OperationalError):
            cursor.execute(alt)
    conn.commit()
    conn.close()


def get_user(user_id: str):
    """Retrieves user details from database by user_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, name, language_preference, facts, last_interaction"
        " FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            facts = json.loads(row[3])
        except Exception:
            facts = {}
        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": facts,
            "last_interaction": row[4],
        }
    return None


def save_user(user_id: str, name: str, language_preference: str, facts: dict):
    """Saves or updates user details and facts in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    facts_str = json.dumps(facts)
    last_interaction = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            facts = excluded.facts,
            last_interaction = excluded.last_interaction
    """,
        (user_id, name, language_preference, facts_str, last_interaction),
    )
    conn.commit()
    conn.close()
    return {
        "user_id": user_id,
        "name": name,
        "language_preference": language_preference,
        "facts": facts,
        "last_interaction": last_interaction,
    }


def remove_private_info(text: str) -> str:
    if not text:
        return text

    card_pattern = r"\b(?:\d[ -]*?){13,19}\b"
    aadhaar_pattern = r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"
    pan_pattern = r"\b[A-Z]{5}\d{4}[A-Z]\b"
    account_pattern = r"\b\d{9,18}\b"
    keyword_code_pattern = (
        r"\b(?:pin|otp|password|pwd|passcode|cvv|code)\b\s*[:=-]?\s*[a-zA-Z0-9]+"
    )

    sanitized = text
    sanitized = re.sub(pan_pattern, "[REDACTED PAN]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(card_pattern, "[REDACTED CARD]", sanitized)
    sanitized = re.sub(aadhaar_pattern, "[REDACTED AADHAAR]", sanitized)
    sanitized = re.sub(account_pattern, "[REDACTED ACCOUNT]", sanitized)

    def redact_sensitive_keyword(match):
        val = match.group(0)
        keyword_match = re.search(
            r"\b(?:pin|otp|password|pwd|passcode|cvv|code)\b",
            val,
            re.IGNORECASE,
        )
        if keyword_match:
            return f"{keyword_match.group(0)}: [REDACTED]"
        return "[REDACTED]"

    sanitized = re.sub(
        keyword_code_pattern,
        redact_sensitive_keyword,
        sanitized,
        flags=re.IGNORECASE,
    )
    return sanitized


def trigger_webhook(payload: dict):
    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        return
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception as e:
        print(f"Webhook delivery failed: {e}", file=sys.stderr)


def create_escalation(
    caller_id: str,
    caller_name: str,
    situation: str,
    what_happened: str,
    checked_facts: dict,
    urgency: str,
    language: str,
    follow_up_method: str,
    contact_details: str,
) -> str:
    """Inserts or updates a human support escalation request and returns Reference ID."""
    caller_name = remove_private_info(caller_name)
    situation = remove_private_info(situation)
    what_happened = remove_private_info(what_happened)
    contact_details = remove_private_info(contact_details)

    urgency = urgency.capitalize().strip() if urgency else "Low"
    urgency_ranks = {"Low": 1, "Medium": 2, "High": 3, "Emergency": 4}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, reference_id, what_happened, checked_facts, urgency
        FROM escalations
        WHERE caller_id = ? AND situation = ? AND status = 'open'
    """,
        (caller_id, situation),
    )
    existing = cursor.fetchone()

    if existing:
        (
            db_id,
            reference_id,
            prev_what_happened,
            prev_checked_facts_str,
            prev_urgency,
        ) = existing

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_what_happened = (
            f"{prev_what_happened}\n\n[Updated {timestamp_str}]: {what_happened}"
        )

        try:
            prev_facts = (
                json.loads(prev_checked_facts_str) if prev_checked_facts_str else {}
            )
        except Exception:
            prev_facts = {}

        merged_facts = {**prev_facts, **(checked_facts or {})}
        merged_facts_str = json.dumps(merged_facts)

        prev_rank = urgency_ranks.get(prev_urgency, 1)
        new_rank = urgency_ranks.get(urgency, 1)
        final_urgency = prev_urgency if prev_rank >= new_rank else urgency

        updated_at = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE escalations
            SET what_happened = ?, checked_facts = ?, urgency = ?, created_at = ?, contact_details = ?, follow_up_method = ?, language = ?
            WHERE id = ?
        """,
            (
                updated_what_happened,
                merged_facts_str,
                final_urgency,
                updated_at,
                contact_details,
                follow_up_method,
                language,
                db_id,
            ),
        )
        conn.commit()
        conn.close()

        trigger_webhook(
            {
                "event": "escalation_updated",
                "reference_id": reference_id,
                "caller_name": caller_name,
                "situation": situation,
                "what_happened": updated_what_happened,
                "urgency": final_urgency,
                "language": language,
                "follow_up_method": follow_up_method,
                "contact_details": contact_details,
                "updated_at": updated_at,
            }
        )
        return reference_id

    date_str = datetime.now().strftime("%Y%m%d")
    random_suffix = "".join(random.choices("0123456789", k=4))
    reference_id = f"ESC-{date_str}-{random_suffix}"

    checked_facts_str = json.dumps(checked_facts)
    created_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO escalations (
            reference_id, caller_id, caller_name, situation, what_happened,
            checked_facts, urgency, language, follow_up_method, contact_details,
            created_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
    """,
        (
            reference_id,
            caller_id,
            caller_name,
            situation,
            what_happened,
            checked_facts_str,
            urgency,
            language,
            follow_up_method,
            contact_details,
            created_at,
        ),
    )
    conn.commit()
    conn.close()

    trigger_webhook(
        {
            "event": "escalation_created",
            "reference_id": reference_id,
            "caller_name": caller_name,
            "situation": situation,
            "what_happened": what_happened,
            "urgency": urgency,
            "language": language,
            "follow_up_method": follow_up_method,
            "contact_details": contact_details,
            "created_at": created_at,
        }
    )
    return reference_id


def start_call(
    room_name: str, participant_identity: str, channel: str = "Browser"
) -> int:
    """Logs the start of a call and returns the call log ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO calls (room_name, participant_identity, status, created_at, channel)
        VALUES (?, ?, 'started', ?, ?)
    """,
        (room_name, participant_identity, created_at, channel),
    )
    call_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return call_id


def complete_call(
    call_id: int,
    status: str,
    error_message: Optional[str] = None,
    avg_latency: float = 0.0,
    language: str = "English",
    failure_type: str = "none",
    outcome_type: str = "none",
):
    """Updates the status, ended time, duration, and metrics of a call log."""
    if not call_id:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ended_at = datetime.now().isoformat()
    duration = 0
    try:
        cursor.execute("SELECT created_at FROM calls WHERE id = ?", (call_id,))
        row = cursor.fetchone()
        if row and row[0]:
            from datetime import datetime as dt

            start_dt = dt.fromisoformat(row[0])
            end_dt = dt.fromisoformat(ended_at)
            duration = int((end_dt - start_dt).total_seconds())
    except Exception as e:
        print(f"Error calculating call duration: {e}")

    cursor.execute(
        """
        UPDATE calls
        SET status = ?, ended_at = ?, error_message = ?, duration = ?,
            avg_latency = ?, language = ?, failure_type = ?, outcome_type = ?
        WHERE id = ?
    """,
        (
            status,
            ended_at,
            error_message,
            duration,
            avg_latency,
            language,
            failure_type,
            outcome_type,
            call_id,
        ),
    )
    conn.commit()
    conn.close()


def get_call_stats() -> dict:
    """Returns advanced call statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM calls")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM calls WHERE status = 'success'")
        successful = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM calls WHERE status = 'failed'")
        failed = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM calls WHERE failure_type != 'user_declined'"
        )
        accepted = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM calls WHERE failure_type = 'user_declined'"
        )
        rejected = cursor.fetchone()[0]

        # Calculate average response latency
        cursor.execute(
            "SELECT AVG(avg_latency) FROM calls WHERE status = 'success' AND avg_latency > 0"
        )
        avg_latency = cursor.fetchone()[0] or 0.0

        # Success rate
        success_rate = (successful / total * 100) if total > 0 else 0.0

        # Failures group counts
        failures_group = {}
        cursor.execute(
            "SELECT failure_type, COUNT(*) FROM calls WHERE status = 'failed' GROUP BY failure_type"
        )
        for r in cursor.fetchall():
            failures_group[r[0]] = r[1]

        # Outcomes group counts
        outcomes_group = {
            "eligibility_check": 0,
            "escalation": 0,
            "saved_facts": 0,
            "none": 0,
        }
        cursor.execute("SELECT outcome_type, COUNT(*) FROM calls GROUP BY outcome_type")
        for r in cursor.fetchall():
            outcomes_group[r[0]] = r[1]

    except sqlite3.OperationalError:
        total, successful, failed, avg_latency, success_rate = 0, 0, 0, 0.0, 0.0
        accepted, rejected = 0, 0
        failures_group = {}
        outcomes_group = {}
    conn.close()
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "accepted": accepted,
        "rejected": rejected,
        "avg_latency": round(avg_latency, 2),
        "success_rate": round(success_rate, 1),
        "failures_group": failures_group,
        "outcomes_group": outcomes_group,
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "get_escalations_json":
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM escalations ORDER BY id DESC")
                rows = cursor.fetchall()
                result = []
                for r in rows:
                    item = dict(r)
                    with contextlib.suppress(Exception):
                        item["checked_facts"] = json.loads(item["checked_facts"])
                    result.append(item)
                print(json.dumps(result))
            except sqlite3.OperationalError:
                print(json.dumps([]))
            conn.close()
        elif cmd == "update_status" and len(sys.argv) > 3:
            ticket_id = sys.argv[2]
            new_status = sys.argv[3]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE escalations SET status = ? WHERE id = ?",
                (new_status, ticket_id),
            )
            conn.commit()
            conn.close()
            print(json.dumps({"success": True}))
        elif cmd == "delete_ticket" and len(sys.argv) > 2:
            ticket_id = sys.argv[2]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM escalations WHERE id = ?", (ticket_id,))
            conn.commit()
            conn.close()
            print(json.dumps({"success": True}))
        elif cmd == "get_call_stats_json":
            stats = get_call_stats()
            print(json.dumps(stats))
        elif cmd == "get_calls_history_json":
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM calls ORDER BY id DESC")
                rows = cursor.fetchall()
                result = [dict(r) for r in rows]
                print(json.dumps(result))
            except sqlite3.OperationalError:
                print(json.dumps([]))
            conn.close()
