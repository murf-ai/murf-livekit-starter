import json
import logging

logging.basicConfig(level=logging.DEBUG)

from dotenv import load_dotenv
from livekit import rtc
from prompt import SYSTEM_PROMPT
from db import lookup_caller, save_caller_memory_db
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def explain_scheme(self, context: RunContext, scheme_name: str) -> str:
        """Lookup details, eligibility, benefits, and application guidance for official government financial schemes.

        Args:
            scheme_name: The name or acronym of the government scheme (e.g., 'PMJDY', 'PMSBY', 'PMJJBY', 'APY', 'Sukanya Samriddhi', 'Mudra', 'SCSS', 'SGB').
        """
        logger.info(f"Explaining government scheme: {scheme_name}")
        normalized = scheme_name.lower().strip()

        schemes = {
            "pmjdy": (
                "Pradhan Mantri Jan Dhan Yojana (PMJDY) offers a zero-balance bank account with a free RuPay debit card, "
                "accidental insurance cover up to 2 Lakh rupees, and an overdraft facility up to 10,000 rupees after 6 months."
            ),
            "jan dhan": (
                "Pradhan Mantri Jan Dhan Yojana (PMJDY) offers a zero-balance bank account with a free RuPay debit card, "
                "accidental insurance cover up to 2 Lakh rupees, and an overdraft facility up to 10,000 rupees after 6 months."
            ),
            "pmsby": (
                "Pradhan Mantri Suraksha Bima Yojana (PMSBY) is an accidental insurance scheme for ages 18 to 70. "
                "It offers 2 Lakh rupees cover for accidental death or total disability for a nominal annual premium of 20 rupees."
            ),
            "suraksha bima": (
                "Pradhan Mantri Suraksha Bima Yojana (PMSBY) is an accidental insurance scheme for ages 18 to 70. "
                "It offers 2 Lakh rupees cover for accidental death or total disability for a nominal annual premium of 20 rupees."
            ),
            "pmjjby": (
                "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY) provides life insurance cover of 2 Lakh rupees for death due to any cause. "
                "It is available for individuals aged 18 to 50 for an annual premium of 436 rupees."
            ),
            "jeevan jyoti": (
                "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY) provides life insurance cover of 2 Lakh rupees for death due to any cause. "
                "It is available for individuals aged 18 to 50 for an annual premium of 436 rupees."
            ),
            "apy": (
                "Atal Pension Yojana (APY) is a guaranteed pension scheme for unorganized sector workers aged 18 to 40. "
                "Subscribers receive a monthly pension of 1,000 to 5,000 rupees after age 60, depending on their contributions."
            ),
            "atal pension": (
                "Atal Pension Yojana (APY) is a guaranteed pension scheme for unorganized sector workers aged 18 to 40. "
                "Subscribers receive a monthly pension of 1,000 to 5,000 rupees after age 60, depending on their contributions."
            ),
            "sukanya samriddhi": (
                "Sukanya Samriddhi Yojana is a small savings scheme for a girl child below 10 years. "
                "It offers high interest rates, tax deductions under Section 80C, and tax-free returns. It matures when the girl turns 21 or gets married after 18."
            ),
            "ssy": (
                "Sukanya Samriddhi Yojana is a small savings scheme for a girl child below 10 years. "
                "It offers high interest rates, tax deductions under Section 80C, and tax-free returns. It matures when the girl turns 21 or gets married after 18."
            ),
            "mudra": (
                "Pradhan Mantri Mudra Yojana provides collateral-free business loans up to 10 Lakh rupees for micro and small enterprises. "
                "Loans are categorized into Shishu up to 50,000 rupees, Kishor up to 5 Lakhs, and Tarun up to 10 Lakhs."
            ),
            "pmmy": (
                "Pradhan Mantri Mudra Yojana provides collateral-free business loans up to 10 Lakh rupees for micro and small enterprises. "
                "Loans are categorized into Shishu up to 50,000 rupees, Kishor up to 5 Lakhs, and Tarun up to 10 Lakhs."
            ),
            "scss": (
                "Senior Citizen Savings Scheme (SCSS) is a government savings option for individuals aged 60 and above. "
                "It offers high quarterly interest payouts, 5-year tenure expandable by 3 years, and tax benefit under Section 80C."
            ),
            "sgb": (
                "Sovereign Gold Bonds (SGB) are government securities denominated in grams of gold. "
                "They pay an annual interest of 2.5 percent plus gold value appreciation, with zero capital gains tax if held till 8-year maturity."
            ),
        }

        for key, description in schemes.items():
            if key in normalized:
                return description

        return (
            f"Government scheme '{scheme_name}' is available through nationalized banks and post offices. "
            "Please check eligibility criteria, required documents like Aadhaar and PAN card, and visit your nearest bank branch or official portal."
        )

    @function_tool
    async def check_fraud_risk(
        self, context: RunContext, scenario_description: str
    ) -> str:
        """Evaluate a financial situation or message for potential fraud and scam risks.

        Args:
            scenario_description: Description of the call, SMS, email, or offer received by the user.
        """
        logger.info(f"Evaluating fraud risk for: {scenario_description}")
        desc = scenario_description.lower()

        if any(
            term in desc for term in ["otp", "pin", "cvv", "password", "card number"]
        ):
            return (
                "HIGH RISK FRAUD WARNING: No legitimate bank, RBI official, or customer care agent will EVER ask for your OTP, PIN, password, or CVV. "
                "Do NOT share any code. Disconnect the call immediately. If shared, block your card and call your bank hotline right away."
            )
        if any(
            term in desc
            for term in [
                "anydesk",
                "teamviewer",
                "rustdesk",
                "quicksupport",
                "screen share",
            ]
        ):
            return (
                "HIGH RISK SCAM ALERT: Scammers ask victims to install screen sharing apps like AnyDesk or TeamViewer to steal banking credentials. "
                "Do not install any app requested by strangers. Uninstall it immediately and disconnect your internet."
            )
        if any(
            term in desc
            for term in [
                "kyc update",
                "electricity bill",
                "sim block",
                "suspend account",
            ]
        ):
            return (
                "HIGH RISK PHISHING WARNING: Messages claiming your account, SIM, or electricity will be blocked unless you click a link or make a urgent payment are fake. "
                "Never click links in SMS or WhatsApp messages. Contact your service provider directly using their official website or bill statement."
            )
        if any(
            term in desc
            for term in [
                "guaranteed return",
                "double money",
                "youtube like",
                "work from home job",
                "part time job",
                "task complete",
            ]
        ):
            return (
                "HIGH RISK INVESTMENT FRAUD: Offers promising guaranteed high returns, doubling money, or paying cash for liking videos are classic financial scams. "
                "Never send money or join Telegram groups offering guaranteed profits."
            )

        return (
            "MODERATE RISK ADVISORY: Always verify unexpected financial requests. "
            "Never share credentials or click unknown links. If you suspect cyber fraud in India, immediately dial helpline 1930 or report on cybercrime.gov.in."
        )

    @function_tool
    async def explain_banking_term(self, context: RunContext, term: str) -> str:
        """Explain a banking or financial term in simple everyday language.

        Args:
            term: Banking concept or financial term (e.g., 'KYC', 'UPI', 'CIBIL', 'FD', 'RD', 'NEFT', 'IMPS', 'Repo rate').
        """
        logger.info(f"Explaining banking term: {term}")
        t = term.lower().strip()

        terms = {
            "kyc": "KYC stands for Know Your Customer. It is a process where banks verify your identity using official documents like Aadhaar card and PAN card to prevent money laundering and identity theft.",
            "upi": "UPI stands for Unified Payments Interface. It allows you to instantly transfer money between bank accounts 24/7 using a smartphone app and a virtual payment address without entering full bank account details.",
            "cibil": "CIBIL score is a 3-digit number between 300 and 900 that represents your creditworthiness. A score above 750 helps you get loans and credit cards quickly with better interest rates.",
            "credit score": "Credit score is a numerical rating of your credit history. Paying credit bills and loan EMIs on time keeps your credit score healthy.",
            "fd": "Fixed Deposit (FD) is a safe investment where you deposit money with a bank for a fixed period at a guaranteed interest rate higher than a regular savings account.",
            "rd": "Recurring Deposit (RD) allows you to deposit a fixed amount of money every month into your bank account and earn guaranteed interest over a chosen period.",
            "repo rate": "Repo rate is the interest rate at which the central bank lends money to commercial banks. When repo rate increases, bank loan interest rates usually increase too.",
        }

        for key, explanation in terms.items():
            if key in t:
                return explanation

        return f"{term} is a common financial concept. Ask your bank or financial advisor for specific details regarding your account."

    def _resolve_user_id(self, context: RunContext, user_id: str) -> str:
        if (
            user_id
            and user_id.strip()
            and user_id.strip().lower() not in ["none", "unknown", "null", "undefined"]
        ):
            return user_id.strip()

        try:
            if context and hasattr(context, "session") and context.session:
                room = getattr(context.session, "room", None)
                if room and hasattr(room, "remote_participants") and room.remote_participants:
                    for p in room.remote_participants.values():
                        if p.identity:
                            return p.identity
        except Exception as e:
            logger.warning(f"Failed to resolve participant identity from room: {e}")

        return "caller_default"

    @function_tool
    async def lookup_caller_memory(
        self, context: RunContext, user_id: str = ""
    ) -> str:
        """Lookup persistent caller memory in SQLite database.
        Returns the caller's saved name, language preference, financial facts, and last interaction timestamp if found.

        Args:
            user_id: Caller or user ID string. If empty, uses the current participant identity.
        """
        target_id = self._resolve_user_id(context, user_id)
        logger.info(f"Looking up memory for user_id='{target_id}'")
        try:
            res = lookup_caller(target_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error in lookup_caller_memory tool: {e}", exc_info=True)
            return json.dumps({"exists": False, "error": str(e)})

    @function_tool
    async def save_caller_memory(
        self,
        context: RunContext,
        user_id: str = "",
        name: str = "",
        language_preference: str = "",
        fact_key: str = "",
        fact_value: str = "",
    ) -> str:
        """Save caller information or financial facts to persistent SQLite memory.
        CRITICAL MANDATORY RULE: You MUST ONLY call this function AFTER asking the caller for explicit permission ('Would you like me to save that?') and receiving user consent ('YES'). NEVER call silently.

        Args:
            user_id: Caller or user ID string. If empty, uses current participant identity.
            name: Caller's name if provided and consented.
            language_preference: Caller's preferred language.
            fact_key: Key for financial fact (e.g. 'scheme_checked', 'eligibility_status', 'financial_goal').
            fact_value: Non-sensitive fact value (e.g. 'PMJDY', 'Eligible for zero-balance account and 2 Lakh insurance'). DO NOT include bank/Aadhaar/PAN/OTP/passwords.
        """
        target_id = self._resolve_user_id(context, user_id)
        logger.info(
            f"Saving caller memory for user_id='{target_id}', name='{name}', lang='{language_preference}', fact=('{fact_key}': '{fact_value}')"
        )
        try:
            facts = {}
            if fact_key and fact_value:
                facts[fact_key] = fact_value

            res = save_caller_memory_db(
                user_id=target_id,
                name=name if name else None,
                language_preference=language_preference if language_preference else None,
                facts=facts if facts else None,
            )
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error in save_caller_memory tool: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})


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
stt=deepgram.STT(
    model="nova-3",
    language="multi",
),        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
       tts=murf.TTS(
    voice="hi-IN-anisha",
    style="Conversation",
    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
    text_pacing=True,
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

    # Join the room and connect to the user FIRST, before generating any reply
    await ctx.connect()

    # Look up caller memory directly in Python (not as an LLM tool call) so the
    # very first LLM turn is a plain greeting, never a function call.
    # Gemini requires a function call to come right after a user turn or a
    # function-response turn — calling a tool as the agent's first-ever turn
    # violates that and causes a 400 "function call turn" error.
    caller_id = "caller_default"
    if ctx.room and ctx.room.remote_participants:
        for p in ctx.room.remote_participants.values():
            if p.identity:
                caller_id = p.identity
                break

    try:
        memory = lookup_caller(caller_id)
    except Exception as e:
        logger.warning(f"Caller memory lookup failed: {e}")
        memory = {"exists": False}

    if memory.get("exists"):
        greeting_instructions = (
            f"The caller has been here before. Their saved info: {json.dumps(memory, ensure_ascii=False)}. "
            "Greet them warmly by their saved name in their preferred language if known "
            "(e.g. 'Namaste Ramesh, welcome back!'), reference their saved facts naturally, "
            "and ask if they'd like to continue from last time. Do not call any tools for this greeting."
        )
    else:
        greeting_instructions = (
            "This is a new caller with no saved memory. Introduce yourself as FinGuide, "
            "your AI Financial Guidance Assistant, and ask how you can help them today. "
            "Do not call any tools for this greeting."
        )

    await session.generate_reply(instructions=greeting_instructions)


if __name__ == "__main__":
    cli.run_app(server)