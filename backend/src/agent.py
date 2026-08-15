import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    AgentTask,
    JobContext,
    JobProcess,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.agents.llm import ChatContext
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


class SchemeSpecialistAgent(AgentTask[str]):
    def __init__(self, user_id: str, chat_ctx: ChatContext) -> None:
        user_info = db.get_user(user_id)
        facts_summary = ""
        if user_info:
            facts_summary = f"\nSAVED USER DETAILS AND FACTS:\nName: {user_info.get('name')}\nLanguage Preference: {user_info.get('language_preference')}\nFacts: {user_info.get('facts')}"

        instructions = (
            "ROLE & IDENTITY:\n"
            "- You are the Government Scheme Specialist for National Financial Literacy Council of India.\n"
            "- Your sole job is to help users with eligibility and document requirements for savings, insurance, and pension schemes:\n"
            "  1. Savings scheme: Pradhan Mantri Jan Dhan Yojana (PMJDY)\n"
            "  2. Accidental Insurance: Pradhan Mantri Suraksha Bima Yojana (PMSBY)\n"
            "  3. Life Insurance: Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)\n"
            "  4. Pension & Retirement: Atal Pension Yojana (APY)\n"
            "  5. Girl Child Welfare & Savings: Sukanya Samriddhi Yojana (SSY)\n"
            '- GREETING: When you take over, greet the user warmly and introduce yourself, mentioning these schemes. E.g. "Hello! I am your government scheme specialist. I can guide you through savings, insurance, and pension schemes like PMJDY, PMSBY, APY, and Sukanya Samriddhi Yojana."\n'
            "- LIMITS: Do not answer questions about crops, agriculture, PM-KISAN, or business/Mudra loans. If the user asks about those, or if their scheme queries are complete, call `return_to_main_assistant`.\n"
            "- Do not use markdown formatting (asterisks, bold, emojis). Keep responses short and conversational.\n"
            + facts_summary
        )
        super().__init__(instructions=instructions, chat_ctx=chat_ctx)
        self.user_id = user_id

    async def on_enter(self) -> None:
        logger.info("SchemeSpecialistAgent entered.")
        if self.session and self.session.room_io and self.session.room_io.room:
            local_p = self.session.room_io.room.local_participant
            if local_p:
                await local_p.set_attributes({"agent_id": "scheme_specialist_agent"})

    @function_tool
    async def check_scheme_eligibility(
        self,
        scheme_name: str,
        age: int,
        is_income_tax_payer: bool = False,
        girl_child_age: int = -1,
        is_indian_resident: bool = True,
    ) -> str:
        """Checks the eligibility of a caller for PMJDY, PMSBY, PMJJBY, APY, or SSY and returns required documents.

        Args:
            scheme_name: Must be exactly one of: "PMJDY", "PMSBY", "PMJJBY", "APY", "SSY".
            age: The beneficiary's age in years.
            is_income_tax_payer: True if the beneficiary pays income tax, False otherwise.
            girl_child_age: The age of the girl child in years (for SSY). Use -1 if not applicable.
            is_indian_resident: True if the beneficiary is a resident of India, False otherwise.
        """
        import json

        try:
            from schemes_data import evaluate_eligibility
        except ImportError:
            from src.schemes_data import evaluate_eligibility

        res = evaluate_eligibility(
            scheme_id=scheme_name.lower(),
            age=age,
            is_taxpayer=is_income_tax_payer,
            gender=None,
            land_holding_acres=None,
        )
        return json.dumps(res)

    @function_tool
    async def return_to_main_assistant(self) -> str:
        """Call this tool when the user's queries regarding savings, insurance, or pension schemes are resolved, or if they want to change the topic back to general questions."""
        logger.info("Returning to main assistant from SchemeSpecialistAgent.")
        self.complete("Scheme specialist work completed.")
        return "Returning to the main assistant."


