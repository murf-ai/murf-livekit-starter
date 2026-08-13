"""SQLite database module for persistent caller memory and facts."""

import hashlib
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


# Day 8 — Financial Services success = eligibility completed OR document list delivered.
ELIGIBILITY_DONE_STATUSES = frozenset({"likely_eligible", "likely_not_eligible"})
VALID_CHANNELS = frozenset({"browser", "sip"})


def init_db(db_path: Path | str | None = None) -> None:
    """Initialize SQLite tables for caller memory and call outcomes."""
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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS call_outcomes (
                room_id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_seconds REAL,
                outcome TEXT,
                failure_type TEXT,
                eligibility_completed INTEGER DEFAULT 0,
                eligibility_started INTEGER DEFAULT 0,
                document_list_delivered INTEGER DEFAULT 0,
                escalation_created INTEGER DEFAULT 0,
                tool_failure INTEGER DEFAULT 0,
                scheme_codes TEXT,
                user_turns INTEGER DEFAULT 0,
                first_reply_latency_ms INTEGER,
                last_reply_latency_ms INTEGER,
                connected INTEGER DEFAULT 0
            )
            """
        )
        cols = {
            row[1] for row in cursor.execute("PRAGMA table_info(call_outcomes)")
        }
        if "connected" not in cols:
            cursor.execute(
                "ALTER TABLE call_outcomes ADD COLUMN connected INTEGER DEFAULT 0"
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _public_call_id(room_id: str) -> str:
    """Short non-identifying handle. Never the full room name."""
    clean = (room_id or "").strip()
    if not clean:
        return "call"
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:8]


def _scheme_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if item]


def _add_scheme(raw: str | None, scheme_code: str | None) -> str:
    codes = _scheme_list(raw)
    code = (scheme_code or "").strip().lower()
    if code and code not in codes:
        codes.append(code)
    return json.dumps(codes)


def _row_to_call(row: sqlite3.Row) -> dict:
    return {
        "call_id": _public_call_id(row["room_id"]),
        "channel": row["channel"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "duration_seconds": row["duration_seconds"],
        "outcome": row["outcome"],
        "failure_type": row["failure_type"],
        "eligibility_completed": bool(row["eligibility_completed"]),
        "document_list_delivered": bool(row["document_list_delivered"]),
        "escalation_created": bool(row["escalation_created"]),
        "scheme_codes": _scheme_list(row["scheme_codes"]),
        "user_turns": row["user_turns"] or 0,
        "first_reply_latency_ms": row["first_reply_latency_ms"],
        "last_reply_latency_ms": row["last_reply_latency_ms"],
        "connected": bool(row["connected"]),
    }


def start_call(
    room_id: str,
    channel: str = "browser",
    db_path: Path | str | None = None,
) -> dict:
    """Open a call-outcome row when a browser or SIP session starts."""
    if not room_id:
        raise ValueError("room_id is required to start a call record.")
    clean_channel = channel if channel in VALID_CHANNELS else "browser"
    init_db(db_path)
    now_iso = _now_iso()
    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO call_outcomes (
                room_id, channel, started_at, scheme_codes
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id) DO NOTHING
            """,
            (room_id, clean_channel, now_iso, "[]"),
        )
        conn.commit()
    logger.info("Started call record room=%s channel=%s", room_id, clean_channel)
    return {"room_id": room_id, "channel": clean_channel, "started_at": now_iso}


def mark_call_connected(room_id: str, db_path: Path | str | None = None) -> None:
    """Mark that the caller actually joined (not cancelled on the connecting screen)."""
    if not room_id:
        return
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        conn.execute(
            "UPDATE call_outcomes SET connected = 1 WHERE room_id = ?",
            (room_id,),
        )
        conn.commit()


