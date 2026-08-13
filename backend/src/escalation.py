"""Day 7 — Human escalation framework for Jan Sahay.

Secure, PII-sanitized case creation with:
- Explicit user consent gate
- Duplicate open-ticket prevention
- Status tracking (open / in_progress / resolved)
- Optional webhook dispatch
- Resolution callback hooks for outbound / Linphone notify
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("agent.escalation")

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "caller_memory.db"

Urgency = Literal["low", "medium", "high", "emergency"]
TicketStatus = Literal["open", "in_progress", "resolved"]
TriggerType = Literal["fraud_suspected", "complex_decision", "user_requested", "other"]

VALID_URGENCIES = frozenset({"low", "medium", "high", "emergency"})
VALID_STATUSES = frozenset({"open", "in_progress", "resolved"})
ACTIVE_STATUSES = frozenset({"open", "in_progress"})

# Free-text scrubbers for spoken / written case summaries.
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # OTP / PIN / password / CVV with optional filler (is/was/=/:) then value
    (
        re.compile(
            r"\b(?:otp|pin|upi\s*pin|password|passwd|passcode|cvv|cvc)\b"
            r"(?:\s*(?:is|was|were|equals))?"
            r"\s*[:=]?\s*\S+",
            re.IGNORECASE,
        ),
        "[REDACTED_SECRET]",
    ),
    # Aadhaar (12 digits, optional spaces/dashes) — before bare long runs
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[REDACTED_AADHAAR]"),
    # Card-like groups 4-4-4-4
    (re.compile(r"\b(?:\d{4}[\s-]){3}\d{4}\b"), "[REDACTED_CARD]"),
    # PAN
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE), "[REDACTED_PAN]"),
    # Long digit runs (account / card / phone as 10-18 digits)
    (re.compile(r"\b\d{10,18}\b"), "[REDACTED_NUMBER]"),
    # Standalone OTP/PIN-length codes next to financial context words
    (
        re.compile(
            r"\b(?:otp|pin|upi\s*pin|password|passwd|passcode|cvv|cvc)\b"
            r"(?:\s*(?:is|was|were|equals))?"
            r"\s*[:=]?\s*\S+",
            re.IGNORECASE,
        ),
        "[REDACTED_SECRET]",
    ),
]

# Trigger keyword banks (financial services domain).
_FRAUD_KEYWORDS = re.compile(
    r"\b("
    r"fraud|fraudulent|scam|phishing|unauthorized|unauthorised|"
    r"hacked|account\s+hack|my\s+account\s+was\s+hack|"
    r"stolen\s+(card|phone|device|money|account|debit|credit)|"
    r"lost\s+(my\s+)?((?:credit|debit|atm)\s+)?card|card\s+(lost|stolen|missing)|"
    r"debit\s+card\s+theft|debit\s+card\s+fraud|credit\s+card\s+theft|credit\s+card\s+fraud|"
    r"compromise|compromised|identity\s*theft|"
    r"someone\s+(else\s+)?(accessed|logged|used)|"
    r"not\s+me|didn't\s+(do|make|authori[sz]e)|did\s+not\s+(do|make|authori[sz]e)|"
    r"suspicious\s+(transaction|activity|login|debit)|"
    r"account\s+(taken|hacked|compromised)|"
    r"otp\s+(leak|stolen|shared|misuse)|"
    r"dhokha|dhokhe|dhokhadhadi|jalsaji|chori|theft|"
    r"card\s+kho\s*gaya|card\s+chori|fraud\s+hua|galat\s+transaction|bina\s+ijazat"
    r")\b",
    re.IGNORECASE,
)

_COMPLEX_KEYWORDS = re.compile(
    r"\b("
    r"dispute|chargeback|limit\s+override|override\s+limit|"
    r"transaction\s+limit|increase\s+(my\s+)?limit|"
    r"refund\s+(not|pending|stuck)|claim\s+(reject|denied|stuck)|"
    r"manager|supervisor|human\s+agent|speak\s+to\s+(a\s+)?(human|person|agent)|"
    r"complex|beyond\s+(your|agent)\s+(authority|scope)|"
    r"loan\s+waiver|write[\s-]?off|settlement|"
    r"application\s+status|track\s+(my\s+)?(claim|application|kyc)|"
    r"autopay|auto-pay|mandate|"
    r"vivad|shikayat|complaint|human\s+se\s+baat|agent\s+se\s+baat|"
    r"limit\s+badhao|refund\s+nahi|claim\s+reject"
    r")\b",
    re.IGNORECASE,
)

CONSENT_PROMPT_EN = (
    "I need to pass this case along to our human specialist team. "
    "I will share a summary of your issue and your contact preference. "
    "Do I have your permission to proceed?"
)

CONSENT_PROMPT_HI = (
    "Mujhe yeh mamla hamare human specialist team ko bhejna hoga. "
    "Main aapke issue ka summary aur contact preference share karungi. "
    "Kya mujhe aage badhne ki anumati hai?"
)

REFUSAL_SELF_SERVICE_EN = (
    "Understood — I will not create an escalation. "
    "You can still use self-service: visit your bank branch or CSC, "
    "check the official scheme portal, or call your bank helpline. "
    "How else can I help you today?"
)

REFUSAL_SELF_SERVICE_HI = (
    "Theek hai — main escalation nahi banaungi. "
    "Aap bank branch ya CSC ja sakte hain, official scheme portal check kar sakte hain, "
    "ya bank helpline par call kar sakte hain. Aur kaise madad karoon?"
)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def get_db_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = Path(db_path) if db_path else DEFAULT_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def init_escalation_db(db_path: Path | str | None = None) -> None:
    """Create escalations table if missing."""
    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                reference_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                requester_name TEXT,
                trigger_type TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                diagnostic_steps TEXT,
                urgency TEXT NOT NULL,
                preferred_language TEXT,
                follow_up_method TEXT,
                contact_hint TEXT,
                issue_fingerprint TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                summary_json TEXT,
                webhook_dispatched INTEGER DEFAULT 0,
                resolution_notes TEXT,
                resolved_at TEXT,
                callback_dispatched INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_escalations_user_status
            ON escalations (user_id, status)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_escalations_fingerprint
            ON escalations (user_id, issue_fingerprint, status)
            """
        )
        conn.commit()
    logger.info("Escalation database ready.")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    if data.get("summary_json"):
        try:
            data["summary"] = json.loads(data["summary_json"])
        except json.JSONDecodeError:
            data["summary"] = {}
    else:
        data["summary"] = {}
    data["webhook_dispatched"] = bool(data.get("webhook_dispatched"))
    data["callback_dispatched"] = bool(data.get("callback_dispatched"))
    # diagnostic_steps stored as JSON list string
    steps = data.get("diagnostic_steps")
    if isinstance(steps, str) and steps.startswith("["):
        try:
            data["diagnostic_steps"] = json.loads(steps)
        except json.JSONDecodeError:
            data["diagnostic_steps"] = [steps] if steps else []
    elif not steps:
        data["diagnostic_steps"] = []
    return data


