import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import agent
import db


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "agent_memory_test.db"
    db.init_db(db_file)
    return db_file


@pytest.mark.asyncio
async def test_agent_lookup_and_save_tool(temp_db, monkeypatch):
    monkeypatch.setattr(db, "DEFAULT_DB_PATH", temp_db)
    assistant = agent.Assistant()

    # Call save_caller_memory tool
    save_res_str = await assistant.save_caller_memory(
        ctx=None,
        name="Ramesh",
        language_preference="hi",
        facts=json.dumps({"schemes_checked": ["PMJDY", "PMSBY"], "eligible_age": True}),
    )
    save_res = json.loads(save_res_str)
    assert save_res["saved"] is True
    assert save_res["status"] == "success"

    # Lookup caller by name tool
    lookup_res_str = await assistant.lookup_caller(ctx=None, name_or_id="Ramesh")
    caller_data = json.loads(lookup_res_str)
    assert caller_data["name"] == "Ramesh"
    assert caller_data["facts"]["schemes_checked"] == ["PMJDY", "PMSBY"]


@pytest.mark.asyncio
async def test_returning_caller_greeting(temp_db, monkeypatch):
    # Setup caller record in DB
    db.save_caller(
        user_id="caller_101",
        name="Ramesh",
        language_preference="hi",
        facts={"schemes_checked": ["PMJDY"]},
        consent_given=True,
        db_path=temp_db,
    )

    caller = db.get_caller("caller_101", db_path=temp_db)
    assert caller is not None
    assert caller["name"] == "Ramesh"
    assert caller["facts"]["schemes_checked"] == ["PMJDY"]


def test_language_detection():
    assert (
        agent.detect_reply_language("Hello, please save my conversation", "hi-IN")
        == "en"
    )
    assert agent.detect_reply_language("My name is Ramesh", "hi-IN") == "en"
    assert agent.detect_reply_language("Namaste, mera naam Ramesh hai", "en-IN") == "hi"
    assert agent.detect_reply_language("नमस्ते जन सहाय", "en-IN") == "hi"
    # English with noisy multilingual STT garbage must still be English
    assert (
        agent.detect_reply_language(
            "tell me about some government schemes moneda ムーレン",
            "hi",
        )
        == "en"
    )
    assert agent.detect_reply_language("What is PMJDY eligibility?", None) == "en"
    assert agent.detect_reply_language("PMJDY kya hai batao", None) == "hi"


def test_name_extraction_stopwords():
    # Non-name phrases must return None (not extract "Conversation", "Details", "Schemes")
    assert agent.extract_caller_name("no please save the conversation") is None
    assert agent.extract_caller_name("tell me about government schemes") is None
    assert agent.extract_caller_name("save details for me") is None
    assert agent.extract_caller_name("how to open a bank account") is None

    # Valid name extractions
    assert agent.extract_caller_name("My name is Raj") == "Raj"
    assert agent.extract_caller_name("Mera naam Priya hai") == "Priya"
    assert agent.extract_caller_name("Save it under Amit Kumar") == "Amit Kumar"


def test_passive_memory_note_format():
    caller = {"name": "Raj", "facts": {"schemes_checked": ["PMJDY"]}}
    note = agent._format_passive_memory(caller)
    assert "CALLER_CONTEXT" in note
    assert "Do NOT say welcome back again" in note
    assert "Raj" in note
