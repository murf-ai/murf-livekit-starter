from agent_config import (
    AGENT_NAME,
    LLM_MODEL,
    LLM_PROVIDER,
    MURF_LOCALE,
    MURF_STYLE,
    MURF_VOICE_ID,
    SYSTEM_PROMPT,
    TRACK,
)


def test_day1_track_and_agent_identity() -> None:
    assert TRACK == "Financial Services"
    assert AGENT_NAME == "suraksha-saathi"
    assert "Suraksha Saathi" in SYSTEM_PROMPT
    assert "UPI" in SYSTEM_PROMPT


def test_day1_uses_telugu_indian_murf_voice() -> None:
    assert MURF_VOICE_ID == "Samar"
    assert MURF_LOCALE == "te-IN"
    assert MURF_STYLE == "Conversational"
    assert "Telugu-first" in SYSTEM_PROMPT


def test_day1_financial_safety_boundaries_are_present() -> None:
    required_terms = ["OTP", "UPI PIN", "1930", "cybercrime.gov.in"]

    for term in required_terms:
        assert term in SYSTEM_PROMPT


def test_day1_uses_gpt_instead_of_gemini() -> None:
    assert LLM_PROVIDER == "openai"
    assert LLM_MODEL == "gpt-4.1-mini"
