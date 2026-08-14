"""Day 9 routing tests for the focused Jan Sahay specialist team."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from livekit.agents import llm

from agent import Assistant
from specialists import (
    AccountSupportSpecialist,
    DigitalSafetySpecialist,
    GovernmentSchemeSpecialist,
)


def test_normal_question_stays_with_main_agent() -> None:
    """A greeting is intentionally covered by the main agent's prompt, not a route."""
    main = Assistant()
    assert hasattr(main, "handoff_to_specialist")
    assert main._last_user_topic == "government schemes"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("specialist_id", "specialist_type"),
    [
        ("government_schemes", GovernmentSchemeSpecialist),
        ("digital_safety", DigitalSafetySpecialist),
        ("account_support", AccountSupportSpecialist),
    ],
)
async def test_main_handoffs_to_requested_specialist(
    specialist_id: str, specialist_type: type
) -> None:
    main = Assistant()
    main._reply_lang = "en"
    session = MagicMock()
    session.say = AsyncMock()
    context = MagicMock(session=session)

    result = json.loads(
        await main.handoff_to_specialist(
            context,
            specialist_id=specialist_id,
            reason="The caller needs focused help.",
        )
    )

    assert result["handed_off"] is True
    handed_agent = session.update_agent.call_args.args[0]
    assert isinstance(handed_agent, specialist_type)
    assert handed_agent._primary_agent is main
    assert result["conversation_preserved"] is True
    assert session.say.await_count == 2
    assert "is taking over your case" in session.say.await_args_list[0].args[0]


@pytest.mark.asyncio
async def test_specialist_can_return_to_main_agent() -> None:
    main = Assistant()
    specialist = DigitalSafetySpecialist(main, "en")
    session = MagicMock()
    session.say = AsyncMock()
    context = MagicMock(session=session)

    result = json.loads(await specialist.return_to_main_agent(context))

    assert result["returned"] is True
    session.update_agent.assert_called_once_with(main)
    session.say.assert_awaited_once()


@pytest.mark.asyncio
async def test_digital_safety_specialist_creates_one_complete_incident_case() -> None:
    """A security ticket keeps the caller's story, but no banking secret."""
    main = Assistant()
    specialist = DigitalSafetySpecialist(main, "en")
    context = MagicMock()
    created = {
        "ok": True,
        "reference_id": "JS-SECURE01",
        "status": "open",
    }

    with patch(
        "specialists.escalation.create_escalation", return_value=created
    ) as save:
        result = json.loads(
            await specialist.create_specialist_case(
                context,
                requester_name="Asha Kumar",
                contact_hint="asha@example.test",
                issue_description=(
                    "Caller received a phishing link claiming to be from their bank."
                ),
                diagnostic_steps="Caller reported the sender and did not share credentials.",
                user_consent=True,
            )
        )

    assert result["ok"] is True
    assert main._last_escalation_ref == "JS-SECURE01"
    assert save.call_args.kwargs["trigger_type"] == "fraud_suspected"
    assert save.call_args.kwargs["urgency"] == "high"
    assert save.call_args.kwargs["requester_name"] == "Asha Kumar"
    assert save.call_args.kwargs["contact_hint"] == "asha@example.test"


def test_specialist_intake_requires_full_story_and_consent() -> None:
    specialist = AccountSupportSpecialist(Assistant(), "en")

    assert "Listen to the whole story" in specialist.instructions
    assert "explicit permission" in specialist.instructions


@pytest.mark.asyncio
async def test_unknown_specialist_fails_without_switching_agents() -> None:
    main = Assistant()
    context = MagicMock(session=MagicMock())

    result = json.loads(
        await main.handoff_to_specialist(
            context, specialist_id="unknown", reason="Bad routing input."
        )
    )

    assert result["handed_off"] is False
    context.session.update_agent.assert_not_called()


@pytest.mark.asyncio
async def test_hindi_handoff_announces_then_introduces_specialist() -> None:
    main = Assistant()
    main._reply_lang = "hi"
    session = MagicMock()
    session.say = AsyncMock()
    context = MagicMock(session=session)

    result = json.loads(
        await main.handoff_to_specialist(
            context,
            specialist_id="government_schemes",
            reason="User asked about PMJDY in Hindi.",
        )
    )

    assert result["handed_off"] is True
    announcement = session.say.await_args_list[0].args[0]
    introduction = session.say.await_args_list[1].args[0]
    assert "Sarkari Yojana Specialist" in announcement
    assert "Namaste" in introduction
    assert "Sarkari Yojana Specialist" in introduction


@pytest.mark.asyncio
async def test_upi_question_is_handed_to_digital_safety_specialist() -> None:
    main = Assistant()
    main._reply_lang = "en"
    session = MagicMock()
    session.say = AsyncMock()
    main._session = session

    with pytest.raises(llm.StopResponse):
        await main.on_user_turn_completed(
            llm.ChatContext(), llm.ChatMessage(role="user", content=["What is UPI?"])
        )

    handed_agent = session.update_agent.call_args.args[0]
    assert isinstance(handed_agent, DigitalSafetySpecialist)
    assert session.say.await_count == 2


@pytest.mark.asyncio
async def test_lost_card_goes_to_security_specialist_before_human_escalation() -> None:
    main = Assistant()
    main._reply_lang = "en"
    session = MagicMock()
    session.say = AsyncMock()
    main._session = session

    with pytest.raises(llm.StopResponse):
        await main.on_user_turn_completed(
            llm.ChatContext(),
            llm.ChatMessage(role="user", content=["My card was lost"]),
        )

    handed_agent = session.update_agent.call_args.args[0]
    assert isinstance(handed_agent, DigitalSafetySpecialist)
    assert main._awaiting_escalation_consent is False
    assert "Security Specialist" in session.say.await_args_list[0].args[0]
