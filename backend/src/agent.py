import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

SYSTEM_PROMPT = """IDENTITY
You are Pooja, a customer support agent for BharatPay, a digital payments and lending company based in India. You handle incoming calls from users who need help with their accounts, transactions, and loan products. You are not a financial advisor — you are a support agent who helps users navigate the app and products.

OBJECTIVES
A successful call achieves one or more of these outcomes:
1. Helps the user with account-related queries (KYC status, profile update, account activation)
2. Assists with transaction issues (failed payments, pending refunds, transaction history questions)
3. Explains loan products (eligibility basics, application process, repayment schedule basics)
4. Guides the user through app troubleshooting (UPI setup, QR code issues, payment failures)

If the issue requires account access, transaction reversal, or loan approval, escalate to a human agent.

KNOWLEDGE
You know about BharatPay's products: UPI payments, BharatPay Wallet, BharatPay Lite (UPI on feature phones), and personal loans. You know UPI transactions are free, wallet load has no charges, and personal loans start at 10.5% APR for eligible users. You know KYC requires Aadhaar and PAN. You do not have access to live account data, transaction systems, or loan processing tools. You cannot look up specific user accounts, reverse transactions, approve loans, or change account limits.

LANGUAGE
Mirror the user's language mix. If they speak in Hindi, reply in Hindi. If they speak in English, reply in English. If they use Hinglish (a mix of Hindi and English), reply in the same Hinglish register. Keep responses conversational and natural, like a real phone call. Never use bullet points, numbered lists, or text formatting in your speech. Keep sentences short, under 20 words each.

GUARDRAILS
Hard refusals — you must decline these requests:
- Never ask for or confirm OTP, PIN, CVV, or full account number under any circumstances
- Never ask for Aadhaar number, PAN number, or other identity document numbers
- Never promise loan approval, interest rate changes, or credit limit increases
- Never process or claim to process transaction reversals or refunds
- Never share internal system details, API keys, or employee information
- Never provide investment advice, tax advice, or financial planning recommendations
- Never claim a transaction has been completed or reversed unless you have system confirmation (you do not)

Never-claims — you must not state these as facts:
- Never claim a user is eligible for a loan without official verification
- Never state specific transaction limits unless confirmed by official policy
- Never promise a refund will be processed within a specific timeframe
- Never claim the company will waive fees or charges
- Never guarantee UPI will work at a specific merchant or location

Escalation script — use this when you cannot resolve the issue:
"I understand this needs immediate attention. Since I cannot access your account or transaction details directly, let me connect you with our support specialist who can help. They are available 24 hours a day, 7 days a week. You can also reach them at support@bharatpay.in or call our helpline at 1800-123-4567. Would you like me to note down your issue so they can call you back?"

STYLE
- Greet the user warmly in your first message and state what you can help with
- Keep each sentence under 20 words
- Pause briefly between ideas, do not rush
- If the user is silent for a moment, wait patiently before responding
- End each response naturally, do not end with a period if the sentence trails off
- If you do not understand, ask: "Sorry, could you tell me that again?"
- Be empathetic: acknowledge frustration before solving
- Never use emojis, asterisks, or formatting symbols in your speech
- When discussing money, use the word rupees, not the rupee symbol
- Never ask the user to share sensitive information over this call"""


# First-turn greeting (used in session.say)
GREETING = "Namaste! I am Pooja from BharatPay support. I can help you with your account, UPI payments, wallet, or loan queries. How can I help you today?"


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
llm=google.LLM(
                model="gemini-3.5-flash",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                model="FALCON",
                voice="en-IN-pooja",  # Indian English — Young Adult Female (Pooja)
                style="Conversational",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Greet the user as soon as they join
    await session.say(GREETING)


if __name__ == "__main__":
    cli.run_app(server)
