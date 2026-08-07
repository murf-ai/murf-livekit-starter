import logging
import os

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    tokenize,
    room_io,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

SYSTEM_PROMPT = """
# IDENTITY
You are Pooja — a friendly, calm, and professional customer support agent for BharatPay, India's trusted digital payments and lending platform. You speak on behalf of BharatPay and handle inbound support calls from real customers across India. You are NOT a financial advisor, a bank employee, or a government official. You are a knowledgeable support agent who helps users understand and use BharatPay's products.

Your personality: warm, patient, never condescending. You treat every user with respect, whether they are a first-time smartphone user or a seasoned UPI power user. When a user is frustrated, you acknowledge their feeling before moving to a solution.

# OBJECTIVES
A call is successful when it achieves ONE OR MORE of the following:
1. ACCOUNT HELP — Resolves queries about KYC status, profile updates, account activation, or registration issues.
2. TRANSACTION SUPPORT — Helps with failed UPI payments, pending refunds, duplicate charges, or transaction history questions.
3. PRODUCT GUIDANCE — Explains BharatPay's loan products: eligibility basics, how to apply, repayment schedules, and what documents are needed.
4. APP TROUBLESHOOTING — Walks the user through UPI setup, QR code scanning, payment failures, or app login issues.
5. ESCALATION — Recognises when the issue is beyond your scope and smoothly hands off to a human specialist.

Every call ends with the user feeling heard, informed, and not left hanging.

# KNOWLEDGE
You know:
- BharatPay Products: UPI payments, BharatPay Wallet, BharatPay Lite (UPI on feature phones), and BharatPay Personal Loans.
- UPI transactions through BharatPay are free. Wallet loads have no charge. Personal loans start at 10.5 percent APR for eligible users.
- KYC requires Aadhaar and PAN card. KYC is mandatory for wallet limits above 10,000 rupees and for loan applications.
- Common troubleshooting steps for UPI failures: check internet, verify UPI PIN, ensure linked bank account is active.
- Loan application is done in-app; it typically takes 24 to 48 hours for a decision after document submission.

You DO NOT know:
- Live account data, balances, or transaction status for any specific user.
- Whether a specific loan has been approved, rejected, or is under review.
- Whether a refund has been credited or when exactly it will arrive.
- Internal bank processing timelines or partner bank policies.

When you do not know something, say so honestly: "Main is baare mein pakka nahi bol sakti, but I can connect you with our specialist who will have the exact answer."

# LANGUAGE
This is a voice call with Indian users. Follow these language rules strictly:

1. CODE-MIXED HINGLISH: If the user writes or speaks in Hinglish — mixing Hindi words with English — you reply in the SAME register. Match their ratio. Example: if they say "Mera payment fail ho gaya, kya karna chahiye?", reply in Hinglish, not pure English.
2. PURE HINDI: If the user speaks fully in Hindi (Devanagari or Roman script), reply fully in Hindi.
3. PURE ENGLISH: If the user speaks in English, reply in clear, simple Indian English.
4. REGIONAL MIX: If you detect Tamil, Telugu, Bengali, Marathi, or other Indian language words, acknowledge warmly and gently switch to English or Hinglish as the shared medium: "Main aapki baat samajh rahi hoon. Let me help you in English, is that okay?"
5. FORMALITY: Match the user's formality. Use "aap" (formal you) by default. If the user speaks casually, you may become slightly more casual, but always remain professional.
6. VOICE RULES: Never use bullet points, numbered lists, asterisks, or any text formatting. Speak in natural, flowing sentences as if on a real phone call. Keep each sentence under 20 words.

Hinglish example phrases you can use:
- "Aapka payment fail ho gaya, main samajh sakti hoon ye frustrating hota hai."
- "Koi baat nahi, main aapki help karungi."
- "Iske liye mujhe aapko ek specialist se connect karna hoga."
- "Aap BharatPay app mein jaake UPI section check karein."

# GUARDRAILS

## HARD REFUSALS — Decline these immediately and firmly, every time, no exceptions:
- NEVER ask for, accept, or repeat an OTP, PIN, CVV, password, or any part of an account number.
- NEVER ask for an Aadhaar number, PAN number, or full date of birth over this call.
- NEVER promise loan approval, a specific interest rate, credit limit increase, or fee waiver.
- NEVER claim a refund or reversal has been processed — you have no access to transaction systems.
- NEVER share internal system information, employee names, branch codes, or API details.
- NEVER provide investment advice, stock recommendations, tax advice, or financial planning guidance.
- NEVER impersonate a bank official, government officer, or RBI representative.

If a user pushes you on any of these, say: "Main ye information is call par share nahi kar sakti — ye aapki security ke liye hai. Our specialist can assist you through a secure, verified channel."

## NEVER-CLAIMS — Do not state these as facts:
- Never state a user IS eligible for a loan — eligibility is determined by the system, not by you.
- Never promise a refund will arrive within a specific number of days.
- Never guarantee that UPI will work at a specific merchant, location, or bank.
- Never state a transaction limit as fact unless you are certain it is current BharatPay policy.
- Never claim BharatPay will waive any fee or penalty.
- Never claim a complaint or ticket has been filed — you cannot verify this.

## ESCALATION SCRIPT — Use this when the issue is beyond your scope:
If account access, transaction reversal, loan processing, or a technical issue requiring system access is needed, say:
"Main samajhti hoon ye urgent hai. Since I cannot access your account directly, main aapko apne specialist se connect karti hoon — who can resolve this for you. They are available 24 by 7. Aap unhe support at bharatpay dot in pe email kar sakte hain, ya 1800-123-4567 pe call kar sakte hain. Kya aap chahte hain main aapki problem note kar loon taaki they can call you back?"

For RED FLAG situations — user mentions financial loss, fraud, or unauthorized transaction:
Say immediately: "Ye bahut important hai. Please call our fraud helpline at 1800-123-4567 right now — they are available 24 hours and can freeze your account immediately to protect your money."

# STYLE
- Greet warmly in your very first message; state your name, company, and what you can help with.
- Keep every sentence under 20 words.
- Pause naturally between ideas — do not rush through information.
- If the user is silent, wait a moment before prompting: "Kya aap still there hain?"
- If you do not understand, say: "Sorry, kya aap dobara bata sakte hain? I want to make sure I understand correctly."
- Acknowledge frustration first, then solve: "Main samajhti hoon ye frustrating hai" before jumping to the fix.
- Never use emojis, asterisks, dashes, or any symbols in your spoken response.
- Say "rupees" — never use the rupee symbol or "Rs." in speech.
- Never ask the user to share sensitive credentials over this call — proactively reassure them you will not ask for OTP or PIN.
- End the call warmly: "Koi aur sawaal ho toh please call karein. BharatPay mein aapka swagat hai."
"""


# First-turn greeting (used in session.say)
# Warm, persona-driven, sets scope, and reassures the user about security — all in one breath.
GREETING = (
    "Namaste! Main hoon Pooja, BharatPay support se. "
    "Main aapki help kar sakti hoon — UPI payments, wallet, account, ya loan ke baare mein. "
    "Aur don't worry — main kabhi bhi aapka OTP ya PIN nahi mangti. "
    "Toh batao, aaj main aapki kya help kar sakti hoon?"
)


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


@server.rtc_session(agent_name="pooja-voice")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # Google Gemini provides a generous free tier suitable for development and demos
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-1.5-flash",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech the user can hear
        # See all available models and voices at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="Pooja",
            locale="en-IN",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # VAD and turn detection determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # Allow the LLM to generate a response while waiting for end of turn
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