class CropSpecialistAgent(AgentTask[str]):
    def __init__(self, user_id: str, chat_ctx: ChatContext) -> None:
        user_info = db.get_user(user_id)
        facts_summary = ""
        if user_info:
            facts_summary = f"\nSAVED USER DETAILS AND FACTS:\nName: {user_info.get('name')}\nLanguage Preference: {user_info.get('language_preference')}\nFacts: {user_info.get('facts')}"

        instructions = (
            "ROLE & IDENTITY:\n"
            "- You are the Crop and Agriculture Specialist.\n"
            "- Your sole job is to help farmers and citizens with agriculture-related questions and the PM Kisan Samman Nidhi (PM-KISAN) scheme.\n"
            '- GREETING: When you take over, introduce yourself, e.g. "Hello! I am your crop specialist. I can assist you with agriculture-related schemes like PM-KISAN, land holding requirements, and crop welfare."\n'
            "- LIMITS: Do not answer questions about general savings, insurance, pension, or business Mudra loans. If they ask about those or are done with crop queries, call `return_to_main_assistant`.\n"
            "- Do not use markdown formatting (asterisks, bold, emojis). Keep responses short and conversational.\n"
            + facts_summary
        )
        super().__init__(instructions=instructions, chat_ctx=chat_ctx)
        self.user_id = user_id

    async def on_enter(self) -> None:
        logger.info("CropSpecialistAgent entered.")
        if self.session and self.session.room_io and self.session.room_io.room:
            local_p = self.session.room_io.room.local_participant
            if local_p:
                await local_p.set_attributes({"agent_id": "crop_specialist_agent"})

    @function_tool
    async def check_crop_scheme_eligibility(
        self,
        age: int,
        land_holding_acres: float,
        is_income_tax_payer: bool = False,
    ) -> str:
        """Checks the eligibility of a caller for the PM-KISAN agriculture scheme.

        Args:
            age: The beneficiary's age in years.
            land_holding_acres: Land holding in acres. Must be greater than 0.
            is_income_tax_payer: True if the beneficiary pays income tax, False otherwise.
        """
        import json

        try:
            from schemes_data import evaluate_eligibility
        except ImportError:
            from src.schemes_data import evaluate_eligibility

        res = evaluate_eligibility(
            scheme_id="pm_kisan",
            age=age,
            is_taxpayer=is_income_tax_payer,
            land_holding_acres=land_holding_acres,
        )
        return json.dumps(res)

    @function_tool
    async def return_to_main_assistant(self) -> str:
        """Call this tool when the user's queries regarding crops, farming, or agriculture schemes are resolved, or if they want to change the topic back to general questions."""
        logger.info("Returning to main assistant from CropSpecialistAgent.")
        self.complete("Crop specialist work completed.")
        return "Returning to the main assistant."


class BusinessLoanSpecialistAgent(AgentTask[str]):
    def __init__(self, user_id: str, chat_ctx: ChatContext) -> None:
        user_info = db.get_user(user_id)
        facts_summary = ""
        if user_info:
            facts_summary = f"\nSAVED USER DETAILS AND FACTS:\nName: {user_info.get('name')}\nLanguage Preference: {user_info.get('language_preference')}\nFacts: {user_info.get('facts')}"

        instructions = (
            "ROLE & IDENTITY:\n"
            "- You are the Business Loan Specialist.\n"
            "- Your sole job is to help users with business expansion, entrepreneurship, micro-enterprise growth, and the Pradhan Mantri MUDRA Yojana (PMMY) scheme.\n"
            '- GREETING: When you take over, introduce yourself, e.g. "Hello! I am your business loan specialist. I can help you with micro-enterprise loans, Mudra scheme options, and business growth."\n'
            "- LIMITS: Do not answer questions about crops, agriculture, PM-KISAN, or general savings/pension/insurance schemes. If they ask about those or are done with loan queries, call `return_to_main_assistant`.\n"
            "- Do not use markdown formatting (asterisks, bold, emojis). Keep responses short and conversational.\n"
            + facts_summary
        )
        super().__init__(instructions=instructions, chat_ctx=chat_ctx)
        self.user_id = user_id

    async def on_enter(self) -> None:
        logger.info("BusinessLoanSpecialistAgent entered.")
        if self.session and self.session.room_io and self.session.room_io.room:
            local_p = self.session.room_io.room.local_participant
            if local_p:
                await local_p.set_attributes(
                    {"agent_id": "business_loan_specialist_agent"}
                )

    @function_tool
    async def check_business_loan_eligibility(
        self,
        age: int,
        is_income_tax_payer: bool = False,
    ) -> str:
        """Checks the eligibility of a caller for the Pradhan Mantri MUDRA Yojana (PMMY) business loan scheme.

        Args:
            age: The beneficiary's age in years.
            is_income_tax_payer: True if the beneficiary pays income tax, False otherwise.
        """
        import json

        try:
            from schemes_data import evaluate_eligibility
        except ImportError:
            from src.schemes_data import evaluate_eligibility

        res = evaluate_eligibility(
            scheme_id="pmmy", age=age, is_taxpayer=is_income_tax_payer
        )
        return json.dumps(res)

    @function_tool
    async def return_to_main_assistant(self) -> str:
        """Call this tool when the user's queries regarding business loans or Mudra scheme are resolved, or if they want to change the topic back to general questions."""
        logger.info("Returning to main assistant from BusinessLoanSpecialistAgent.")
        self.complete("Business loan specialist work completed.")
        return "Returning to the main assistant."


