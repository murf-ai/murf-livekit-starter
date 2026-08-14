import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant, SchemeSpecialistAgent


def _llm() -> llm.LLM:
    return inference.LLM(model="google/gemini-2.5-flash")


@pytest.mark.asyncio
async def test_normal_path_no_handoff() -> None:
    """Validate normal path: caller asks a general financial/budgeting question, main agent answers directly without handoff tool execution."""
    async with (
        _llm() as llm_instance,
        AgentSession(llm=llm_instance) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="How should I create a simple monthly personal budget?")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm_instance,
                intent="""
                Provides friendly general advice on creating a personal budget.
                Must NOT trigger any agent handoff or transfer tool.
                """,
            )
        )

        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_farmer_scheme_handoff() -> None:
    """Validate specific regression test: caller asks 'Am I eligible for any government schemes for small farmers?' -> main agent MUST trigger transfer_to_scheme_specialist."""
    async with (
        _llm() as llm_instance,
        AgentSession(llm=llm_instance) as session,
    ):
        main_agent = Assistant()
        await session.start(main_agent)

        result = await session.run(
            user_input="Am I eligible for any government schemes for small farmers?"
        )

        # First event is either verbal announcement or tool call
        event = result.expect.next_event()
        if event.is_message(role="assistant"):
            event = result.expect.next_event()

        event.is_function_call(name="transfer_to_scheme_specialist")



