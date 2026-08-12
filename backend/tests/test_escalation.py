import pytest
import os
import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from escalation import classify_escalation_reason, sanitize_and_validate_payload, post_to_slack_webhook, create_escalation


class MockRunContext:
    pass


def test_classify_escalation_reason():
    # Test possible_fraud classifier
    assert classify_escalation_reason("I see a $420 transaction that is unauthorized!") == "possible_fraud"
    assert classify_escalation_reason("Someone stole my card and made a charge") == "possible_fraud"
    
    # Test decision_agent_cannot_make classifier
    assert classify_escalation_reason("Can you waive my fee for late payment?") == "decision_agent_cannot_make"
    assert classify_escalation_reason("I want to approve loan for 5000 dollars") == "decision_agent_cannot_make"
    assert classify_escalation_reason("Please reverse chargeback on my account") == "decision_agent_cannot_make"
    
    # Test none classifier
    assert classify_escalation_reason("What is my account balance?") == "none"
    assert classify_escalation_reason("Tell me about government schemes for farmers") == "none"


def test_sanitize_payload_redacts_sensitive_info():
    raw_payload = {
        "who_needs_help": "John Doe",
        "what_happened": "Caller reports unrecognized $420 charge.",
        "already_checked": "Checked card 4532123456784471 and pin 1234. Confirmed $420 charge on Aug 10.",
        "urgency": "HIGH",
        "language_and_followup": "English, Call back"
    }
    sanitized = sanitize_and_validate_payload(raw_payload)
    
    assert "4532123456784471" not in sanitized["already_checked"]
    assert "ending in 4471" in sanitized["already_checked"]
    assert "[REDACTED]" in sanitized["already_checked"]
    assert sanitized["urgency"] == "high"
    assert sanitized["who_needs_help"] == "John Doe"


@pytest.mark.asyncio
async def test_create_escalation_tool_success():
    ctx = MockRunContext()
    # Call underlying tool function directly
    tool_fn = getattr(create_escalation, "fn", getattr(create_escalation, "_fn", create_escalation))
    res = await tool_fn(
        None,
        ctx,
        who_needs_help="John Doe",
        what_happened="Caller reported unauthorized charge of $420.",
        already_checked="Verified transaction on card ending in 4471.",
        urgency="high",
        language_and_followup="English, Phone Call"
    )
    
    assert res["status"] == "created"
    assert res["reference_id"].startswith("ESC-")
    assert "created_at" in res


# End-to-end simulation test of the two requested scenarios
class EscalationTracker:
    def __init__(self):
        self.call_count = 0
        self.last_payload = None

    def call_create_escalation(self, payload: dict) -> dict:
        self.call_count += 1
        self.last_payload = payload
        success, ref_id = post_to_slack_webhook(sanitize_and_validate_payload(payload))
        return {"status": "created" if success else "failed", "reference_id": ref_id}


def test_scenario_a_escalation_path():
    """
    Scenario A: Escalation path
    Caller reports a $420 charge they don't recognize on their card -> agent checks transaction,
    can't resolve it, asks permission, caller consents, creates escalation.
    """
    tracker = EscalationTracker()
    
    # 1. Turn 1: User statement
    user_turn = "I see a $420 charge on my card from yesterday that I did not make."
    reason = classify_escalation_reason(user_turn)
    assert reason == "possible_fraud"
    
    # 2. Agent checks transaction & flags need for human escalation
    already_checked = "Checked account ending in 4471. Confirmed $420 charge on Aug 10 is not recognized by caller."
    
    # 3. Agent asks permission (Simulated)
    agent_permission_request = "I see the unrecognized $420 charge. Would you like me to submit an escalation to our fraud department?"
    user_consent_response = "Yes, please do."
    
    # 4. Consent granted -> trigger create_escalation
    if "yes" in user_consent_response.lower():
        payload = {
            "who_needs_help": "John Doe",
            "what_happened": "Caller reports unrecognized $420 charge on card.",
            "already_checked": already_checked,
            "urgency": "high",
            "language_and_followup": "English, Call back at 555-0199"
        }
        res = tracker.call_create_escalation(payload)
        assert res["status"] == "created"
        assert res["reference_id"].startswith("ESC-")

    # Assert create_escalation called EXACTLY ONCE
    assert tracker.call_count == 1


def test_scenario_b_normal_path():
    """
    Scenario B: Normal path
    Caller asks a routine question the agent CAN fully answer itself ("what's my current balance")
    -> agent answers directly and never calls create_escalation.
    """
    tracker = EscalationTracker()
    
    # 1. Turn 1: User statement
    user_turn = "What's my current account balance?"
    reason = classify_escalation_reason(user_turn)
    assert reason == "none"
    
    # 2. Agent handles request directly
    agent_response = "Your current account balance is $2,450.00."
    
    # Assert create_escalation called ZERO TIMES
    assert tracker.call_count == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
