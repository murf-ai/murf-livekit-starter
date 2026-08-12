"""Day 7 — Escalation framework unit tests.

Covers:
  1. Successful escalation (fraud + complex decision)
  2. Standard non-escalated path (scheme questions)
  3. Denied consent scenario
  Plus: PII scrub, duplicate prevention, status tracking, resolution callback.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import escalation
from agent import (
    Assistant,
    _is_consent_no,
    _is_consent_yes,
    _prepare_pending_escalation,
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_escalations.db"
    escalation.init_escalation_db(db_file)
    return db_file


# ---------------------------------------------------------------------------
# Trigger detection
# ---------------------------------------------------------------------------


def test_trigger_a_fraud_suspected():
    samples = [
        "I think there is fraud on my account",
        "Unauthorized transaction happened yesterday",
        "Someone accessed my account without permission",
        "Mera account pe dhokha hua, chori ho gayi",
        "Suspicious debit that I did not authorize",
    ]
    for text in samples:
        assert escalation.detect_escalation_trigger(text) == "fraud_suspected", text


def test_trigger_b_complex_decision():
    samples = [
        "I need a limit override on my card",
        "Please escalate this transaction dispute",
        "My claim is stuck and rejected, I need a supervisor",
        "I want to speak to a human agent about settlement",
        "Refund nahi aa raha, complaint register karo",
    ]
    for text in samples:
        assert escalation.detect_escalation_trigger(text) == "complex_decision", text


def test_non_escalated_path_no_trigger():
    """Ordinary scheme / literacy questions must NOT escalate."""
    samples = [
        "Tell me about PMJDY",
        "Am I eligible for PMSBY if I am 32?",
        "What documents do I need for APY?",
        "How do I open a bank account?",
        "UPI safety tips please",
        "Namaste, government schemes batao",
    ]
    for text in samples:
        assert escalation.detect_escalation_trigger(text) is None, text


def test_generic_hack_question_is_not_account_fraud():
    """Avoid false-positive escalation on general 'how to hack' questions."""
    assert (
        escalation.detect_escalation_trigger(
            "How can I hack into someone's computer without permission?"
        )
        is None
    )


# ---------------------------------------------------------------------------
# PII sanitization
# ---------------------------------------------------------------------------


def test_scrub_pii_removes_secrets():
    dirty = (
        "OTP is 123456 and PIN 4321, password=Secret@1, "
        "CVV 987, account 1234567890123456, "
        "Aadhaar 9999 8888 7777, PAN ABCDE1234F"
    )
    clean = escalation.scrub_pii(dirty)
    assert "123456" not in clean
    assert "4321" not in clean
    assert "Secret@1" not in clean
    assert "987" not in clean or "REDACTED" in clean
    assert "1234567890123456" not in clean
    assert "9999 8888 7777" not in clean
    assert "ABCDE1234F" not in clean
    assert "REDACTED" in clean


def test_build_case_summary_excludes_forbidden_fields():
    summary = escalation.build_case_summary(
        requester_name="Ramesh",
        user_id="ramesh",
        issue_description="Fraud report; OTP was 654321 on account 998877665544",
        diagnostic_steps=["Asked about unauthorized debit", "Did not request OTP"],
        urgency="high",
        preferred_language="en",
        follow_up_method="voice_callback",
        trigger_type="fraud_suspected",
    )
    blob = json.dumps(summary)
    assert "654321" not in blob
    assert "998877665544" not in blob
    assert summary["urgency"] == "high"
    assert summary["requester_name"] == "Ramesh"
    assert summary["trigger_type"] == "fraud_suspected"
    assert "pii_policy" in summary


# ---------------------------------------------------------------------------
# 1) Successful escalation path
# ---------------------------------------------------------------------------


def test_successful_fraud_escalation_with_consent(temp_db):
    result = escalation.create_escalation(
        user_id="ramesh",
        requester_name="Ramesh",
        issue_description="Unauthorized login and suspicious debit on my account",
        user_consent=True,
        trigger_type="fraud_suspected",
        diagnostic_steps=[
            "Caller reported unauthorized access",
            "Agent did not request OTP or PIN",
            "Consent granted to share summary",
        ],
        urgency="high",
        preferred_language="en",
        follow_up_method="voice_callback",
        db_path=temp_db,
    )
    assert result["ok"] is True
    assert result["created"] is True
    assert result["status"] == "open"
    assert result["reference_id"].startswith("JS-")
    assert "speak_out_loud_en" in result
    assert result["reference_id"] in result["speak_out_loud_en"]
    # Must show compact ticket ID, not letter-spelled "J S dash …"
    assert "dash" not in result["speak_out_loud_en"].lower()
    assert f"reference ID is {result['reference_id']}" in result["speak_out_loud_en"]
    assert "immediate live" in result["speak_out_loud_en"].lower() or (
        "not an immediate" in result["next_steps"]["en"].lower()
    )
    # Persist + lookup
    ticket = escalation.get_escalation(result["reference_id"], db_path=temp_db)
    assert ticket is not None
    assert ticket["status"] == "open"
    assert ticket["trigger_type"] == "fraud_suspected"
    assert ticket["urgency"] == "high"


def test_successful_complex_decision_escalation(temp_db):
    result = escalation.create_escalation(
        user_id="priya",
        requester_name="Priya",
        issue_description="Need limit override and transaction dispute review",
        user_consent=True,
        trigger_type="complex_decision",
        urgency="medium",
        preferred_language="hi",
        db_path=temp_db,
    )
    assert result["ok"] is True
    assert result["created"] is True
    assert result["reference_id"]
    assert "speak_out_loud_hi" in result
    assert result["summary"]["urgency"] == "medium"


# ---------------------------------------------------------------------------
# 3) Denied consent
# ---------------------------------------------------------------------------


def test_denied_consent_aborts_escalation(temp_db):
    result = escalation.create_escalation(
        user_id="amit",
        requester_name="Amit",
        issue_description="Fraud on account",
        user_consent=False,
        trigger_type="fraud_suspected",
        db_path=temp_db,
    )
    assert result["ok"] is False
    assert result["created"] is False
    assert result["status"] == "consent_denied"
    assert (
        "self-service" in result["message"].lower()
        or "consent" in result["message"].lower()
    )
    assert result["speak_out_loud_en"]
    # No ticket stored
    open_tickets = escalation.list_escalations(
        user_id="amit", status="open", db_path=temp_db
    )
    assert open_tickets == []


def test_consent_helpers_yes_no():
    assert _is_consent_yes("yes")
    assert _is_consent_yes("haan ji")
    assert _is_consent_yes("sure, go ahead")
    assert _is_consent_no("no")
    assert _is_consent_no("nahi")
    assert _is_consent_no("don't share")
    assert _is_consent_no("mat bhejo")
    assert not _is_consent_yes("no thanks")
    assert not _is_consent_no("yes please")


# ---------------------------------------------------------------------------
# Duplicate prevention + status tracking + resolution callback
# ---------------------------------------------------------------------------


def test_duplicate_prevention_updates_existing(temp_db):
    issue = "Unauthorized transaction dispute on savings account"
    first = escalation.create_escalation(
        user_id="neha",
        requester_name="Neha",
        issue_description=issue,
        user_consent=True,
        trigger_type="fraud_suspected",
        urgency="high",
        diagnostic_steps=["Initial report"],
        db_path=temp_db,
    )
    second = escalation.create_escalation(
        user_id="neha",
        requester_name="Neha",
        issue_description=issue,
        user_consent=True,
        trigger_type="fraud_suspected",
        urgency="emergency",
        diagnostic_steps=["Initial report", "Caller called again with more detail"],
        db_path=temp_db,
    )
    assert first["ok"] and second["ok"]
    assert first["reference_id"] == second["reference_id"]
    assert second["created"] is False
    assert second["updated"] is True
    assert second["duplicate_prevented"] is True
    ticket = escalation.get_escalation(first["reference_id"], db_path=temp_db)
    assert ticket["urgency"] == "emergency"
    open_list = escalation.list_escalations(
        user_id="neha", status="open", db_path=temp_db
    )
    assert len(open_list) == 1


def test_status_tracking_and_resolution_callback(temp_db):
    created = escalation.create_escalation(
        user_id="vijay",
        requester_name="Vijay",
        issue_description="Complex claim stuck after rejection",
        user_consent=True,
        trigger_type="complex_decision",
        preferred_language="en",
        follow_up_method="voice_callback",
        contact_hint="linphone:vijay",
        db_path=temp_db,
    )
    ref = created["reference_id"]

    mid = escalation.update_escalation_status(ref, "in_progress", db_path=temp_db)
    assert mid["ok"] is True
    assert mid["ticket"]["status"] == "in_progress"

    resolved = escalation.resolve_and_prepare_callback(
        ref,
        resolution_notes="Specialist verified claim documents; no further action.",
        db_path=temp_db,
    )
    assert resolved["ok"] is True
    assert resolved["ticket"]["status"] == "resolved"
    cb = resolved["callback"]
    assert cb["purpose"] == "escalation_resolution"
    assert cb["reference_id"] == ref
    assert cb["caller_name"] == "Vijay"
    assert cb["language"] == "en"
    assert "OTP" not in (cb.get("resolution_notes") or "")


def test_webhook_dispatch_local_log(temp_db, tmp_path, monkeypatch):
    # Force local-only path (no external URL)
    monkeypatch.delenv("ESCALATION_WEBHOOK_URL", raising=False)
    with patch.object(
        escalation,
        "DEFAULT_DB_PATH",
        tmp_path / "caller_memory.db",
    ):
        result = escalation.create_escalation(
            user_id="local_user",
            issue_description="Fraud suspected on UPI",
            user_consent=True,
            trigger_type="fraud_suspected",
            db_path=temp_db,
        )
    assert result["ok"] is True
    assert result["webhook"]["ok"] is True


# ---------------------------------------------------------------------------
# Agent helpers / pending draft
# ---------------------------------------------------------------------------


def test_prepare_pending_escalation_scrubs_and_sets_trigger():
    pending = _prepare_pending_escalation(
        "There is fraud, my OTP was 112233",
        "en",
        "Ramesh",
    )
    assert pending["trigger_type"] == "fraud_suspected"
    assert pending["urgency"] in {"high", "emergency"}
    assert "112233" not in pending["issue_description"]
    assert pending["requester_name"] == "Ramesh"
    assert pending["follow_up_method"] == "voice_callback"


def test_assistant_has_create_escalation_tool():
    agent = Assistant()
    assert hasattr(agent, "create_escalation")
    assert agent._awaiting_escalation_consent is False
    assert agent._pending_escalation is None


def test_urgency_guide():
    assert escalation.suggest_urgency("fraud_suspected", "stolen phone") == "high"
    assert (
        escalation.suggest_urgency("fraud_suspected", "emergency ongoing fraud")
        == "emergency"
    )
    assert escalation.suggest_urgency("complex_decision", "dispute") == "medium"
    assert escalation.suggest_urgency("other", "hello") == "low"


def test_consent_and_refusal_prompts_bilingual():
    assert "permission" in escalation.consent_prompt("en").lower()
    assert "anumati" in escalation.consent_prompt("hi").lower()
    assert "self-service" in escalation.refusal_self_service("en").lower()
    assert "escalation nahi" in escalation.refusal_self_service("hi").lower()


def test_outbound_resolution_greeting_mentions_reference():
    """Day 7 Linphone greeting must include reference + stop instruction."""
    from telephony.outbound.agent import build_greeting

    en = build_greeting(
        {
            "purpose": "escalation_resolution",
            "caller_name": "Ramesh",
            "language": "en",
            "reference_id": "JS-ABCD1234",
            "resolution_notes": "No further unauthorized activity found.",
        }
    )
    assert "Jan Sahay" in en
    assert "JS-ABCD1234" in en
    assert "dash" not in en.lower() or "JS-ABCD1234" in en
    assert "stop calling" in en.lower()
    assert "OTP" in en  # safety line mentions we will not ask

    hi = build_greeting(
        {
            "purpose": "escalation_resolution",
            "caller_name": "Priya",
            "language": "hi",
            "reference_id": "JS-ZZZZ9999",
            "resolution_notes": "Case closed by specialist.",
        }
    )
    assert "जन सहाय" in hi or "Jan Sahay" in hi
    assert "JS-ZZZZ9999" in hi


def test_lost_card_triggers_fraud_escalation():
    assert (
        escalation.detect_escalation_trigger("I lost my credit card.")
        == "fraud_suspected"
    )


def test_welcome_back_line_includes_topic_and_ticket():
    from agent import _welcome_back_line

    caller = {
        "name": "Sam",
        "facts": {
            "last_topic": "fraud / unauthorized access",
            "last_escalation_ref": "JS-3FC81621",
            "last_escalation_status": "open",
        },
    }
    en = _welcome_back_line(caller, "en")
    assert "Sam" in en
    assert "fraud" in en.lower() or "unauthorized" in en.lower()
    assert "JS-3FC81621" in en
    assert "dash" not in en.lower()


def test_unknown_caller_creates_new_ticket_no_dedupe(temp_db):
    first = escalation.create_escalation(
        user_id="caller",
        requester_name="Caller",
        issue_description="I lost my credit card.",
        user_consent=True,
        trigger_type="fraud_suspected",
        urgency="high",
        db_path=temp_db,
    )
    second = escalation.create_escalation(
        user_id="caller",
        requester_name="Caller",
        issue_description="I lost my credit card.",
        user_consent=True,
        trigger_type="fraud_suspected",
        urgency="high",
        db_path=temp_db,
    )
    assert first["ok"] is True
    assert second["ok"] is True
    assert first["reference_id"] != second["reference_id"]
    assert second["created"] is True
    assert second["updated"] is False
    assert second["duplicate_prevented"] is False

    open_tickets = escalation.list_escalations(
        user_id="caller", status="open", db_path=temp_db
    )
    assert len(open_tickets) == 2


def test_case_recall_helpers():
    from agent import (
        _format_ticket_status_response,
        _wants_case_recall,
        extract_ticket_ref,
    )

    assert _wants_case_recall("any progress on my case?") is True
    assert _wants_case_recall("Do you remember my case?") is True
    assert _wants_case_recall("case status check") is True
    assert _wants_case_recall("mera case yaad hai?") is True
    assert _wants_case_recall("status of JS-12345678") is True
    assert _wants_case_recall("tell me about APY scheme") is False

    assert extract_ticket_ref("My case ref is JS-ABCD1234") == "JS-ABCD1234"
    assert extract_ticket_ref("My case ref is js-abcd1234") == "JS-ABCD1234"
    assert extract_ticket_ref("no ref here") is None

    ticket = {
        "reference_id": "JS-12345678",
        "status": "resolved",
        "resolution_notes": "Refund credited.",
        "urgency": "medium",
        "issue_description": "dispute",
    }
    resp_en = _format_ticket_status_response(ticket, "en", "Sam")
    assert "Sam" in resp_en
    assert "JS-12345678" in resp_en
    assert "resolved" in resp_en
    assert "Refund credited." in resp_en

    resp_hi = _format_ticket_status_response(ticket, "hi", "Priya")
    assert "Priya" in resp_hi
    assert "JS-12345678" in resp_hi
    assert "resolve" in resp_hi
    assert "Refund credited." in resp_hi


@pytest.mark.asyncio
async def test_case_recall_intercept_end_to_end(temp_db, monkeypatch):
    import agent

    monkeypatch.setattr(escalation, "DEFAULT_DB_PATH", temp_db)
    assistant = agent.Assistant()
    assistant._known_caller_name = "Sam"
    assistant._reply_lang = "en"

    # Create a ticket in the DB for user "sam"
    result = escalation.create_escalation(
        user_id="sam",
        requester_name="Sam",
        issue_description="lost card dispute",
        user_consent=True,
        trigger_type="fraud_suspected",
        db_path=temp_db,
    )
    ref_id = result["reference_id"]

    spoken_phrases = []

    class MockSession:
        async def say(self, text, allow_interruptions=True):
            spoken_phrases.append(text)

    monkeypatch.setattr(
        agent.Assistant, "session", property(lambda self: MockSession())
    )

    class MockMessage:
        def __init__(self, content):
            self.text_content = content
            self.role = "user"

    class MockChatContext:
        def __init__(self):
            self.messages = []
            self.items = []

        def add_message(self, role, content):
            self.messages.append({"role": role, "content": content})

    # Mock apply_language
    async def mock_apply_language(*args, **kwargs):
        return "en"

    monkeypatch.setattr(assistant, "apply_language", mock_apply_language)

    # Turn 1: User says "any progress on my case?"
    ctx = MockChatContext()
    msg = MockMessage("any progress on my case?")
    with pytest.raises(agent.StopResponse):
        await assistant.on_user_turn_completed(ctx, msg)

    assert len(spoken_phrases) == 1
    assert ref_id in spoken_phrases[0]
    assert "is currently open" in spoken_phrases[0]
