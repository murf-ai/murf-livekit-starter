import pytest
import asyncio
import uuid
import json
from unittest.mock import AsyncMock, MagicMock
from livekit.agents import llm
from livekit import rtc
import manager
import db
import threat_engine
from agent import Assistant

@pytest.mark.asyncio
async def test_name_ambiguity_clarification_and_resolve() -> None:
    """Test that introducing a different name prompts clarification, and confirming resolves it.
    When the resolved name exists in DB, it should speak a welcome-back with memory facts.
    """
    assistant = Assistant()
    assistant._call_room_id = f"test_room_{uuid.uuid4().hex}"
    assistant._reply_lang = "en"  # Force English language for English assertion
    session_mock = MagicMock()
    session_mock.say = AsyncMock()
    session_mock.close = AsyncMock()
    session_mock.room = MagicMock()
    session_mock.room.connection_state = rtc.ConnectionState.CONN_CONNECTED
    assistant._session = session_mock

    # Pre-populate DB with a known "Bria" profile that has memory facts
    db.init_db()
    db.save_caller("bria", "Bria", "en", {"safe_key": "abcd", "last_topic": "account creation"}, True)

    # Mock chat_ctx
    chat_ctx = llm.ChatContext()

    # 1. First introduction with a misspelled name: "I am Phria"
    msg1 = llm.ChatMessage(role="user", content=["I am Phria"])
    try:
        await assistant.on_user_turn_completed(chat_ctx, msg1)
    except llm.StopResponse:
        pass

    assert assistant._known_caller_name == "Phria"

    # 2. Correction: "No I am Bria"
    msg2 = llm.ChatMessage(role="user", content=["No I am Bria"])
    try:
        await assistant.on_user_turn_completed(chat_ctx, msg2)
    except llm.StopResponse:
        pass

    assert assistant._awaiting_name_ambiguity_resolution is True
    assert assistant._candidate_name_switch == "Bria"

    # 3. Clarification response: "Bria"
    msg3 = llm.ChatMessage(role="user", content=["Bria"])
    try:
        await assistant.on_user_turn_completed(chat_ctx, msg3)
    except llm.StopResponse:
        pass

    assert assistant._awaiting_name_ambiguity_resolution is False
    assert assistant._known_caller_name == "Bria"
    # Since Bria exists in DB with last_topic, should speak welcome-back with memory
    assert assistant._memory_loaded is True
    assert assistant._last_user_topic == "account creation"
    # The welcome-back line should mention the last topic
    last_say_args = session_mock.say.call_args
    spoken_text = last_say_args[0][0] if last_say_args[0] else ""
    assert "Bria" in spoken_text
    assert "account creation" in spoken_text.lower() or "account" in spoken_text.lower()


@pytest.mark.asyncio
async def test_name_ambiguity_multiple_switches_ban() -> None:
    """Test that continuing to provide ambiguous names results in a ban."""
    assistant = Assistant()
    assistant._call_room_id = f"test_room_{uuid.uuid4().hex}"
    assistant._reply_lang = "en"
    session_mock = MagicMock()
    session_mock.say = AsyncMock()
    session_mock.close = AsyncMock()
    session_mock.room = MagicMock()
    session_mock.room.connection_state = rtc.ConnectionState.CONN_CONNECTED
    assistant._session = session_mock

    chat_ctx = llm.ChatContext()

    # 1. First name
    msg1 = llm.ChatMessage(role="user", content=["I am Kia"])
    try:
        await assistant.on_user_turn_completed(chat_ctx, msg1)
    except llm.StopResponse:
        pass

    # 2. Ambiguity trigger
    msg2 = llm.ChatMessage(role="user", content=["I am Rohan"])
    try:
        await assistant.on_user_turn_completed(chat_ctx, msg2)
    except llm.StopResponse:
        pass

    assert assistant._awaiting_name_ambiguity_resolution is True

    # 3. Keep changing names: "I am Anita"
    msg3 = llm.ChatMessage(role="user", content=["I am Anita"])
    try:
        await assistant.on_user_turn_completed(chat_ctx, msg3)
    except llm.StopResponse:
        pass

    assert assistant._known_caller_name == "Banned"
    assert assistant.get_threat_scorer().is_banned is True
    session_mock.say.assert_called_with(
        "Identity verification failed. Access has been restricted due to multiple identity changes.",
        allow_interruptions=False
    )


@pytest.mark.asyncio
async def test_manager_rejection_closes_session() -> None:
    """Test that manager rejection in database is detected by status polling and closes the session."""
    assistant = Assistant()
    assistant._call_room_id = f"test_room_{uuid.uuid4().hex}"
    session_mock = MagicMock()
    session_mock.say = AsyncMock()
    session_mock.close = AsyncMock()
    session_mock.room = MagicMock()
    session_mock.room.connection_state = rtc.ConnectionState.CONN_CONNECTED
    assistant._session = session_mock

    # Pre-set transaction request ID
    assistant._safe_key_request_id = "test-tx-123"

    # Create a mock pending request in the manager table
    manager.init_manager_db()
    with manager._get_conn() as conn:
        conn.execute("DELETE FROM manager_approvals WHERE request_id = 'test-tx-123'")
        conn.execute(
            "INSERT INTO manager_approvals (request_id, request_type, requester_name, safe_key, status, user_id, details_json, created_at, updated_at) "
            "VALUES ('test-tx-123', 'TRANSACTION_TRANSFER', 'Kia', 'abcd', 'PENDING_APPROVAL', 'kia_user', '{}', 'now', 'now')"
        )
        conn.commit()

    # Start status polling
    assistant.start_manager_status_polling("en")

    # Give it a second to start
    await asyncio.sleep(0.5)

    # Modify request to REJECTED in DB
    with manager._get_conn() as conn:
        conn.execute("UPDATE manager_approvals SET status = 'REJECTED' WHERE request_id = 'test-tx-123'")
        conn.commit()

    # Wait for polling to detect rejection and close the session
    closed = False
    for _ in range(12):
        await asyncio.sleep(0.5)
        if assistant._safe_key_request_id is None:
            closed = True
            break

    assert closed is True
    # Wait for the post-rejection 4.0s sleep to finish so close is called
    await asyncio.sleep(4.5)
    session_mock.close.assert_called_once()


