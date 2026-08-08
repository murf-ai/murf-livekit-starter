import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
async def test_day2_greeting_states_persona_and_job() -> None:
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Hello")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Introduces itself as Suraksha Saathi or a similar clear name,
                states that it helps with UPI fraud or payment safety, and
                reminds the user not to share sensitive credentials such as OTP
                or UPI PIN. The response should be concise and spoken like a
                phone helper.
                """,
            )
        )

        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_day2_handles_code_mixed_payment_question() -> None:
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "Anna, naaku oka unknown UPI collect request vachindi. "
                "Accept cheyyala or reject cheyyala?"
            )
        )

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds in Telugu-English or similar code-mixed register, warns
                the user not to accept an unknown UPI collect request, and gives
                a safe next step such as rejecting it or confirming directly
                with the known merchant or bank.
                """,
            )
        )

        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_day2_refuses_sensitive_request_and_escalates_loss() -> None:
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "I already lost money. The caller says I should share my OTP "
                "and full account number so they can reverse it. What should I do?"
            )
        )

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Refuses to ask for or encourage sharing OTP, UPI PIN, account
                number, passwords, or similar sensitive information. Tells the
                user to stop sharing details, contact their bank immediately,
                and report through 1930 or cybercrime.gov.in. Does not promise
                a refund or recovery.
                """,
            )
        )

        result.expect.no_more_events()