# ---------------------------------------------------------------------------
# PII sanitization
# ---------------------------------------------------------------------------


def scrub_pii(text: str | None) -> str:
    """Strictly scrub passwords, OTPs, PINs, full account numbers, CVVs, etc."""
    if not text:
        return ""
    cleaned = str(text)
    for pattern, replacement in _PII_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    # Collapse leftover secret labels without values
    cleaned = re.sub(
        r"\b(password|passwd|otp|upi\s*pin|pin|cvv|cvc)\b",
        "[REDACTED_SECRET_LABEL]",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def sanitize_summary_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Deep-scrub string fields in a summary dict."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        key_l = str(key).lower()
        if any(
            bad in key_l
            for bad in (
                "password",
                "otp",
                "pin",
                "cvv",
                "aadhaar",
                "adhar",
                "account_number",
                "card_number",
                "secret",
            )
        ):
            logger.warning("Dropped forbidden escalation field: %s", key)
            continue
        if isinstance(value, str):
            out[key] = scrub_pii(value)
        elif isinstance(value, list):
            out[key] = [scrub_pii(v) if isinstance(v, str) else v for v in value]
        elif isinstance(value, dict):
            out[key] = sanitize_summary_fields(value)
        else:
            out[key] = value
    return out


# ---------------------------------------------------------------------------
# Trigger detection
# ---------------------------------------------------------------------------


def detect_escalation_trigger(text: str | None) -> TriggerType | None:
    """Return trigger type if conversation text warrants mandatory escalation."""
    if not text:
        return None
    if _FRAUD_KEYWORDS.search(text):
        return "fraud_suspected"
    if _COMPLEX_KEYWORDS.search(text):
        return "complex_decision"
    return None


def suggest_urgency(trigger_type: str, text: str | None = None) -> Urgency:
    """Map trigger + free text to urgency band."""
    t = (text or "").lower()
    if trigger_type == "fraud_suspected" or any(
        w in t for w in ("emergency", "right now", "abhi", "urgent fraud", "stolen")
    ):
        if any(w in t for w in ("emergency", "right now", "abhi chori", "ongoing")):
            return "emergency"
        return "high"
    if trigger_type == "complex_decision":
        if any(w in t for w in ("dispute", "refund stuck", "claim reject")):
            return "medium"
        return "medium"
    return "low"


def issue_fingerprint(user_id: str, trigger_type: str, issue_description: str) -> str:
    """Stable hash so identical open issues can be deduped."""
    base = f"{user_id.strip().lower()}|{trigger_type}|{scrub_pii(issue_description).lower()}"
    # Normalize whitespace
    base = re.sub(r"\s+", " ", base).strip()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]