def _update_call_flags(
    room_id: str,
    db_path: Path | str | None = None,
    *,
    eligibility_started: bool = False,
    eligibility_completed: bool = False,
    document_list_delivered: bool = False,
    escalation_created: bool = False,
    tool_failure: bool = False,
    scheme_code: str | None = None,
    user_turn: bool = False,
    reply_latency_ms: int | None = None,
) -> None:
    if not room_id:
        return
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM call_outcomes WHERE room_id = ?",
            (room_id,),
        ).fetchone()
        if not row:
            logger.warning("No call record for room=%s; skipping flag update", room_id)
            return

        schemes = _add_scheme(row["scheme_codes"], scheme_code)
        first_latency = row["first_reply_latency_ms"]
        last_latency = row["last_reply_latency_ms"]
        if reply_latency_ms is not None and reply_latency_ms >= 0:
            last_latency = int(reply_latency_ms)
            if first_latency is None:
                first_latency = last_latency

        conn.execute(
            """
            UPDATE call_outcomes SET
                eligibility_started = MAX(eligibility_started, ?),
                eligibility_completed = MAX(eligibility_completed, ?),
                document_list_delivered = MAX(document_list_delivered, ?),
                escalation_created = MAX(escalation_created, ?),
                tool_failure = MAX(tool_failure, ?),
                scheme_codes = ?,
                user_turns = user_turns + ?,
                first_reply_latency_ms = ?,
                last_reply_latency_ms = ?
            WHERE room_id = ?
            """,
            (
                1 if eligibility_started else 0,
                1 if eligibility_completed else 0,
                1 if document_list_delivered else 0,
                1 if escalation_created else 0,
                1 if tool_failure else 0,
                schemes,
                1 if user_turn else 0,
                first_latency,
                last_latency,
                room_id,
            ),
        )
        conn.commit()


def record_eligibility_result(
    room_id: str,
    result: dict | None,
    db_path: Path | str | None = None,
) -> None:
    """Mark eligibility progress from a tool payload. No PII is stored."""
    payload = result or {}
    scheme = payload.get("scheme_code") or payload.get("scheme_short_name")
    status = str(payload.get("status") or "")
    if not payload.get("ok"):
        _update_call_flags(room_id, db_path, tool_failure=True, scheme_code=scheme)
        return
    if status in ELIGIBILITY_DONE_STATUSES:
        _update_call_flags(
            room_id,
            db_path,
            eligibility_started=True,
            eligibility_completed=True,
            scheme_code=scheme,
        )
        return
    _update_call_flags(room_id, db_path, eligibility_started=True, scheme_code=scheme)


def record_document_list_result(
    room_id: str,
    result: dict | None,
    db_path: Path | str | None = None,
) -> None:
    payload = result or {}
    scheme = payload.get("scheme_code") or payload.get("scheme_short_name")
    if payload.get("ok"):
        _update_call_flags(
            room_id,
            db_path,
            document_list_delivered=True,
            scheme_code=scheme,
        )
        return
    _update_call_flags(room_id, db_path, tool_failure=True, scheme_code=scheme)


def record_escalation(room_id: str, db_path: Path | str | None = None) -> None:
    _update_call_flags(room_id, db_path, escalation_created=True)


def record_tool_error(room_id: str, db_path: Path | str | None = None) -> None:
    _update_call_flags(room_id, db_path, tool_failure=True)


def note_user_turn(room_id: str, db_path: Path | str | None = None) -> None:
    _update_call_flags(room_id, db_path, user_turn=True)


def note_reply_latency_ms(
    room_id: str,
    latency_ms: int,
    db_path: Path | str | None = None,
) -> None:
    _update_call_flags(room_id, db_path, reply_latency_ms=latency_ms)


def end_call(
    room_id: str,
    channel: str | None = None,
    db_path: Path | str | None = None,
) -> dict:
    """Close the call and set success/failed from the Day 8 success condition."""
    if not room_id:
        raise ValueError("room_id is required to end a call record.")
    init_db(db_path)
    now_iso = _now_iso()
    with get_db_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM call_outcomes WHERE room_id = ?",
            (room_id,),
        ).fetchone()
        if not row:
            start_call(room_id, channel or "browser", db_path)
            row = conn.execute(
                "SELECT * FROM call_outcomes WHERE room_id = ?",
                (room_id,),
            ).fetchone()

        connected = bool(row["connected"])
        user_turns = int(row["user_turns"] or 0)
        # Success if connected and successfully talked to user query at least once (user_turns >= 1)
        success = connected and user_turns >= 1
        outcome = "success" if success else "failed"
        if success:
            failure_type = None
        elif row["tool_failure"]:
            failure_type = "tool_failure"
        elif not connected:
            failure_type = "cancelled_before_connect"
        else:
            failure_type = "incomplete_task"
        started = _parse_iso(row["started_at"])
        ended = datetime.now(timezone.utc)
        duration = (ended - started).total_seconds() if started else 0.0
        final_channel = (
            channel
            if channel in VALID_CHANNELS
            else (row["channel"] if row["channel"] in VALID_CHANNELS else "browser")
        )

        conn.execute(
            """
            UPDATE call_outcomes SET
                channel = ?,
                ended_at = ?,
                duration_seconds = ?,
                outcome = ?,
                failure_type = ?
            WHERE room_id = ?
            """,
            (final_channel, now_iso, duration, outcome, failure_type, room_id),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM call_outcomes WHERE room_id = ?",
            (room_id,),
        ).fetchone()

    logger.info(
        "Ended call room=%s outcome=%s failure_type=%s",
        room_id,
        outcome,
        failure_type,
    )
    return _row_to_call(updated)


