import json
import pytest
from pathlib import Path
from livekit.agents import RunContext
from agent import Assistant

@pytest.mark.asyncio
async def test_check_scheme_eligibility_success(monkeypatch):
    assistant = Assistant()
    
    # Test valid eligibility check call
    result = await assistant.check_scheme_eligibility(
        context=None,
        age=25,
        occupation="unorganized worker",
        approximate_annual_income=150000,
        has_bank_account=True,
        has_daughter_under_10=True,
    )
    
    assert "official government financial schemes you qualify for" in result
    assert "eligibility criteria as of the scheme's official 2025-26 government scheme guidelines" in result
    assert "document checklist includes:" in result
    assert "Pradhan Mantri Suraksha Bima Yojana" in result
    assert "Sukanya Samriddhi Yojana" in result

@pytest.mark.asyncio
async def test_check_scheme_eligibility_failure_handling(monkeypatch):
    assistant = Assistant()
    
    # Temporarily point to a non-existent file to simulate dataset outage
    orig_file = Path("backend/src/scheme_data.json")
    
    # Call with non-existent path simulation by raising exception or checking fallback
    with monkeypatch.context() as m:
        m.setattr("agent.Path", lambda *args: Path("non_existent_file.json"))
        result = await assistant.check_scheme_eligibility(
            context=None,
            age=30,
            occupation="salaried",
            approximate_annual_income=300000,
            has_bank_account=True,
        )
        assert result == "I'm not able to check live eligibility data right now, but based on what I know, here's my best guidance. Please confirm with your bank or the official scheme portal."