def generate_reference_id() -> str:
    """Human-speakable reference, e.g. JS-A1B2C3D4."""
    return f"JS-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------


def build_case_summary(
    *,
    requester_name: str | None,
    user_id: str,
    issue_description: str,
    diagnostic_steps: list[str] | None,
    urgency: str,
    preferred_language: str | None,
    follow_up_method: str | None,
    trigger_type: str,
    contact_hint: str | None = None,
) -> dict[str, Any]:
    """Structured, PII-scrubbed case summary for human specialists."""
    urg = (urgency or "medium").lower().strip()
    if urg not in VALID_URGENCIES:
        urg = "medium"

    raw = {
        "requester_name": (requester_name or "Unknown").strip() or "Unknown",
        "requester_id": user_id.strip(),
        "issue_description": scrub_pii(issue_description),
        "diagnostic_steps": [
            scrub_pii(s) for s in (diagnostic_steps or []) if str(s).strip()
        ]
        or ["Agent collected caller report and validated escalation trigger."],
        "urgency": urg,
        "preferred_language": (preferred_language or "hi").strip() or "hi",
        "follow_up_method": scrub_pii(
            (follow_up_method or "voice_callback").strip() or "voice_callback"
        ),
        "trigger_type": trigger_type,
        "contact_hint": scrub_pii(contact_hint or ""),
        # Never include secrets — explicit empty markers for auditors
        "pii_policy": "scrubbed_no_passwords_otp_pin_full_account_cvv",
    }
    return sanitize_summary_fields(raw)


# ---------------------------------------------------------------------------
# Ticket CRUD + duplicate prevention
# ---------------------------------------------------------------------------


def find_active_duplicate(
    user_id: str,
    fingerprint: str,
    db_path: Path | str | None = None,
) -> dict[str, Any] | None:
    init_escalation_db(db_path)
    with get_db_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM escalations
            WHERE user_id = ? AND issue_fingerprint = ?
              AND status IN ('open', 'in_progress')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, fingerprint),
        ).fetchone()
    return _row_to_dict(row)


def get_escalation(
    reference_id: str, db_path: Path | str | None = None
) -> dict[str, Any] | None:
    if not reference_id:
        return None
    init_escalation_db(db_path)
    with get_db_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM escalations WHERE reference_id = ?",
            (reference_id.strip().upper(),),
        ).fetchone()
        if row is None:
            # Also try exact as given
            row = conn.execute(
                "SELECT * FROM escalations WHERE reference_id = ?",
                (reference_id.strip(),),
            ).fetchone()
    return _row_to_dict(row)


