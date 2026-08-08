from agent_config import (
    CALL_OBJECTIVES,
    ESCALATION_SCRIPT,
    FIRST_TURN_GREETING,
    GUARDRAILS,
    KNOWLEDGE_BOUNDARIES,
    LANGUAGE_POLICY,
    STT_LANGUAGE,
    SYSTEM_PROMPT,
)


def test_day2_defines_two_to_three_call_objectives() -> None:
    assert len(CALL_OBJECTIVES) == 3
    assert any("collect request" in objective for objective in CALL_OBJECTIVES)
    assert any("OTP" in objective for objective in CALL_OBJECTIVES)
    assert any("report" in objective for objective in CALL_OBJECTIVES)


def test_day2_guardrails_cover_refusals_never_claims_and_escalation() -> None:
    assert "refuse" in GUARDRAILS
    assert "never_claim" in GUARDRAILS
    assert "escalate" in GUARDRAILS

    refusal_text = " ".join(GUARDRAILS["refuse"])
    never_claim_text = " ".join(GUARDRAILS["never_claim"])

    assert "OTP" in refusal_text
    assert "UPI PIN" in refusal_text
    assert "account number" in refusal_text
    assert "scheme approval" in never_claim_text
    assert ESCALATION_SCRIPT in GUARDRAILS["escalate"]


def test_day2_language_policy_requires_code_mix_mirroring() -> None:
    assert STT_LANGUAGE == "multi"
    assert "Telugu" in LANGUAGE_POLICY
    assert "Hindi" in LANGUAGE_POLICY
    assert "English" in LANGUAGE_POLICY
    assert "mirror" in LANGUAGE_POLICY
    assert "code-mixed" in SYSTEM_PROMPT


def test_day2_first_turn_greeting_is_explicit_and_spoken() -> None:
    assert "Suraksha Saathi" in FIRST_TURN_GREETING
    assert "UPI fraud" in FIRST_TURN_GREETING
    assert "OTP" in FIRST_TURN_GREETING
    assert FIRST_TURN_GREETING in SYSTEM_PROMPT


def test_day2_prompt_uses_required_section_structure() -> None:
    required_sections = [
        "IDENTITY",
        "OBJECTIVES",
        "KNOWLEDGE",
        "LANGUAGE",
        "GUARDRAILS",
        "STYLE",
    ]

    for section in required_sections:
        assert section in SYSTEM_PROMPT

    assert KNOWLEDGE_BOUNDARIES in SYSTEM_PROMPT
    assert ESCALATION_SCRIPT in SYSTEM_PROMPT