def record_cancelled_call(
    room_id: str | None = None,
    channel: str = "browser",
    db_path: Path | str | None = None,
) -> dict:
    """Record a call the user cancelled before connecting."""
    rid = room_id or f"cancelled_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    start_call(rid, channel, db_path)
    return end_call(rid, channel, db_path)


def _call_filters(
    channel: str | None = None,
    since: str | None = None,
) -> tuple[str, list]:
    clauses: list[str] = ["ended_at IS NOT NULL"]
    params: list = []
    if channel in VALID_CHANNELS:
        clauses.append("channel = ?")
        params.append(channel)
    if since:
        clauses.append("started_at >= ?")
        params.append(since)
    return " AND ".join(clauses), params


def get_call_stats(
    channel: str | None = None,
    since: str | None = None,
    db_path: Path | str | None = None,
) -> dict:
    """Aggregate dashboard numbers from recorded calls. No PII."""
    init_db(db_path)
    where, params = _call_filters(channel, since)
    with get_db_connection(db_path) as conn:
        totals = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total_calls,
                SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) AS successful_calls,
                SUM(CASE WHEN outcome = 'failed' THEN 1 ELSE 0 END) AS failed_calls,
                SUM(eligibility_completed) AS eligibility_checks,
                SUM(document_list_delivered) AS document_lists,
                SUM(escalation_created) AS escalations,
                AVG(first_reply_latency_ms) AS avg_first_reply_latency_ms
            FROM call_outcomes
            WHERE {where}
            """,
            params,
        ).fetchone()
        failure_rows = conn.execute(
            f"""
            SELECT failure_type, COUNT(*) AS n
            FROM call_outcomes
            WHERE {where} AND outcome = 'failed' AND failure_type IS NOT NULL
            GROUP BY failure_type
            """,
            params,
        ).fetchall()

    total = int(totals["total_calls"] or 0)
    successful = int(totals["successful_calls"] or 0)
    failed = int(totals["failed_calls"] or 0)
    success_rate = round((successful / total) * 100, 1) if total else 0.0
    avg_latency = totals["avg_first_reply_latency_ms"]
    return {
        "total_calls": total,
        "successful_calls": successful,
        "failed_calls": failed,
        "success_rate": success_rate,
        "eligibility_checks": int(totals["eligibility_checks"] or 0),
        "document_lists": int(totals["document_lists"] or 0),
        "escalations": int(totals["escalations"] or 0),
        "avg_first_reply_latency_ms": (
            int(avg_latency) if avg_latency is not None else None
        ),
        "failure_types": {row["failure_type"]: int(row["n"]) for row in failure_rows},
    }


def get_recent_calls(
    limit: int = 20,
    channel: str | None = None,
    since: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict]:
    """Recent closed calls for the dashboard. Public fields only."""
    init_db(db_path)
    where, params = _call_filters(channel, since)
    cap = max(1, min(int(limit or 20), 100))
    with get_db_connection(db_path) as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM call_outcomes
            WHERE {where}
            ORDER BY ended_at DESC
            LIMIT ?
            """,
            [*params, cap],
        ).fetchall()
    return [_row_to_call(row) for row in rows]


def get_dashboard_payload(
    channel: str | None = None,
    since: str | None = None,
    limit: int = 20,
    db_path: Path | str | None = None,
) -> dict:
    stats = get_call_stats(channel=channel, since=since, db_path=db_path)
    return {
        **stats,
        "recent_calls": get_recent_calls(
            limit=limit, channel=channel, since=since, db_path=db_path
        ),
        "filters": {"channel": channel, "since": since},
        "success_condition": (
            "Caller connected and interacted with the agent at least once (user turns >= 1)."
        ),
    }


def clear_call_outcomes(db_path: Path | str | None = None) -> None:
    """Clear all records in the call_outcomes table."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        conn.execute("DELETE FROM call_outcomes")
        conn.commit()
    logger.info("Cleared all records in call_outcomes table.")
