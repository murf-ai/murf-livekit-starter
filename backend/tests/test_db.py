import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

import db


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_caller_memory.db"
    db.init_db(db_file)
    return db_file


def test_save_and_lookup_caller_with_consent(temp_db):
    res = db.save_caller(
        user_id="user_123",
        name="Ramesh",
        language_preference="hi",
        facts={"schemes_checked": ["PMJDY"], "eligibility_answers": {"age": "35"}},
        consent_given=True,
        db_path=temp_db,
    )
    assert res["saved"] is True
    assert res["status"] == "success"

    caller = db.get_caller("user_123", db_path=temp_db)
    assert caller is not None
    assert caller["user_id"] == "user_123"
    assert caller["name"] == "Ramesh"
    assert caller["language_preference"] == "hi"
    assert caller["consent_given"] is True
    assert caller["facts"]["schemes_checked"] == ["PMJDY"]


def test_refuse_save_without_consent(temp_db):
    res = db.save_caller(
        user_id="user_456",
        name="Suresh",
        language_preference="en",
        facts={"schemes_checked": ["PMSBY"]},
        consent_given=False,
        db_path=temp_db,
    )
    assert res["saved"] is False
    assert res["status"] == "refused"

    caller = db.get_caller("user_456", db_path=temp_db)
    assert caller is None


def test_sanitize_sensitive_data(temp_db):
    dirty_facts = {
        "schemes_checked": ["PMJDY"],
        "account_number": "123456789012",
        "aadhaar_num": "999988887777",
        "pin_code": "1234",
        "otp": "654321",
    }
    clean = db.sanitize_facts(dirty_facts)
    assert "schemes_checked" in clean
    assert "account_number" not in clean
    assert "aadhaar_num" not in clean
    assert "otp" not in clean

    # Save facts with sensitive data stripped
    res = db.save_caller(
        user_id="user_789",
        name="Anita",
        facts=dirty_facts,
        consent_given=True,
        db_path=temp_db,
    )
    assert res["saved"] is True
    caller = db.get_caller("user_789", db_path=temp_db)
    assert "account_number" not in caller["facts"]
    assert "aadhaar_num" not in caller["facts"]
    assert caller["facts"]["schemes_checked"] == ["PMJDY"]