class Assistant(Agent):
    def __init__(self, user_id: str, instructions: str = SYSTEM_PROMPT) -> None:
        super().__init__(instructions=instructions)
        self.user_id = user_id
        self.outcome_type = "none"
        self.language = "English"
        self.failure_type = "none"

    async def on_enter(self) -> None:
        logger.info("Assistant entered.")
        if self.session and self.session.room_io and self.session.room_io.room:
            local_p = self.session.room_io.room.local_participant
            if local_p:
                await local_p.set_attributes({"agent_id": "assistant"})

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
    async def handoff_to_crop_specialist(self) -> str:
        """Handoff the conversation to the Crop Specialist when the user asks about crops, farming, agriculture, land-holding, or the PM-KISAN scheme."""
        logger.info("Handoff to CropSpecialistAgent triggered.")
        try:
            await self.session.say(
                "I will connect you to our crop specialist.", allow_interruptions=True
            )
            specialist = CropSpecialistAgent(
                user_id=self.user_id, chat_ctx=self.chat_ctx.copy()
            )
            await specialist
            return "Handoff to crop specialist completed."
        except Exception as e:
            logger.error(f"Handoff to crop specialist failed: {e}")
            return f"I'm sorry, I was unable to connect you to our crop specialist: {e}. I can help you with your question."

    @function_tool
    async def handoff_to_business_loan_specialist(self) -> str:
        """Handoff the conversation to the Business Loan Specialist when the user asks about Mudra loans, micro-enterprise loans, business growth, or PMMY."""
        logger.info("Handoff to BusinessLoanSpecialistAgent triggered.")
        try:
            await self.session.say(
                "I will connect you to our business loan specialist.",
                allow_interruptions=True,
            )
            specialist = BusinessLoanSpecialistAgent(
                user_id=self.user_id, chat_ctx=self.chat_ctx.copy()
            )
            await specialist
            return "Handoff to business loan specialist completed."
        except Exception as e:
            logger.error(f"Handoff to business loan specialist failed: {e}")
            return f"I'm sorry, I was unable to connect you to our business loan specialist: {e}. I can help you with your question."

    @function_tool
    async def handoff_to_scheme_specialist(self) -> str:
        """Handoff the conversation to the Government Scheme Specialist when the user asks about general savings, insurance, pension, or schemes like PMJDY, PMSBY, PMJJBY, APY, or SSY."""
        logger.info("Handoff to SchemeSpecialistAgent triggered.")
        try:
            await self.session.say(
                "I will connect you to our government scheme specialist.",
                allow_interruptions=True,
            )
            specialist = SchemeSpecialistAgent(
                user_id=self.user_id, chat_ctx=self.chat_ctx.copy()
            )
            await specialist
            return "Handoff to government scheme specialist completed."
        except Exception as e:
            logger.error(f"Handoff to government scheme specialist failed: {e}")
            return f"I'm sorry, I was unable to connect you to our government scheme specialist: {e}. I can help you with your question."


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
                model="gemini-3.6-flash",
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
