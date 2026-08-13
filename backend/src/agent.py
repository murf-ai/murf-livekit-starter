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
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

try:
    from prompt import SYSTEM_PROMPT
except ImportError:
    from src.prompt import SYSTEM_PROMPT

try:
    import db
except ImportError:
    import src.db as db


class Assistant(Agent):
    def __init__(self, user_id: str, instructions: str = SYSTEM_PROMPT) -> None:
        super().__init__(instructions=instructions)
        self.user_id = user_id
        self.outcome_type = "none"
        self.language = "English"
        self.failure_type = "none"

    @function_tool
    async def lookup_caller(self) -> str:
        """Looks up the current caller's details and saved facts in the database.
        Always execute this tool at the very beginning of the call to check if they are a returning caller.
        """
        logger.info(f"Tool lookup_caller called for current user: {self.user_id}")
        user_info = db.get_user(self.user_id)
        if user_info:
            import json

            return json.dumps(user_info)
        return f"No record found for user ID: {self.user_id}"

    @function_tool
    async def create_escalation(
        self,
        caller_name: str,
        situation: str,
        what_happened: str,
        urgency: str,
        language: str,
        follow_up_method: str,
        contact_details: str,
        checked_facts: dict | None = None,
    ) -> str:
        """Creates a human support request/escalation in the database when the caller reports fraud or requests a manual decision.
        Always verify the caller has given verbal permission/consent before calling this.
        Do NOT save credit card numbers, passwords, OTPs, PINs, or account numbers in the what_happened details.

        Args:
            caller_name: The caller's name.
            situation: Short description of the reason, e.g. "Fraud Reporting" or "Manual Approval Request".
            what_happened: Detailed explanation of the caller's concern.
            urgency: How urgent this issue is. Must be exactly one of: "Low", "Medium", "High", "Emergency".
            language: The caller's preferred language.
            follow_up_method: The caller's preferred contact method (e.g., Phone Call, SMS, Email).
            contact_details: Phone number or email to reach them.
            checked_facts: Key-value facts/context the agent already checked.
        """
        self.outcome_type = "escalation"
        if language:
            self.language = language
        if checked_facts is None:
            checked_facts = {}
        logger.info(
            f"Tool create_escalation called for user_id: {self.user_id}, name: {caller_name}"
        )
        ref_id = db.create_escalation(
            caller_id=self.user_id,
            caller_name=caller_name,
            situation=situation,
            what_happened=what_happened,
            checked_facts=checked_facts,
            urgency=urgency,
            language=language,
            follow_up_method=follow_up_method,
            contact_details=contact_details,
        )
        return ref_id

    @function_tool
    async def save_caller_facts(
        self, name: str, language_preference: str, facts: dict
    ) -> str:
        """Saves current caller's details and facts (e.g. checked schemes, eligibility answers) to the database.
        Always verify the caller has given verbal permission/consent before calling this.

        Args:
            name: The caller's name.
            language_preference: The caller's preferred language (e.g., Hindi, English, Hinglish).
            facts: A dictionary of key-value pairs representing facts about the caller (e.g., eligibility, schemes checked). Do not store account or ID numbers.
        """
        self.outcome_type = "saved_facts"
        if language_preference:
            self.language = language_preference
        logger.info(
            f"Tool save_caller_facts called for user_id: {self.user_id}, name: {name}"
        )
        # Clean facts from any ID numbers or account numbers
        cleaned_facts = {}
        for k, v in facts.items():
            if "id" in k.lower() or "account" in k.lower() or "number" in k.lower():
                continue
            cleaned_facts[k] = v

        db.save_user(self.user_id, name, language_preference, cleaned_facts)
        return f"Successfully saved details for user {name} (ID: {self.user_id})."

    @function_tool
    async def check_scheme_eligibility(
        self,
        scheme_name: str,
        age: int,
        is_income_tax_payer: bool = False,
        girl_child_age: int = -1,
        is_indian_resident: bool = True,
    ) -> str:
        """Checks the eligibility of a caller for a specific Indian government financial scheme and returns the required document checklist.

        Only call this tool when the caller explicitly asks about their eligibility, required documents, or interest rates/premiums for one of the supported schemes: PMJDY, PMSBY, PMJJBY, APY, or SSY, AND you have gathered the necessary parameters (such as age, tax payer status, or girl child details). Do NOT call this tool for general conversations or if you don't know which scheme they are interested in.

        Args:
            scheme_name: The abbreviation of the scheme name to check. Must be exactly one of: "PMJDY", "PMSBY", "PMJJBY", "APY", "SSY".
            age: The beneficiary's age in years.
            is_income_tax_payer: True if the beneficiary pays income tax, False otherwise. (Important for APY eligibility).
            girl_child_age: The age of the girl child in years. (Mandatory when checking Sukanya Samriddhi Yojana / SSY). Use -1 if not applicable.
            is_indian_resident: True if the beneficiary is a resident of India, False otherwise.
        """
        import json
        from datetime import datetime

        today_str = datetime.now().strftime("%B %d, %Y")

        try:
            # SIMULATE TRANSIENT FAILURE (Step 4 & user request)
            # The first call to this tool in the session will fail, and subsequent retries will succeed.
            attempts = getattr(self, "_eligibility_attempts", 0) + 1
            self._eligibility_attempts = attempts
            if attempts == 1:
                self.failure_type = "tool_failure"
                raise Exception("API Connection Timeout (Simulated Transient Error)")

            logger.info(
                f"Tool check_scheme_eligibility called (Attempt {attempts}) for scheme: {scheme_name}, user_id: {self.user_id}"
            )
            self.outcome_type = "eligibility_check"
            name_upper = scheme_name.upper().strip()
            supported_schemes = ["PMJDY", "PMSBY", "PMJJBY", "APY", "SSY"]

            if name_upper not in supported_schemes:
                return json.dumps(
                    {
                        "eligible": False,
                        "reason": (
                            f"Scheme '{scheme_name}' is not supported. Supported"
                            f" schemes are: {', '.join(supported_schemes)}."
                        ),
                        "document_checklist": [],
                        "scheme_benefits": {},
                        "data_last_updated": today_str,
                        "error": f"Unsupported scheme: {scheme_name}",
                    }
                )

            if not is_indian_resident:
                return json.dumps(
                    {
                        "eligible": False,
                        "reason": (
                            f"Only Indian residents are eligible for {name_upper}."
                        ),
                        "document_checklist": [],
                        "scheme_benefits": {},
                        "data_last_updated": today_str,
                    }
                )

            if name_upper == "PMJDY":
                # Pradhan Mantri Jan Dhan Yojana
                is_eligible = age >= 10
                reason = (
                    "Eligible. Open to any resident Indian citizen aged 10 or"
                    " above. (Designed for individuals who do not have any other"
                    " bank account)."
                    if is_eligible
                    else ("Ineligible. Min age to open PMJDY account is 10 years.")
                )
                docs = [
                    "Aadhaar Card (primary KYC)",
                    "PAN Card (if available)",
                    (
                        "Or other officially valid document (Voter ID, driving"
                        " license, NREGA card)"
                    ),
                ]
                benefits = {
                    "benefits_and_interest": (
                        "Basic savings account with zero minimum balance"
                        " requirement, earn interest on savings deposit (approx"
                        " 2.70% to 3.00% p.a. depending on bank), free Rupay"
                        " debit card with built-in Rs 2 Lakh accidental insurance"
                        " cover, and overdraft facility up to Rs 10,000 for"
                        " eligible accounts."
                    )
                }

            elif name_upper == "PMSBY":
                # Pradhan Mantri Suraksha Bima Yojana
                is_eligible = 18 <= age <= 70
                reason = (
                    "Eligible. Open to individuals aged between 18 and 70 years."
                    if is_eligible
                    else (
                        f"Ineligible. Age must be between 18 and 70 years."
                        f" Provided age: {age}."
                    )
                )
                docs = [
                    "Aadhaar Card (primary KYC)",
                    "Savings bank account details",
                    "Consent form for auto-debit of premium",
                ]
                benefits = {
                    "premium": "Rs 20 per annum (auto-debited from savings account)",
                    "insurance_cover": (
                        "Rs 2 Lakh for accidental death or total permanent"
                        " disability, and Rs 1 Lakh for partial permanent"
                        " disability."
                    ),
                    "validity": ("1 year (June 1 to May 31), auto-renewed annually."),
                }

            elif name_upper == "PMJJBY":
                # Pradhan Mantri Jeevan Jyoti Bima Yojana
                is_eligible = 18 <= age <= 50
                reason = (
                    "Eligible. Open to individuals aged between 18 and 50 years."
                    if is_eligible
                    else (
                        f"Ineligible. Age must be between 18 and 50 years."
                        f" Provided age: {age}."
                    )
                )
                docs = [
                    "Aadhaar Card (primary KYC)",
                    "Savings bank account details",
                    "Consent form for auto-debit of premium",
                    "Self-declaration of good health (if enrolling late)",
                ]
                benefits = {
                    "premium": ("Rs 436 per annum (auto-debited from savings account)"),
                    "insurance_cover": (
                        "Rs 2 Lakh life insurance cover for death due to any cause."
                    ),
                    "validity": (
                        "1 year (June 1 to May 31), auto-renewed annually. Risk"
                        " cover continues up to age 55 if enrolled by 50."
                    ),
                }

            elif name_upper == "APY":
                # Atal Pension Yojana
                if is_income_tax_payer:
                    is_eligible = False
                    reason = (
                        "Ineligible. Income tax payers are not eligible to join"
                        " Atal Pension Yojana (rule effective since October 1,"
                        " 2022)."
                    )
                else:
                    is_eligible = 18 <= age <= 40
                    reason = (
                        "Eligible. Open to all non-taxpaying citizens aged"
                        " between 18 and 40 years."
                        if is_eligible
                        else (
                            "Ineligible. Age must be between 18 and 40 years to"
                            f" enroll. Provided age: {age}."
                        )
                    )
                docs = [
                    "Aadhaar Card (primary KYC)",
                    "Mobile number",
                    "Savings bank account details",
                    "Auto-debit authorization form",
                ]
                benefits = {
                    "premium": ("Varies based on entry age and selected pension slab."),
                    "pension_benefit": (
                        "Guaranteed minimum pension of Rs 1,000, Rs 2,000, Rs"
                        " 3,000, Rs 4,000, or Rs 5,000 per month after age 60,"
                        " depending on contributions."
                    ),
                    "co_contribution": (
                        "Government co-contribution is not available for new"
                        " subscribers, but the pension amount is fully"
                        " guaranteed by the Government of India."
                    ),
                }

            elif name_upper == "SSY":
                # Sukanya Samriddhi Yojana
                if girl_child_age == -1:
                    return json.dumps(
                        {
                            "eligible": "uncertain",
                            "reason": (
                                "Please provide the age of the girl child using the"
                                " 'girl_child_age' parameter."
                            ),
                            "document_checklist": [],
                            "scheme_benefits": {},
                            "data_last_updated": today_str,
                        }
                    )
                is_eligible = 0 <= girl_child_age <= 10
                reason = (
                    "Eligible. Open for girl child aged 10 years or below."
                    if is_eligible
                    else (
                        "Ineligible. The account can only be opened for a girl"
                        " child aged 10 years or below. Provided girl child"
                        " age: "
                        f"{girl_child_age}."
                    )
                )
                docs = [
                    "Birth certificate of the girl child (mandatory)",
                    "Aadhaar Card and PAN Card of the parent/guardian",
                    "Photograph of the girl child and parent",
                    "Proof of address",
                ]
                benefits = {
                    "interest_rate": (
                        "8.2% per annum (compounded annually, tax-free"
                        " interest, interest rate updated for fiscal year"
                        f" 2025-2026 as of {today_str})"
                    ),
                    "tax_benefits": (
                        "Triple tax exemption under Section 80C of the Income Tax Act."
                    ),
                    "maturity": (
                        "Matures after 21 years from account opening or upon"
                        " marriage of the girl child after she reaches 18 years."
                    ),
                }

            return json.dumps(
                {
                    "eligible": is_eligible,
                    "reason": reason,
                    "document_checklist": docs,
                    "scheme_benefits": benefits,
                    "data_last_updated": today_str,
                }
            )

        except Exception as e:
            logger.error(f"Error checking scheme eligibility: {e}")
            return json.dumps(
                {
                    "eligible": "error",
                    "reason": (
                        "The eligibility checker system is temporarily"
                        " experiencing technical issues. Please check the inputs or"
                        " try again shortly."
                    ),
                    "document_checklist": [],
                    "scheme_benefits": {},
                    "data_last_updated": today_str,
                    "error": str(e),
                }
            )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize SQLite database
    db.init_db()

    # Retrieve the participant's identity and detect if it is a SIP call
    user_id = "unknown_user"
    is_sip = ctx.room.name.startswith("outbound_call_room")
    for p_identity, p_info in ctx.room.remote_participants.items():
        user_id = p_identity
        if p_info.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            is_sip = True
        break

    logger.info(f"Active connection with user_id: {user_id}, is_sip: {is_sip}")

    import random

    schemes_list = [
        "Pradhan Mantri Jan Dhan Yojana",
        "Pradhan Mantri Suraksha Bima Yojana",
        "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "Atal Pension Yojana",
        "Sukanya Samriddhi Yojana",
    ]
    selected_scheme = random.choice(schemes_list)

    if is_sip:
        instructions = (
            f"{SYSTEM_PROMPT}\n\n"
            "OUTBOUND CALL SCENARIO:\n"
            "- Ignore any default returning caller logic. Do NOT check for returning caller facts or greet them by name at the start.\n"
            "- IMPORTANT: You MUST strictly open the conversation with these first two sentences in English:\n"
            "  1. 'Hello, this is Shreya calling from Jan Sahay.'\n"
            f"  2. 'We found you eligible for the {selected_scheme} scheme, and the deadline is on August 15th, so hurry up! If you want to know more, say yes, and if you want to stop these calls, say no.'\n"
            f"- If the user says 'yes', you must explain the eligibility criteria for ONLY the {selected_scheme} scheme in EXACTLY ONE SHORT SENTENCE (under 15 words). Do NOT explain any other schemes and do NOT use long paragraphs.\n"
            "- IMPORTANT: To avoid speaking all at once, you MUST speak slowly and keep your responses extremely short (under 15 words).\n"
            "- If the user says 'no', you must wrap up the call. If they ask how to stop these types of calls, reply exactly: 'To stop these calls, press or say 1.'\n"
            "- Do not ask any questions during the main explanation.\n"
            "- Do not say anything else in your opening turn. Wait for the user's response after this opening."
        )
    else:
        instructions = (
            f"{SYSTEM_PROMPT}\n\n"
            f"CURRENT USER CALL INFO:\n"
            f"- Current Caller User ID: {user_id}\n"
            f"- IMPORTANT: You MUST immediately call `lookup_caller` at the very start of the conversation. "
            f"If a record is returned, welcome the user back by name and reference their previous interaction "
            f"(e.g. 'नमस्ते Ramesh जी, पिछली बार हमने आपके Atal Pension Yojana के बारे में बात की थी। क्या उससे जुड़ा कोई सवाल है?'). "
            f"If no record is found, greet them as a new user."
        )

    # Log the start of the call
    channel = "SIP" if is_sip else "Browser"
    call_id = None
    try:
        call_id = db.start_call(ctx.room.name, user_id, channel)
        logger.info(f"Logged start of call ID: {call_id} (Channel: {channel})")
    except Exception as e:
        logger.error(f"Failed to start call log: {e}")

    try:
        # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
        session = AgentSession(
            stt=deepgram.STT(model="nova-3", language="multi"),
            llm=google.LLM(
                model="gemini-3.5-flash",
            ),
            tts=murf.TTS(
                voice="Anisha",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True,
            ),
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=False,
        )

        agent_inst = Assistant(user_id=user_id, instructions=instructions)

        # Track turn latency dynamically
        import time

        user_speech_ended = 0
        latencies = []
        user_spoke = False

        @session.on("user_input_transcribed")
        def on_user_input(event):
            nonlocal user_speech_ended, user_spoke
            if event.is_final and event.transcript.strip():
                user_spoke = True
                user_speech_ended = time.time()
                logger.info(f"User finished speaking turn at {user_speech_ended}")

        @session.on("speech_created")
        def on_speech(event):
            nonlocal user_speech_ended, latencies
            if user_speech_ended > 0:
                latency = time.time() - user_speech_ended
                latencies.append(latency)
                logger.info(f"Agent speech created. Turn Latency: {latency:.2f}s")
                user_speech_ended = 0  # reset

        # Start the session, which initializes the voice pipeline and warms up the models
        await session.start(
            agent=agent_inst,
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

        # Register successful shutdown callback
        async def on_shutdown():
            try:
                avg_l = sum(latencies) / len(latencies) if latencies else 0.0
                out_type = getattr(agent_inst, "outcome_type", "none")
                lang = getattr(agent_inst, "language", "English")
                fail_type = getattr(agent_inst, "failure_type", "none")
                status = "success"

                if fail_type != "none":
                    status = "failed"
                elif not user_spoke:
                    status = "failed"
                    fail_type = "user_declined" if is_sip else "no_response"
                elif out_type == "none":
                    if is_sip:
                        status = "failed"
                        fail_type = "user_declined"
                    else:
                        status = "success"
                        fail_type = "incomplete_task"

                db.complete_call(
                    call_id=call_id,
                    status=status,
                    avg_latency=avg_l,
                    language=lang,
                    failure_type=fail_type,
                    outcome_type=out_type,
                )
                logger.info(
                    f"Logged completion of call ID: {call_id} (Status: {status}, Failure: {fail_type}, Outcome: {out_type})"
                )
            except Exception as e:
                logger.error(f"Failed to log call completion: {e}")

        ctx.add_shutdown_callback(on_shutdown)

        if is_sip:
            # Trigger the compliant 2-sentence opening greeting automatically for the outbound call
            await session.say(
                f"Hello, this is Sita calling from Jana Sahaya. "
                f"We found you eligible for the {selected_scheme} scheme, and the deadline is on August 15th, so hurry up! "
                f"If you want to know more, say yes, and if you want to stop these calls, say no.",
                allow_interruptions=True,
            )
    except Exception as e:
        logger.error(f"Error in my_agent session: {e}")
        if call_id:
            try:
                err_str = str(e).lower()
                fail_type = "api_error"
                if "db" in err_str or "database" in err_str or "sqlite" in err_str:
                    fail_type = "tool_failure"
                db.complete_call(
                    call_id=call_id,
                    status="failed",
                    error_message=str(e),
                    avg_latency=0.0,
                    language="English",
                    failure_type=fail_type,
                    outcome_type="none",
                )
                logger.info(
                    f"Logged failed status for call ID: {call_id} (Failure: {fail_type})"
                )
            except Exception as db_err:
                logger.error(f"Failed to log call failure: {db_err}")
        raise e


if __name__ == "__main__":
    cli.run_app(server)
