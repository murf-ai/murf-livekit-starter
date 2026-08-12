#!/usr/bin/env python3
"""Day 7 mock scenarios for Jan Sahay human escalation (no LiveKit required).

Runs three curriculum paths end-to-end against the local SQLite escalation store:

  1. Successful escalation (fraud / complex decision) with consent
  2. Standard non-escalated path (scheme question — no ticket)
  3. Denied consent (abort + self-service copy)

Usage (from backend/):
    uv run python scripts/demo_escalation_scenarios.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

import escalation  # noqa: E402


def _banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def scenario_1_successful_fraud(db_path: Path) -> None:
    _banner("SCENARIO 1 — Successful escalation (Trigger A: fraud)")
    user_text = (
        "There is fraud on my account — unauthorized login and a suspicious debit. "
        "OTP was 445566 but do not store that."
    )
    trigger = escalation.detect_escalation_trigger(user_text)
    print(f"Detected trigger: {trigger}")
    assert trigger == "fraud_suspected"

    print("Consent gate:", escalation.consent_prompt("en"))
    print("Caller: yes, you have my permission.")

    result = escalation.create_escalation(
        user_id="ramesh_demo",
        requester_name="Ramesh",
        issue_description=user_text,
        user_consent=True,
        trigger_type=trigger,
        diagnostic_steps=[
            "Caller reported unauthorized login + suspicious debit",
            "Agent refused to collect OTP/PIN",
            "Explicit consent granted for specialist handoff",
        ],
        urgency=escalation.suggest_urgency(trigger, user_text),
        preferred_language="en",
        follow_up_method="voice_callback",
        contact_hint="linphone:ramesh",
        db_path=db_path,
    )
    print(json.dumps({k: result[k] for k in result if k != "summary"}, indent=2))
    print("Summary (PII-scrubbed):", json.dumps(result["summary"], indent=2))
    assert result["ok"] and result["reference_id"]
    print("Agent speaks:", result["speak_out_loud_en"])


def scenario_2_non_escalated(db_path: Path) -> None:
    _banner("SCENARIO 2 — Non-escalated path (ordinary scheme question)")
    user_text = "Tell me about PMSBY eligibility and documents."
    trigger = escalation.detect_escalation_trigger(user_text)
    print(f"User: {user_text}")
    print(f"Detected trigger: {trigger}")
    assert trigger is None
    before = escalation.list_escalations(db_path=db_path)
    print(
        f"Open tickets unchanged count={len(before)} — agent answers with scheme tools."
    )
    print(
        "Agent (mock): PMSBY is accidental insurance at about twenty rupees a year. "
        "I can check eligibility if you share your age — no human escalation needed."
    )


def scenario_3_denied_consent(db_path: Path) -> None:
    _banner("SCENARIO 3 — Denied consent (Trigger B: complex decision)")
    user_text = "I need a limit override and want this transaction dispute escalated."
    trigger = escalation.detect_escalation_trigger(user_text)
    print(f"Detected trigger: {trigger}")
    assert trigger == "complex_decision"
    print("Consent gate:", escalation.consent_prompt("hi"))
    print("Caller: nahi, mat bhejo.")

    result = escalation.create_escalation(
        user_id="priya_demo",
        requester_name="Priya",
        issue_description=user_text,
        user_consent=False,
        trigger_type=trigger,
        preferred_language="hi",
        db_path=db_path,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    assert result["status"] == "consent_denied"
    assert not escalation.list_escalations(
        user_id="priya_demo", status="open", db_path=db_path
    )
    print("Agent speaks:", result["speak_out_loud_hi"])


def scenario_bonus_resolve_callback(db_path: Path) -> None:
    _banner("BONUS — Resolve + prepare Linphone callback metadata")
    created = escalation.create_escalation(
        user_id="ramesh_demo",
        requester_name="Ramesh",
        issue_description="Unauthorized login follow-up",
        user_consent=True,
        trigger_type="fraud_suspected",
        preferred_language="en",
        db_path=db_path,
    )
    # May update duplicate from scenario 1
    ref = created["reference_id"]
    escalation.update_escalation_status(ref, "in_progress", db_path=db_path)
    resolved = escalation.resolve_and_prepare_callback(
        ref,
        resolution_notes="Specialist confirmed no further unauthorized activity.",
        db_path=db_path,
    )
    print(json.dumps(resolved["callback"], indent=2))
    print(
        "Next: uv run python src/telephony/outbound/resolve_notify.py "
        f"--ref {ref} --to $LINPHONE_SIP_URI --dry-run"
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "demo_escalations.db"
        escalation.init_escalation_db(db_path)
        scenario_1_successful_fraud(db_path)
        scenario_2_non_escalated(db_path)
        scenario_3_denied_consent(db_path)
        scenario_bonus_resolve_callback(db_path)
        _banner("ALL DAY 7 MOCK SCENARIOS PASSED")


if __name__ == "__main__":
    main()