@pytest.mark.asyncio
async def test_identity_mismatch_ban() -> None:
    """Test that a caller named Priya attempting to verify with Bria's Safe Key (abcd) is immediately banned and closed."""
    assistant = Assistant()
    assistant._call_room_id = f"test_room_{uuid.uuid4().hex}"
    assistant._reply_lang = "en"
    session_mock = MagicMock()
    session_mock.say = AsyncMock()
    session_mock.close = AsyncMock()
    session_mock.room = MagicMock()
    session_mock.room.connection_state = rtc.ConnectionState.CONN_CONNECTED
    assistant._session = session_mock

    # Setup database with Bria and Priya profiles
    db.init_db()
    db.save_caller("bria", "Bria", "en", {"safe_key": "abcd"}, True)
    db.save_caller("priya", "Priya", "en", {"safe_key": "74"}, True)

    # Establish known session name as Priya
    assistant._known_caller_name = "Priya"
    assistant._awaiting_safe_key_verification = True

    chat_ctx = llm.ChatContext()
    # Priya says "Priya a b c d" (which maps to abcd/Bria)
    msg = llm.ChatMessage(role="user", content=["Priya a b c d"])

    with pytest.raises(llm.StopResponse):
        await assistant.on_user_turn_completed(chat_ctx, msg)

    assert assistant._known_caller_name == "Banned"
    assert assistant.get_threat_scorer().is_banned is True
    session_mock.say.assert_called_with(
        "Security protocol activated. Access has been restricted due to identity verification mismatch.",
        allow_interruptions=False
    )
    # Wait for the post-ban sleep to finish and verify call is closed
    await asyncio.sleep(4.5)
    session_mock.close.assert_called_once()


@pytest.mark.asyncio
async def test_manager_approval_status_inquiries() -> None:
    """Test that asking 'did the manager approve' yields dynamic Yes/No responses."""
    assistant = Assistant()
    assistant._call_room_id = f"test_room_{uuid.uuid4().hex}"
    assistant._reply_lang = "en"
    session_mock = MagicMock()
    session_mock.say = AsyncMock()
    session_mock.close = MagicMock()
    session_mock.room = MagicMock()
    session_mock.room.connection_state = rtc.ConnectionState.CONN_CONNECTED
    assistant._session = session_mock

    # Establish caller name as Kia
    assistant._known_caller_name = "Kia"

    # Setup database requests
    manager.init_manager_db()
    with manager._get_conn() as conn:
        conn.execute("DELETE FROM manager_approvals WHERE requester_name = 'Kia'")
        # Insert APPROVED request
        conn.execute(
            "INSERT INTO manager_approvals (request_id, request_type, requester_name, safe_key, status, user_id, details_json, created_at, updated_at) "
            "VALUES ('status-test-1', 'TRANSACTION_TRANSFER', 'Kia', 'abcd', 'APPROVED', 'kia_user', '{}', 'now', 'now')"
        )
        conn.commit()

    chat_ctx = llm.ChatContext()

    # 1. Ask about approved request
    msg = llm.ChatMessage(role="user", content=["Did the manager approve?"])
    with pytest.raises(llm.StopResponse):
        await assistant.on_user_turn_completed(chat_ctx, msg)

    session_mock.say.assert_called_with(
        "Yes, Senior Manager X has approved your request.",
        allow_interruptions=True
    )

    # 2. Update to REJECTED
    with manager._get_conn() as conn:
        conn.execute("UPDATE manager_approvals SET status = 'REJECTED' WHERE request_id = 'status-test-1'")
        conn.commit()

    msg = llm.ChatMessage(role="user", content=["did the manager confirm"])
    with pytest.raises(llm.StopResponse):
        await assistant.on_user_turn_completed(chat_ctx, msg)

    session_mock.say.assert_called_with(
        "No, Senior Manager X has rejected your request.",
        allow_interruptions=True
    )

    # 3. Update to PENDING
    with manager._get_conn() as conn:
        conn.execute("UPDATE manager_approvals SET status = 'PENDING_APPROVAL' WHERE request_id = 'status-test-1'")
        conn.commit()

    msg = llm.ChatMessage(role="user", content=["is my request pending approval"])
    with pytest.raises(llm.StopResponse):
        await assistant.on_user_turn_completed(chat_ctx, msg)

    session_mock.say.assert_called_with(
        "No, it has not been approved yet. It is still pending manager review.",
        allow_interruptions=True
    )
