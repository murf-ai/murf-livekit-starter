import logging
import json
from pathlib import Path

from datetime import datetime, timezone
from dotenv import load_dotenv
from livekit import rtc
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
from livekit.plugins import (
    deepgram,
    google,
    murf,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import asyncio

from prompt import SYSTEM_PROMPT, SCHEME_SPECIALIST_PROMPT
from escalation import create_escalation
from memory import lookup_caller, lookup_caller_memory, save_caller_memory, log_call_outcome


logger = logging.getLogger("agent")

load_dotenv(".env.local")


# ============================================================
# SCHEME FUNCTIONS (Shared logic)
# ============================================================

async def run_check_scheme_eligibility(
    age: int,
    occupation: str,
    approximate_annual_income: int,
    has_bank_account: bool,
    has_daughter_under_10: bool = False,
) -> str:
    """Determine which Indian government financial schemes a caller qualifies for."""

    logger.info(
        f"Checking scheme eligibility for age={age}, "
        f"occupation='{occupation}', "
        f"income={approximate_annual_income}, "
        f"bank_account={has_bank_account}, "
        f"daughter_under_10={has_daughter_under_10}"
    )

    try:
        data_file = Path(__file__).parent / "scheme_data.json"

        if not data_file.exists():
            raise FileNotFoundError(
                "Scheme data file scheme_data.json not found."
            )

        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        as_of_disclosure = data.get(
            "as_of",
            "official government scheme guidelines"
        )

        schemes_list = data.get("schemes", [])

        eligible_schemes = []

        occ_lower = str(occupation).lower().strip()

        for s in schemes_list:

            min_age = s.get("min_age", 0)
            max_age = s.get("max_age", 150)

            req_bank = s.get(
                "requires_bank_account",
                False
            )

            target_occ = s.get(
                "target_occupation"
            )

            req_daughter = s.get(
                "requires_daughter_under_10",
                False
            )

            if age < min_age or age > max_age:
                continue

            if req_bank and not has_bank_account:
                continue

            if req_daughter and not has_daughter_under_10:
                continue

            if (
                target_occ == "unorganized"
                and any(
                    k in occ_lower
                    for k in [
                        "salaried",
                        "corporate",
                        "government servant",
                        "it professional",
                    ]
                )
            ):
                continue

            if (
                target_occ == "business"
                and not any(
                    k in occ_lower
                    for k in [
                        "business",
                        "shop",
                        "micro",
                        "self-employed",
                        "artisan",
                        "entrepreneur",
                        "trader",
                        "vendor",
                        "farmer",
                        "worker",
                        "self",
                        "own",
                        "freelance",
                    ]
                )
            ):
                continue

            eligible_schemes.append(s)

        if not eligible_schemes:
            return (
                f"Based on eligibility criteria as of the scheme's "
                f"{as_of_disclosure}, no specific matched schemes "
                f"were found for your current profile. However, you "
                f"may still visit your nearest nationalized bank "
                f"branch or official government scheme portal for "
                f"personalized options."
            )

        response_parts = [
            "Based on your profile, here are the official government "
            "financial schemes you qualify for, eligibility criteria "
            f"as of the scheme's {as_of_disclosure}:"
        ]

        all_docs = set()

        for s in eligible_schemes:

            name = s["name"]
            desc = s["description"]
            docs = s.get("documents", [])

            all_docs.update(docs)

            response_parts.append(
                f"{name}: {desc}"
            )

        docs_list_str = ", ".join(
            sorted(list(all_docs))
        )

        response_parts.append(
            "To apply for these schemes, your document checklist "
            f"includes: {docs_list_str}. Please present these at "
            "your nearest bank branch or post office."
        )

        return " ".join(response_parts)

    except Exception as e:

        logger.error(
            f"Error checking scheme eligibility: {e}",
            exc_info=True
        )

        return (
            "I'm not able to check live eligibility data right now, "
            "but based on what I know, here's my best guidance. "
            "Please confirm with your bank or the official scheme portal."
        )


async def run_explain_scheme(scheme_name: str) -> str:
    logger.info(
        f"Explaining government scheme: {scheme_name}"
    )

    normalized = scheme_name.lower().strip()

    schemes = {

        "pmjdy": (
            "Pradhan Mantri Jan Dhan Yojana (PMJDY) offers a "
            "zero-balance bank account with a free RuPay debit card, "
            "accidental insurance cover up to 2 Lakh rupees, and an "
            "overdraft facility up to 10,000 rupees after 6 months."
        ),

        "jan dhan": (
            "Pradhan Mantri Jan Dhan Yojana (PMJDY) offers a "
            "zero-balance bank account with a free RuPay debit card, "
            "accidental insurance cover up to 2 Lakh rupees, and an "
            "overdraft facility up to 10,000 rupees after 6 months."
        ),

        "pmsby": (
            "Pradhan Mantri Suraksha Bima Yojana (PMSBY) is an "
            "accidental insurance scheme for ages 18 to 70. "
            "It offers 2 Lakh rupees cover for accidental death or "
            "total disability for a nominal annual premium of 20 rupees."
        ),

        "suraksha bima": (
            "Pradhan Mantri Suraksha Bima Yojana (PMSBY) is an "
            "accidental insurance scheme for ages 18 to 70. "
            "It offers 2 Lakh rupees cover for accidental death or "
            "total disability for a nominal annual premium of 20 rupees."
        ),

        "pmjjby": (
            "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY) "
            "provides life insurance cover of 2 Lakh rupees for death "
            "due to any cause. It is available for individuals aged "
            "18 to 50 for an annual premium of 436 rupees."
        ),

        "jeevan jyoti": (
            "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY) "
            "provides life insurance cover of 2 Lakh rupees for death "
            "due to any cause. It is available for individuals aged "
            "18 to 50 for an annual premium of 436 rupees."
        ),

        "apy": (
            "Atal Pension Yojana (APY) is a guaranteed pension scheme "
            "for unorganized sector workers aged 18 to 40. Subscribers "
            "receive a monthly pension of 1,000 to 5,000 rupees after "
            "age 60, depending on their contributions."
        ),

        "atal pension": (
            "Atal Pension Yojana (APY) is a guaranteed pension scheme "
            "for unorganized sector workers aged 18 to 40. Subscribers "
            "receive a monthly pension of 1,000 to 5,000 rupees after "
            "age 60, depending on their contributions."
        ),

        "sukanya samriddhi": (
            "Sukanya Samriddhi Yojana is a small savings scheme for "
            "a girl child below 10 years. It offers high interest rates, "
            "tax deductions under Section 80C, and tax-free returns. "
            "It matures when the girl turns 21 or gets married after 18."
        ),

        "ssy": (
            "Sukanya Samriddhi Yojana is a small savings scheme for "
            "a girl child below 10 years. It offers high interest rates, "
            "tax deductions under Section 80C, and tax-free returns. "
            "It matures when the girl turns 21 or gets married after 18."
        ),

        "mudra": (
            "Pradhan Mantri Mudra Yojana provides collateral-free "
            "business loans up to 10 Lakh rupees for micro and small "
            "enterprises. Loans are categorized into Shishu up to "
            "50,000 rupees, Kishor up to 5 Lakhs, and Tarun up to "
            "10 Lakhs."
        ),

        "pmmy": (
            "Pradhan Mantri Mudra Yojana provides collateral-free "
            "business loans up to 10 Lakh rupees for micro and small "
            "enterprises. Loans are categorized into Shishu up to "
            "50,000 rupees, Kishor up to 5 Lakhs, and Tarun up to "
            "10 Lakhs."
        ),

        "scss": (
            "Senior Citizen Savings Scheme (SCSS) is a government "
            "savings option for individuals aged 60 and above. "
            "It offers high quarterly interest payouts, 5-year tenure "
            "expandable by 3 years, and tax benefit under Section 80C."
        ),

        "sgb": (
            "Sovereign Gold Bonds (SGB) are government securities "
            "denominated in grams of gold. They pay an annual interest "
            "of 2.5 percent plus gold value appreciation, with zero "
            "capital gains tax if held till 8-year maturity."
        ),
    }

    for key, description in schemes.items():
        if key in normalized:
            return description

    return (
        f"Government scheme '{scheme_name}' is available through "
        "nationalized banks and post offices. Please check eligibility "
        "criteria and visit your nearest bank branch or official portal."
    )


# ============================================================
# GOVERNMENT SCHEME SPECIALIST AGENT
# ============================================================

class SchemeSpecialistAgent(Agent):

    def __init__(self) -> None:
        super().__init__(
            instructions=SCHEME_SPECIALIST_PROMPT
        )

    @function_tool
    async def check_scheme_eligibility(
        self,
        context: RunContext,
        age: int,
        occupation: str,
        approximate_annual_income: int,
        has_bank_account: bool,
        has_daughter_under_10: bool = False,
    ) -> str:
        """Determine which Indian government financial schemes a caller qualifies for."""
        return await run_check_scheme_eligibility(
            age, occupation, approximate_annual_income, has_bank_account, has_daughter_under_10
        )

    @function_tool
    async def explain_scheme(
        self,
        context: RunContext,
        scheme_name: str
    ) -> str:
        """Explain details and benefits of a specific Indian government financial scheme."""
        return await run_explain_scheme(scheme_name)


# ============================================================
# FINSAFE ASSISTANT (MAIN AGENT)
# ============================================================

class Assistant(Agent):

    create_escalation = create_escalation
    lookup_caller_memory = lookup_caller_memory
    save_caller_memory = save_caller_memory

    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT
        )

    @function_tool
    async def transfer_to_scheme_specialist(
        self,
        context: RunContext,
        scheme_query_summary: str = "",
    ) -> str:
        """Transfer caller to Government Scheme Specialist. MUST be called whenever the caller asks about eligibility for any government financial scheme, subsidy, welfare program, or scheme for small farmers/businesses."""
        logger.info(f"Handoff triggered: transferring to SchemeSpecialistAgent. Query summary: '{scheme_query_summary}'")
        
        session = context.session
        
        # 1. Update participant attributes/metadata so the frontend knows active agent changed
        try:
            if session and hasattr(session, "room") and session.room and session.room.local_participant:
                asyncio.create_task(
                    session.room.local_participant.set_attributes({"active_agent": "Government Scheme Specialist"})
                )
        except Exception as e:
            logger.warning(f"Could not set participant attributes for handoff: {e}")

        # 2. Seamless Agent Handoff via session.update_agent
        if session:
            specialist = SchemeSpecialistAgent()
            session.update_agent(specialist)
            logger.info("Session agent updated to SchemeSpecialistAgent successfully.")
            return "Transferred caller to Government Scheme Specialist. The specialist is now active in the session with full context."
        
        return "Failed to switch agent - session not found."


    # ========================================================
    # FRAUD RISK
    # ========================================================

    @function_tool
    async def check_fraud_risk(
        self,
        context: RunContext,
        scenario_description: str
    ) -> str:

        logger.info(
            f"Evaluating fraud risk for: {scenario_description}"
        )

        desc = scenario_description.lower()

        if any(
            term in desc
            for term in [
                "otp",
                "pin",
                "cvv",
                "password",
                "card number",
            ]
        ):
            return (
                "HIGH RISK FRAUD WARNING: No legitimate bank, RBI official, "
                "or customer care agent will EVER ask for your OTP, PIN, "
                "password, or CVV. Do NOT share any code. Disconnect the "
                "call immediately. If shared, block your card and call "
                "your bank hotline right away."
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
                "HIGH RISK SCAM ALERT: Scammers ask victims to install "
                "screen sharing apps like AnyDesk or TeamViewer to steal "
                "banking credentials. Do not install any app requested by "
                "strangers. Uninstall it immediately and disconnect your internet."
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
                "HIGH RISK PHISHING WARNING: Messages claiming your "
                "account, SIM, or electricity will be blocked unless you "
                "click a link or make an urgent payment are fake. Never "
                "click links in SMS or WhatsApp messages. Contact your "
                "service provider directly using their official website "
                "or bill statement."
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
                "HIGH RISK INVESTMENT FRAUD: Offers promising guaranteed "
                "high returns, doubling money, or paying cash for liking "
                "videos are classic financial scams. Never send money or "
                "join Telegram groups offering guaranteed profits."
            )

        return (
            "MODERATE RISK ADVISORY: Always verify unexpected financial "
            "requests. Never share credentials or click unknown links. "
            "If you suspect cyber fraud in India, immediately dial "
            "helpline 1930 or report on cybercrime.gov.in."
        )

    # ========================================================
    # BANKING TERMS
    # ========================================================

    @function_tool
    async def explain_banking_term(
        self,
        context: RunContext,
        term: str
    ) -> str:

        logger.info(
            f"Explaining banking term: {term}"
        )

        t = term.lower().strip()

        terms = {

            "kyc": (
                "KYC stands for Know Your Customer. It is a process where "
                "banks verify your identity using official documents like "
                "Aadhaar card and PAN card to prevent money laundering and "
                "identity theft."
            ),

            "upi": (
                "UPI stands for Unified Payments Interface. It allows you "
                "to instantly transfer money between bank accounts 24/7 "
                "using a smartphone app and a virtual payment address "
                "without entering full bank account details."
            ),

            "cibil": (
                "CIBIL score is a 3-digit number between 300 and 900 that "
                "represents your creditworthiness. A score above 750 helps "
                "you get loans and credit cards quickly with better "
                "interest rates."
            ),

            "credit score": (
                "Credit score is a numerical rating of your credit history. "
                "Paying credit bills and loan EMIs on time keeps your "
                "credit score healthy."
            ),

            "fd": (
                "Fixed Deposit, or FD, is a safe investment where you "
                "deposit money with a bank for a fixed period at a "
                "guaranteed interest rate higher than a regular savings account."
            ),

            "rd": (
                "Recurring Deposit, or RD, allows you to deposit a fixed "
                "amount of money every month into your bank account and "
                "earn guaranteed interest over a chosen period."
            ),

            "repo rate": (
                "Repo rate is the interest rate at which the central bank "
                "lends money to commercial banks. When repo rate increases, "
                "bank loan interest rates usually increase too."
            ),
        }

        for key, explanation in terms.items():

            if key in t:
                return explanation

        return (
            f"{term} is a common financial concept. Ask your bank or "
            "financial advisor for specific details regarding your account."
        )


