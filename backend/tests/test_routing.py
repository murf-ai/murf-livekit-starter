import asyncio
import pytest
from livekit.agents.llm import ChatContext
from livekit.plugins import google

try:
    from agent import Assistant
except ImportError:
    from src.agent import Assistant


@pytest.mark.asyncio
async def test_routing_scenarios():
    assistant = Assistant(user_id="test_user")
    llm = google.LLM(model="gemini-3.5-flash")

    handoff_tools = {
        "handoff_to_crop_specialist",
        "handoff_to_business_loan_specialist",
        "handoff_to_scheme_specialist",
    }

    # Filter tools to only include handoff tools during routing tests to prevent LLM from calling other startup tools
    tools = [t for t in assistant.tools if t.id in handoff_tools]

    # Format: (user_query, expected_tool_name_or_none)
    scenarios = [
        # 1. Greet / safety query should stay with main agent (no handoff tool call)
        ("Hello, who are you?", None),
        # 2. Digital safety stays with main agent
        ("How do I protect my UPI PIN from online fraud?", None),
        # 3. ATM security stays with main agent
        ("Is it safe to share my ATM card details over a call?", None),
        # 4. PM-KISAN goes to Crop Specialist
        (
            "I am a farmer, can I get direct income support under PM-KISAN?",
            "handoff_to_crop_specialist",
        ),
        # 5. Crop helper goes to Crop Specialist
        ("Are there any crop insurance or farming schemes?", "handoff_to_crop_specialist"),
        # 6. MUDRA loan goes to Business Loan Specialist
        (
            "Can I get a Mudra business loan to expand my shop?",
            "handoff_to_business_loan_specialist",
        ),
        # 7. Business loan goes to Business Loan Specialist
        (
            "Tell me how to apply for a micro-enterprise loan under PMMY",
            "handoff_to_business_loan_specialist",
        ),
        # 8. APY goes to Scheme Specialist
        ("How do I check my eligibility for Atal Pension Yojana?", "handoff_to_scheme_specialist"),
        # 9. PMJDY goes to Scheme Specialist
        ("Can you tell me about Pradhan Mantri Jan Dhan Yojana?", "handoff_to_scheme_specialist"),
        # 10. SSY goes to Scheme Specialist
        (
            "Can you tell me about Sukanya Samriddhi Yojana SSY?",
            "handoff_to_scheme_specialist",
        ),
    ]

    # Clean instructions to remove lookup_caller start-of-call requirement during routing tests
    test_instructions = assistant.instructions
    test_instructions = test_instructions.replace(
        "query returning caller database details by calling `lookup_caller` at the start of the call.",
        "greet users directly.",
    ).replace(
        "You MUST immediately call `lookup_caller` at the very start of the conversation.",
        "Greet the user directly.",
    ).replace(
        "You MUST immediately call `lookup_caller` at the very start of the conversation",
        "Greet the user directly",
    )

    for i, (query, expected_tool) in enumerate(scenarios):
        if i > 0:
            print("Sleeping 13s to respect Gemini Free Tier rate limits...")
            await asyncio.sleep(13.0)

        chat_ctx = ChatContext()
        chat_ctx.add_message(role="system", content=test_instructions)
        chat_ctx.add_message(role="user", content=query)

        # Query LLM to see which tool it chooses (llm.chat is sync, returns stream)
        stream = llm.chat(chat_ctx=chat_ctx, tools=tools)
        called_handoff_tool = None
        async for chunk in stream:
            if chunk.delta and chunk.delta.tool_calls:
                for tc in chunk.delta.tool_calls:
                    if tc.name in handoff_tools:
                        called_handoff_tool = tc.name
                        break
            if called_handoff_tool:
                break

        print(f"Query: '{query}' -> Called Handoff Tool: '{called_handoff_tool}' (Expected: '{expected_tool}')")
        assert (
            called_handoff_tool == expected_tool
        ), f"Expected handoff tool '{expected_tool}' for query '{query}', but got '{called_handoff_tool}'"