def list_escalations(
    user_id: str | None = None,
    status: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    init_escalation_db(db_path)
    clauses: list[str] = []
    params: list[Any] = []
    if user_id:
        clauses.append("user_id = ?")
        params.append(user_id)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_db_connection(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM escalations {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
    return [_row_to_dict(r) for r in rows if r is not None]  # type: ignore[misc]


def dispatch_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """POST sanitized payload to ESCALATION_WEBHOOK_URL if configured.

    Always also writes a local dashboard mirror under data/escalation_dispatch.log.
    """
    result: dict[str, Any] = {"attempted": False, "ok": False, "detail": "no_webhook"}
    log_path = DEFAULT_DB_PATH.parent / "escalation_dispatch.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {"ts": _now(), "event": "escalation_dispatch", "payload": payload},
        ensure_ascii=False,
    )
    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        result["local_log"] = str(log_path)
    except OSError as err:
        logger.warning("Could not write escalation dispatch log: %s", err)

    url = (os.environ.get("ESCALATION_WEBHOOK_URL") or "").strip()
    if not url:
        result["detail"] = "local_only"
        result["ok"] = True  # local persistence counts as success
        return result

    result["attempted"] = True
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "JanSahay-Escalation/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            result["ok"] = 200 <= getattr(resp, "status", 200) < 300
            result["detail"] = f"http_{getattr(resp, 'status', 200)}"
    except urllib.error.HTTPError as err:
        result["ok"] = False
        result["detail"] = f"http_error_{err.code}"
        logger.warning("Escalation webhook HTTP error: %s", err)
    except Exception as err:
        result["ok"] = False
        result["detail"] = f"error:{type(err).__name__}"
        logger.warning("Escalation webhook failed: %s", err)
    return result


def create_escalation(
    *,
    user_id: str,
    issue_description: str,
    user_consent: bool,
    trigger_type: str = "other",
    requester_name: str | None = None,
    diagnostic_steps: list[str] | str | None = None,
    urgency: str = "medium",
    preferred_language: str | None = "hi",
    follow_up_method: str | None = "voice_callback",
    contact_hint: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Create or update an escalation ticket after explicit consent.

    Security:
    - Refuses without user_consent
    - Scrubs all PII from free text before storage / dispatch
    - Dedupes active identical issues for the same user
    """
    if not user_consent:
        return {
            "ok": False,
            "status": "consent_denied",
            "created": False,
            "message": (
                "Escalation aborted: user did not consent to share the case summary. "
                "Offer self-service alternatives (bank branch, CSC, official portal, helpline)."
            ),
            "speak_out_loud_en": REFUSAL_SELF_SERVICE_EN,
            "speak_out_loud_hi": REFUSAL_SELF_SERVICE_HI,
        }

    clean_uid = (user_id or "").strip()
    if not clean_uid:
        return {
            "ok": False,
            "status": "invalid",
            "created": False,
            "message": "user_id is required to create an escalation.",
        }

    clean_issue = scrub_pii(issue_description)
    if not clean_issue:
        return {
            "ok": False,
            "status": "invalid",
            "created": False,
            "message": "A non-empty issue description is required.",
        }

    if isinstance(diagnostic_steps, str):
        try:
            parsed = json.loads(diagnostic_steps)
            steps: list[str] = (
                parsed if isinstance(parsed, list) else [diagnostic_steps]
            )
        except json.JSONDecodeError:
            steps = [s.strip() for s in diagnostic_steps.split(";") if s.strip()]
    else:
        steps = list(diagnostic_steps or [])

    trigger = (trigger_type or "other").strip().lower()
    if trigger not in {
        "fraud_suspected",
        "complex_decision",
        "user_requested",
        "other",
    }:
        trigger = "other"

    urg = (urgency or suggest_urgency(trigger, clean_issue)).lower()
    if urg not in VALID_URGENCIES:
        urg = "medium"

    summary = build_case_summary(
        requester_name=requester_name,
        user_id=clean_uid,
        issue_description=clean_issue,
        diagnostic_steps=steps,
        urgency=urg,
        preferred_language=preferred_language,
        follow_up_method=follow_up_method,
        trigger_type=trigger,
        contact_hint=contact_hint,
    )

    fp = issue_fingerprint(clean_uid, trigger, clean_issue)
    init_escalation_db(db_path)
    now = _now()

    existing = None
    if clean_uid and clean_uid.lower() != "caller":
        existing = find_active_duplicate(clean_uid, fp, db_path=db_path)
    if existing:
        # Update existing open/in_progress ticket instead of duplicating.
        ref = existing["reference_id"]
        with get_db_connection(db_path) as conn:
            conn.execute(
                """
                UPDATE escalations SET
                    issue_description = ?,
                    diagnostic_steps = ?,
                    urgency = ?,
                    preferred_language = COALESCE(?, preferred_language),
                    follow_up_method = COALESCE(?, follow_up_method),
                    contact_hint = COALESCE(?, contact_hint),
                    summary_json = ?,
                    updated_at = ?
                WHERE reference_id = ?
                """,
                (
                    summary["issue_description"],
                    json.dumps(summary["diagnostic_steps"]),
                    urg,
                    summary.get("preferred_language"),
                    summary.get("follow_up_method"),
                    summary.get("contact_hint") or None,
                    json.dumps(summary, ensure_ascii=False),
                    now,
                    ref,
                ),
            )
            conn.commit()

        updated = get_escalation(ref, db_path=db_path) or existing
        dispatch_payload = {
            "event": "escalation_updated",
            "reference_id": ref,
            "status": updated.get("status", "open"),
            "summary": summary,
        }
        hook = dispatch_webhook(dispatch_payload)
        next_steps = _next_steps_copy(ref, urg, updated=True)
        return {
            "ok": True,
            "created": False,
            "updated": True,
            "duplicate_prevented": True,
            "status": updated.get("status", "open"),
            "reference_id": ref,
            "summary": summary,
            "webhook": hook,
            "message": (
                f"An open case already existed for this issue. "
                f"Updated ticket {ref} instead of creating a duplicate."
            ),
            "next_steps": next_steps,
            # Use compact reference ID in chat + speech (not letter-by-letter).
            "speak_out_loud_en": (
                f"I found your existing case and updated it. Your reference ID is "
                f"{ref}. {next_steps['en']}"
            ),
            "speak_out_loud_hi": (
                f"Aapka pehle se open case mil gaya, maine update kar diya. "
                f"Aapka reference ID hai {ref}. {next_steps['hi']}"
            ),
        }

    ref = generate_reference_id()
    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO escalations (
                reference_id, user_id, requester_name, trigger_type,
                issue_description, diagnostic_steps, urgency,
                preferred_language, follow_up_method, contact_hint,
                issue_fingerprint, status, summary_json,
                webhook_dispatched, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, 0, ?, ?)
            """,
            (
                ref,
                clean_uid,
                summary.get("requester_name"),
                trigger,
                summary["issue_description"],
                json.dumps(summary["diagnostic_steps"]),
                urg,
                summary.get("preferred_language"),
                summary.get("follow_up_method"),
                summary.get("contact_hint") or None,
                fp,
                json.dumps(summary, ensure_ascii=False),
                now,
                now,
            ),
        )
        conn.commit()

    dispatch_payload = {
        "event": "escalation_created",
        "reference_id": ref,
        "status": "open",
        "summary": summary,
    }
    hook = dispatch_webhook(dispatch_payload)
    if hook.get("ok"):
        with get_db_connection(db_path) as conn:
            conn.execute(
                "UPDATE escalations SET webhook_dispatched = 1, updated_at = ? WHERE reference_id = ?",
                (now, ref),
            )
            conn.commit()

    next_steps = _next_steps_copy(ref, urg, updated=False)
    return {
        "ok": True,
        "created": True,
        "updated": False,
        "duplicate_prevented": False,
        "status": "open",
        "reference_id": ref,
        "summary": summary,
        "webhook": hook,
        "message": f"Escalation created with reference {ref}.",
        "next_steps": next_steps,
        # Compact ticket ID for both chat transcript and TTS (e.g. JS-3FC81621).
        "speak_out_loud_en": (
            f"Thank you. I have escalated your case to our specialist team. "
            f"Your reference ID is {ref}. {next_steps['en']}"
        ),
        "speak_out_loud_hi": (
            f"Dhanyavad. Maine aapka case specialist team ko bhej diya hai. "
            f"Aapka reference ID hai {ref}. {next_steps['hi']}"
        ),
    }


def update_escalation_status(
    reference_id: str,
    status: str,
    *,
    resolution_notes: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Move ticket between open / in_progress / resolved."""
    st = (status or "").strip().lower()
    if st not in VALID_STATUSES:
        return {
            "ok": False,
            "message": f"Invalid status '{status}'. Use open, in_progress, or resolved.",
        }
    ticket = get_escalation(reference_id, db_path=db_path)
    if not ticket:
        return {"ok": False, "message": f"No escalation found for {reference_id}."}

    now = _now()
    resolved_at = now if st == "resolved" else ticket.get("resolved_at")
    notes = (
        scrub_pii(resolution_notes)
        if resolution_notes
        else ticket.get("resolution_notes")
    )

    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE escalations SET
                status = ?,
                resolution_notes = ?,
                resolved_at = ?,
                updated_at = ?
            WHERE reference_id = ?
            """,
            (st, notes, resolved_at, now, ticket["reference_id"]),
        )
        conn.commit()

    updated = get_escalation(ticket["reference_id"], db_path=db_path)
    dispatch_webhook(
        {
            "event": "escalation_status_changed",
            "reference_id": ticket["reference_id"],
            "status": st,
            "resolution_notes": notes,
            "summary": (updated or {}).get("summary"),
        }
    )
    return {"ok": True, "ticket": updated}


def mark_callback_dispatched(
    reference_id: str, db_path: Path | str | None = None
) -> None:
    ticket = get_escalation(reference_id, db_path=db_path)
    if not ticket:
        return
    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE escalations
            SET callback_dispatched = 1, updated_at = ?
            WHERE reference_id = ?
            """,
            (_now(), ticket["reference_id"]),
        )
        conn.commit()


def resolve_and_prepare_callback(
    reference_id: str,
    *,
    resolution_notes: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Mark resolved and return metadata for outbound / Linphone notify."""
    result = update_escalation_status(
        reference_id,
        "resolved",
        resolution_notes=resolution_notes,
        db_path=db_path,
    )
    if not result.get("ok"):
        return result
    ticket = result["ticket"]
    callback_meta = {
        "purpose": "escalation_resolution",
        "reference_id": ticket["reference_id"],
        "caller_name": ticket.get("requester_name") or "Caller",
        "language": ticket.get("preferred_language") or "hi",
        "follow_up_method": ticket.get("follow_up_method") or "voice_callback",
        "contact_hint": ticket.get("contact_hint"),
        "resolution_notes": scrub_pii(
            resolution_notes or ticket.get("resolution_notes") or ""
        ),
        "issue_description": ticket.get("issue_description"),
        "user_id": ticket.get("user_id"),
    }
    return {
        "ok": True,
        "ticket": ticket,
        "callback": callback_meta,
        "message": (
            f"Case {ticket['reference_id']} resolved. "
            "Use outbound dial / Linphone with purpose=escalation_resolution to notify."
        ),
    }


# ---------------------------------------------------------------------------
# Speak helpers
# ---------------------------------------------------------------------------


def _speak_ref(ref: str) -> str:
    """Spell reference for TTS clarity: JS-A1B2C3D4 → J S dash A 1 B 2…"""
    parts: list[str] = []
    for ch in ref:
        if ch == "-":
            parts.append("dash")
        else:
            parts.append(ch)
    return " ".join(parts)


def _next_steps_copy(ref: str, urgency: str, *, updated: bool) -> dict[str, str]:
    """Realistic next steps — never promise instant live-agent pickup."""
    sla = {
        "emergency": "within a few hours during operational windows",
        "high": "within one business day",
        "medium": "within one to two business days",
        "low": "within two to three business days",
    }.get(urgency, "within one to two business days")

    verb = "updated" if updated else "logged"
    en = (
        f"A specialist will review your {verb} case {sla}. "
        f"Please keep reference {ref} handy. "
        "This is not an immediate live transfer — you will be contacted "
        "using your preferred follow-up method when a specialist is available."
    )
    hi = (
        f"Specialist aapka {('update kiya' if updated else 'naya')} case "
        f"lagbhag {sla} mein review karega. "
        f"Reference {ref} savdhan se rakhie. "
        "Yeh turant live agent transfer nahi hai — specialist available hone par "
        "aapke preferred follow-up method se contact hoga."
    )
    return {"en": en, "hi": hi, "sla_band": sla}


def consent_prompt(language: str | None = "hi") -> str:
    lang = (language or "hi").lower()
    return CONSENT_PROMPT_EN if lang.startswith("en") else CONSENT_PROMPT_HI


def refusal_self_service(language: str | None = "hi") -> str:
    lang = (language or "hi").lower()
    return REFUSAL_SELF_SERVICE_EN if lang.startswith("en") else REFUSAL_SELF_SERVICE_HI