# ============================================================
# LIVEKIT SERVER
# ============================================================

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


# ============================================================
# AGENT SESSION
# ============================================================

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    logger.info(
        f"Starting FinSafe agent for room: {ctx.room.name}"
    )

    # --------------------------------------------------------
    # Call outcome state setup
    # --------------------------------------------------------
    call_id = ctx.room.name or f"call_{id(ctx)}"
    call_state = {
        "outcome": "failed",
        "reason": "dropped",
        "has_user_spoken": False,
    }

    async def on_shutdown():
        t1 = datetime.now(timezone.utc).isoformat()
        logger.info(f"[TIMESTAMP DEBUG 1b/1c] on_shutdown called at {t1} - logging outcome call_id={call_id}, outcome={call_state['outcome']}, reason={call_state['reason']}")
        log_call_outcome(
            call_id=call_id,
            outcome=call_state["outcome"],
            outcome_reason=call_state["reason"]
        )

    ctx.add_shutdown_callback(on_shutdown)

    # --------------------------------------------------------
    # Voice AI pipeline
    # --------------------------------------------------------

    session = AgentSession(

        stt=deepgram.STT(
            model="nova-3"
        ),

        llm=google.LLM(
            model="gemini-3.1-flash-lite",
        ),

        tts=murf.TTS(
            voice="en-IN-pooja",
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        turn_detection=MultilingualModel(),

        vad=ctx.proc.userdata["vad"],

        preemptive_generation=True,
    )

    # Track user interactions or tool calls for outcome tracking
    @ctx.room.on("data_received")
    def _on_room_data_received(data_packet):
        logger.info(f"[EVENT LOG] room data_received fired: participant={getattr(data_packet, 'participant', None)}")
        call_state["has_user_spoken"] = True

    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev):
        transcript = getattr(ev, "transcript", "")
        is_final = getattr(ev, "is_final", False)
        logger.info(f"[EVENT LOG] user_input_transcribed fired: transcript='{transcript}', is_final={is_final}")
        if transcript.strip():
            call_state["has_user_spoken"] = True

    @session.on("user_state_changed")
    def _on_user_state_changed(ev):
        new_state = getattr(ev, "new_state", "")
        logger.info(f"[EVENT LOG] user_state_changed fired: old={getattr(ev, 'old_state', '')}, new={new_state}")
        if new_state == "speaking":
            call_state["has_user_spoken"] = True

    @session.on("conversation_item_added")
    def _on_conversation_item_added(ev):
        item = getattr(ev, "item", None)
        role = getattr(item, "role", None)
        role_str = str(role).lower() if role else ""
        logger.info(f"[EVENT LOG] conversation_item_added fired: role={role_str}, item={item}")
        if role_str == "user":
            call_state["has_user_spoken"] = True
        elif role_str == "assistant":
            # Once the agent successfully delivers a response to the caller AFTER user has spoken,
            # mark as answered_directly if not already set to escalation
            if call_state["has_user_spoken"] and call_state["outcome"] != "success":
                call_state["outcome"] = "success"
                call_state["reason"] = "answered_directly"
                logger.info(f"[EVENT LOG] Outcome updated to SUCCESS (answered_directly)")

    @session.on("tool_executed")
    def _on_tool_executed(event):
        # Check tool execution results for escalation status
        tool_name = getattr(event, "tool_name", "") or getattr(getattr(event, "tool", None), "__name__", "")
        result = getattr(event, "result", None)
        logger.info(f"[EVENT LOG] tool_executed fired: tool_name={tool_name}, result={result}")
        if "escalation" in str(tool_name).lower() or (isinstance(result, dict) and "reference_id" in result):
            if isinstance(result, dict) and result.get("status") == "created":
                call_state["outcome"] = "success"
                call_state["reason"] = "escalated"
                logger.info(f"[EVENT LOG] Outcome updated to SUCCESS (escalated)")
            elif isinstance(result, dict) and result.get("status") == "failed":
                call_state["outcome"] = "failed"
                call_state["reason"] = "escalation_failed"

    @session.on("close")
    def _on_session_close(close_event):
        t0 = datetime.now(timezone.utc).isoformat()
        reason = getattr(close_event, "reason", "")
        reason_str = str(reason).lower()
        logger.info(f"[TIMESTAMP DEBUG 1a] session.close fired at {t0}: reason={reason_str}")
        if call_state["outcome"] != "success":
            if "user_initiated" in reason_str or "participant_disconnected" in reason_str:
                call_state["reason"] = "ended_early"
            elif "error" in reason_str:
                call_state["reason"] = "dropped"
            else:
                call_state["reason"] = "ended_early"
        t_classified = datetime.now(timezone.utc).isoformat()
        logger.info(f"[TIMESTAMP DEBUG 1b] classification complete at {t_classified}: outcome={call_state['outcome']}, reason={call_state['reason']}")
    # --------------------------------------------------------
    # Start session
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Connect to room FIRST
    # --------------------------------------------------------

    await ctx.connect()

    # --------------------------------------------------------
    # NOW detect SIP participant
    # --------------------------------------------------------

    is_sip = any(
        p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
        for p in ctx.room.remote_participants.values()
    )

    logger.info(
        f"FinSafe connection type: "
        f"{'SIP / Linphone' if is_sip else 'Browser'}"
    )

    # --------------------------------------------------------
    # Caller memory
    # --------------------------------------------------------

    caller_id = "caller_default"

    if ctx.room and ctx.room.remote_participants:

        for p in ctx.room.remote_participants.values():

            if p.identity:
                caller_id = p.identity
                break

    try:
        memory = lookup_caller(caller_id)

    except Exception as e:

        logger.warning(
            f"Caller memory lookup failed: {e}"
        )

        memory = {
            "exists": False
        }

    # --------------------------------------------------------
    # INITIAL GREETING
    # --------------------------------------------------------

    if is_sip:

        # ====================================================
        # LINPHONE / SIP GREETING
        # ====================================================

        logger.info(
            "Using outbound SIP greeting."
        )

        greeting_instructions = (
            "This is an outbound financial services call to a "
            "Linphone SIP user. "

            "Introduce yourself as FinSafe, an AI financial guidance "
            "assistant. "

            "Say clearly that this is a financial follow-up call. "

            "Ask politely whether this is a good time to talk. "

            "Keep the opening short, natural, friendly, and professional. "

            "Do not give a long explanation before asking the question. "

            "Do not ask for OTPs, PINs, passwords, CVVs, full card numbers, "
            "bank account numbers, Aadhaar numbers, or PAN numbers. "

            "Do not call any tools for this greeting."
        )

    else:

        # ====================================================
        # BROWSER GREETING
        # ====================================================

        logger.info(
            "Using normal browser greeting."
        )

        if memory.get("exists"):

            saved_name = memory.get("name") or ""
            saved_facts = memory.get("facts", [])
            facts_str = ", ".join(saved_facts) if saved_facts else ""

            greeting_instructions = (
                "This is a normal browser conversation. "

                "Introduce yourself as FinGuide, your AI Financial "
                "Guidance Assistant. "

                + (
                    f"Welcome back the caller by name ('{saved_name}'). "
                    if saved_name
                    else ""
                )

                + (
                    f"Mention briefly that you remember from last time: {facts_str}. "
                    if facts_str
                    else ""
                )

                + "Briefly explain that you can help with general "
                "financial education, budgeting, savings, banking "
                "concepts, government financial schemes, and financial "
                "safety. "

                "Do not mention previous conversations or saved information. "

                "Do not ask whether they want to continue from a previous "
                "conversation. "

                "Ask how you can help them today. "

                "Do not call any tools for this greeting."
            )

        else:

            greeting_instructions = (
                "This is a normal browser conversation. "

                "Introduce yourself as FinGuide, your AI Financial "
                "Guidance Assistant. "

                "Briefly explain that you can help with general financial "
                "education, budgeting, savings, banking concepts, "
                "government financial schemes, and financial safety. "

                "Ask how you can help them today. "

                "Do not call any tools for this greeting."
            )

    # --------------------------------------------------------
    # Generate initial greeting
    # --------------------------------------------------------

    await session.generate_reply(
        instructions=greeting_instructions
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    cli.run_app(server)