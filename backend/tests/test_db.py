import json
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


def test_success_path_increments_totals(temp_db):
    before = db.get_call_stats(db_path=temp_db)
    db.start_call("voice_assistant_room_success", "browser", db_path=temp_db)
    db.mark_call_connected("voice_assistant_room_success", db_path=temp_db)
    db.note_user_turn("voice_assistant_room_success", db_path=temp_db)
    db.record_eligibility_result(
        "voice_assistant_room_success",
        {"ok": True, "status": "likely_eligible", "scheme_code": "pmsby"},
        db_path=temp_db,
    )
    ended = db.end_call("voice_assistant_room_success", "browser", db_path=temp_db)
    after = db.get_call_stats(db_path=temp_db)

    assert ended["outcome"] == "success"
    assert after["total_calls"] == before["total_calls"] + 1
    assert after["successful_calls"] == before["successful_calls"] + 1
    assert after["failed_calls"] == before["failed_calls"]
    assert after["eligibility_checks"] == before["eligibility_checks"] + 1


def test_document_list_is_success(temp_db):
    db.start_call("sip_docs_1", "sip", db_path=temp_db)
    db.mark_call_connected("sip_docs_1", db_path=temp_db)
    db.record_document_list_result(
        "sip_docs_1",
        {"ok": True, "scheme_code": "pmjdy"},
        db_path=temp_db,
    )
    ended = db.end_call("sip_docs_1", "sip", db_path=temp_db)
    assert ended["outcome"] == "success"
    assert ended["document_list_delivered"] is True
    assert ended["channel"] == "sip"


def test_connected_call_is_success_even_without_tools(temp_db):
    db.start_call("room_connected_hangup", "browser", db_path=temp_db)
    db.mark_call_connected("room_connected_hangup", db_path=temp_db)
    ended = db.end_call("room_connected_hangup", db_path=temp_db)
    assert ended["outcome"] == "success"
    assert ended["failure_type"] is None


def test_cancel_before_connect_is_failure(temp_db):
    before = db.get_call_stats(db_path=temp_db)
    ended = db.record_cancelled_call(
        room_id="cancelled_preconnect",
        channel="browser",
        db_path=temp_db,
    )
    after = db.get_call_stats(db_path=temp_db)

    assert ended["outcome"] == "failed"
    assert ended["failure_type"] == "cancelled_before_connect"
    assert after["total_calls"] == before["total_calls"] + 1
    assert after["failed_calls"] == before["failed_calls"] + 1
    assert after["successful_calls"] == before["successful_calls"]


def test_dashboard_payload_has_no_secrets(temp_db):
    db.start_call("secret_room_otp_9999", "browser", db_path=temp_db)
    db.record_eligibility_result(
        "secret_room_otp_9999",
        {
            "ok": True,
            "status": "likely_not_eligible",
            "scheme_code": "pmjjby",
            "otp": "654321",
            "account_number": "123456789012",
            "transcript": "my pin is 1234",
        },
        db_path=temp_db,
    )
    db.mark_call_connected("secret_room_otp_9999", db_path=temp_db)
    db.end_call("secret_room_otp_9999", db_path=temp_db)
    payload = db.get_dashboard_payload(db_path=temp_db)
    blob = json.dumps(payload)
    for forbidden in (
        "654321",
        "123456789012",
        "my pin is 1234",
        "account_number",
        "transcript",
        "secret_room_otp_9999",
    ):
        assert forbidden not in blob
    assert payload["total_calls"] >= 1
    assert "successful_calls" in payload
    assert "failed_calls" in payload
    assert payload["recent_calls"][0]["call_id"] == db._public_call_id(
        "secret_room_otp_9999"
    )


def test_specialist_handoff_summary_is_aggregate_only(temp_db):
    db.record_specialist_handoff("room_a", "government_schemes", db_path=temp_db)
    db.record_specialist_handoff("room_b", "digital_safety", db_path=temp_db)
    db.record_specialist_handoff("room_c", "digital_safety", db_path=temp_db)
    db.record_specialist_handoff("room_d", "account_support", db_path=temp_db)

    summary = db.get_specialist_handoff_summary(db_path=temp_db)
    assert summary == {
        "total": 4,
        "government_schemes": 1,
        "digital_safety": 2,
        "account_support": 1,
    }
    assert "room_a" not in json.dumps(summary)
