"""Manager Approval & Fake Bank Account Management for Jan Sahay.

Handles:
- Account creation / registration requests ("I want to add my account")
- Safe Key storage and activation requests
- Manager Approval Queue (Account Activations, Transactions & Money Transfers)
- Manual approval / rejection by bank manager from the dashboard
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import db

logger = logging.getLogger("agent.manager")

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "caller_memory.db"

RequestType = Literal["ACCOUNT_ACTIVATION", "TRANSACTION_TRANSFER"]
RequestStatus = Literal["PENDING_APPROVAL", "APPROVED", "REJECTED"]


def _get_conn(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = Path(db_path) if db_path else DEFAULT_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_manager_db(db_path: Path | str | None = None) -> None:
    """Initialize manager_approvals table if missing."""
    with _get_conn(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS manager_approvals (
                request_id TEXT PRIMARY KEY,
                request_type TEXT NOT NULL,
                requester_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                safe_key TEXT,
                details_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL',
                resolution_notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_manager_status
            ON manager_approvals (status, created_at DESC)
            """
        )
        conn.commit()
    logger.info("Manager approval database ready.")


def create_manager_request(
    *,
    request_type: RequestType,
    requester_name: str,
    safe_key: str | None = None,
    details: dict[str, Any] | None = None,
    user_id: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Create a new manager approval request (Account activation or Transaction)."""
    init_manager_db(db_path)

    clean_name = (requester_name or "Applicant").strip()
    clean_uid = user_id or clean_name.lower().replace(" ", "_")
    req_id = f"MR-{uuid.uuid4().hex[:8].upper()}"
    now = _now()
    details_dict = details or {}

    with _get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO manager_approvals (
                request_id, request_type, requester_name, user_id,
                safe_key, details_json, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING_APPROVAL', ?, ?)
            """,
            (
                req_id,
                request_type,
                clean_name,
                clean_uid,
                (safe_key or "").strip(),
                json.dumps(details_dict, ensure_ascii=False),
                now,
                now,
            ),
        )
        conn.commit()

    logger.info(
        "Manager request created: id=%s type=%s name=%s",
        req_id,
        request_type,
        clean_name,
    )

    return {
        "ok": True,
        "request_id": req_id,
        "request_type": request_type,
        "requester_name": clean_name,
        "safe_key": safe_key,
        "status": "PENDING_APPROVAL",
        "created_at": now,
    }


def list_manager_requests(
    status: str | None = None,
    request_type: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List requests for the Manager Portal dashboard."""
    init_manager_db(db_path)
    where_clauses = []
    params = []

    if status:
        where_clauses.append("status = ?")
        params.append(status.upper())
    if request_type:
        where_clauses.append("request_type = ?")
        params.append(request_type.upper())

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with _get_conn(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM manager_approvals {where} ORDER BY created_at DESC",
            params,
        ).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        try:
            item["details"] = json.loads(item["details_json"])
        except (json.JSONDecodeError, TypeError):
            item["details"] = {}
        result.append(item)

    return result


def approve_manager_request(
    request_id: str,
    resolution_notes: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Approve a request (Activates account or executes transaction)."""
    init_manager_db(db_path)
    now = _now()

    with _get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM manager_approvals WHERE request_id = ?",
            (request_id.strip(),),
        ).fetchone()

        if not row:
            return {"ok": False, "message": f"No request found for {request_id}"}

        notes = resolution_notes or "Approved by Manager"
        conn.execute(
            """
            UPDATE manager_approvals SET
                status = 'APPROVED',
                resolution_notes = ?,
                updated_at = ?
            WHERE request_id = ?
            """,
            (notes, now, request_id),
        )
        conn.commit()

        # If it was an ACCOUNT_ACTIVATION, activate the caller profile in DB
        if row["request_type"] == "ACCOUNT_ACTIVATION":
            user_id = row["user_id"]
            name = row["requester_name"]
            safe_key = row["safe_key"]
            try:
                db.save_caller(
                    user_id=user_id,
                    name=name,
                    consent_given=True,
                    facts={
                        "account_active": True,
                        "safe_key": safe_key,
                        "activated_at": now,
                        "activated_by": "Manager X",
                    },
                    db_path=db_path,
                )
                logger.info("Account %s activated by Manager approval", name)
            except Exception as err:
                logger.warning("Could not activate caller profile in DB: %s", err)

    return {
        "ok": True,
        "request_id": request_id,
        "status": "APPROVED",
        "message": f"Request {request_id} has been APPROVED.",
    }


def reject_manager_request(
    request_id: str,
    resolution_notes: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Reject a manager request."""
    init_manager_db(db_path)
    now = _now()

    with _get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM manager_approvals WHERE request_id = ?",
            (request_id.strip(),),
        ).fetchone()

        if not row:
            return {"ok": False, "message": f"No request found for {request_id}"}

        notes = resolution_notes or "Rejected by Manager"
        conn.execute(
            """
            UPDATE manager_approvals SET
                status = 'REJECTED',
                resolution_notes = ?,
                updated_at = ?
            WHERE request_id = ?
            """,
            (notes, now, request_id),
        )
        conn.commit()

    return {
        "ok": True,
        "request_id": request_id,
        "status": "REJECTED",
        "message": f"Request {request_id} has been REJECTED.",
    }


def update_manager_request(
    request_id: str,
    *,
    status: RequestStatus | None = None,
    resolution_notes: str | None = None,
    details: dict[str, Any] | None = None,
    safe_key: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Update status, notes, or details of an existing request."""
    init_manager_db(db_path)
    now = _now()
    updates = []
    params = []

    if status:
        updates.append("status = ?")
        params.append(status)
    if resolution_notes:
        updates.append("resolution_notes = ?")
        params.append(resolution_notes)
    if safe_key is not None:
        updates.append("safe_key = ?")
        params.append(safe_key)
    if details:
        updates.append("details_json = ?")
        params.append(json.dumps(details, ensure_ascii=False))

    if not updates:
        return {"ok": False, "message": "No updates specified"}

    updates.append("updated_at = ?")
    params.append(now)
    params.append(request_id)

    with _get_conn(db_path) as conn:
        conn.execute(
            f"UPDATE manager_approvals SET {', '.join(updates)} WHERE request_id = ?",
            params,
        )
        conn.commit()
    return {"ok": True, "request_id": request_id}
