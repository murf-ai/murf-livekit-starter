"""Unit tests for Day 5 scheme eligibility + document checklist tools."""

import schemes
from agent import Assistant, detect_reply_language


def test_resolve_scheme_aliases():
    assert schemes.resolve_scheme_code("PMSBY") == "pmsby"
    assert schemes.resolve_scheme_code("jan dhan") == "pmjdy"
    assert schemes.resolve_scheme_code("Atal Pension Yojana") == "apy"
    assert schemes.resolve_scheme_code("jeevan jyoti") == "pmjjby"
    assert schemes.resolve_scheme_code("totally fake scheme") is None


def test_eligibility_pmsby_likely_eligible():
    result = schemes.check_eligibility(
        scheme_name="PMSBY",
        age=35,
        has_bank_account=True,
    )
    assert result["ok"] is True
    assert result["status"] == "likely_eligible"
    assert result["scheme_short_name"] == "PMSBY"
    assert "data_as_of" in result
    assert result["data_as_of"]
    assert "speak_summary" in result


def test_eligibility_pmsby_too_young():
    result = schemes.check_eligibility(
        scheme_name="PMSBY",
        age=16,
        has_bank_account=True,
    )
    assert result["ok"] is True
    assert result["status"] == "likely_not_eligible"
    assert any("Minimum age" in b for b in result["blockers"])


def test_eligibility_pmjjby_too_old_to_join():
    result = schemes.check_eligibility(
        scheme_name="PMJJBY",
        age=55,
        has_bank_account=True,
    )
    assert result["status"] == "likely_not_eligible"


def test_eligibility_needs_more_info():
    result = schemes.check_eligibility(scheme_name="APY", age=30)
    # APY requires bank account — missing has_bank_account
    assert result["status"] == "need_more_info"
    assert "has_bank_account" in result["missing_fields"]


def test_eligibility_unknown_scheme():
    result = schemes.check_eligibility(scheme_name="Crypto Super Pension", age=30)
    assert result["ok"] is False
    assert result["error"] == "unknown_scheme"
    assert "PMJDY" in result["message"] or "supported" in result["message"].lower()


def test_document_checklist_pmjdy():
    result = schemes.get_document_checklist("Jan Dhan")
    assert result["ok"] is True
    assert result["scheme_code"] == "pmjdy"
    assert len(result["required_documents"]) >= 2
    assert "data_as_of" in result
    assert (
        "Identity" in result["speak_summary"]
        or "identity" in result["speak_summary"].lower()
        or "Aadhaar" in result["speak_summary"]
    )


def test_document_checklist_unknown():
    result = schemes.get_document_checklist("Housing Loan Mega")
    assert result["ok"] is False
    assert result["error"] == "unknown_scheme"


def test_scheme_info_has_vintage():
    result = schemes.get_scheme_overview("APY")
    assert result["ok"] is True
    assert result["data_as_of"] == schemes.DATA_AS_OF
    assert (
        "local" in result["data_source"].lower()
        or "hand-built" in result["data_source"].lower()
    )


def test_assistant_tools_registered():
    """Assistant must expose Day 5 tools to the LLM."""
    agent = Assistant()
    # livekit Agent stores tools; ensure our methods exist and are callable
    assert hasattr(agent, "check_scheme_eligibility")
    assert hasattr(agent, "get_document_checklist")
    assert hasattr(agent, "get_scheme_info")
    assert hasattr(agent, "lookup_caller")
    assert hasattr(agent, "save_caller_memory")


def test_short_greet_language_detect():
    assert detect_reply_language("Hello") == "en"
    assert detect_reply_language("hi") == "en" or detect_reply_language("hi") in (
        "en",
        "hi",
    )
    assert detect_reply_language("Namaste") == "hi"
