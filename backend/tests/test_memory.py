import pytest
import sqlite3
import json
import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from memory import (
    init_db,
    lookup_caller,
    save_caller,
    sanitize_facts,
    lookup_caller_memory,
    save_caller_memory
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_caller_memory.db"
    init_db(db_file)
    return db_file


def test_sqlite_persistence_and_lookup(temp_db):
    user_id = "user_12345"
    
    # Initial lookup returns exists=False
    rec = lookup_caller(user_id, db_path=temp_db)
    assert rec["exists"] is False
    
    # Save caller facts
    saved = save_caller(
        user_id=user_id,
        name="Anita Sharma",
        language_preference="Hindi",
        new_facts=["Checked eligibility for Atal Pension Yojana", "Age 35, vendor"],
        db_path=temp_db
    )
    assert saved["status"] == "saved"
    assert saved["name"] == "Anita Sharma"
    
    # Look up returning caller
    rec2 = lookup_caller(user_id, db_path=temp_db)
    assert rec2["exists"] is True
    assert rec2["name"] == "Anita Sharma"
    assert rec2["language_preference"] == "Hindi"
    assert "Checked eligibility for Atal Pension Yojana" in rec2["facts"]


def test_sensitive_data_redaction():
    # 1. 16-digit card number -> masked to ending in XXXX
    raw_card_fact = "Caller card number is 4532112233445566 with pin 9876"
    sanitized_card = sanitize_facts(raw_card_fact)
    assert "4532112233445566" not in sanitized_card
    assert "ending in 5566" in sanitized_card
    assert "[REDACTED]" in sanitized_card
    
    # 2. 12-digit account number -> masked
    raw_acc_fact = "Transferred from account 123456789012"
    sanitized_acc = sanitize_facts(raw_acc_fact)
    assert "123456789012" not in sanitized_acc
    assert "ending in 9012" in sanitized_acc
    
    # 3. OTP & Password -> REDACTED
    raw_otp_fact = "Caller OTP: 654321 and password: SecretPassword123"
    sanitized_otp = sanitize_facts(raw_otp_fact)
    assert "654321" not in sanitized_otp
    assert "[REDACTED]" in sanitized_otp


class MockRunContext:
    pass


@pytest.mark.asyncio
async def test_memory_tool_functions(temp_db, monkeypatch):
    import memory
    monkeypatch.setattr(memory, "DB_PATH", temp_db)
    ctx = MockRunContext()
    
    # Call save_caller_memory tool function
    tool_fn_save = getattr(save_caller_memory, "fn", getattr(save_caller_memory, "_fn", save_caller_memory))
    res_save = await tool_fn_save(
        None,
        ctx,
        user_id="user_999",
        name="Ramesh Kumar",
        language_preference="English",
        facts_to_remember=["Qualified for PMJDY scheme", "Account 998877665544"]
    )
    
    assert res_save["status"] == "saved"
    assert "998877665544" not in json.dumps(res_save["facts"])
    assert "ending in 5544" in json.dumps(res_save["facts"])
    
    # Call lookup_caller_memory tool function
    tool_fn_lookup = getattr(lookup_caller_memory, "fn", getattr(lookup_caller_memory, "_fn", lookup_caller_memory))
    res_lookup = await tool_fn_lookup(None, ctx, user_id="user_999")
    assert res_lookup["exists"] is True
    assert res_lookup["name"] == "Ramesh Kumar"
