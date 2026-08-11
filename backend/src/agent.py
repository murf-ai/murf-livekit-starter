import logging
import random

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    UserInputTranscribedEvent,
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

try:
    import schemes_data
except ImportError:
    import src.schemes_data as schemes_data


class Assistant(Agent):
    def __init__(self, user_id: str, instructions: str = SYSTEM_PROMPT) -> None:
        super().__init__(instructions=instructions)
        self.user_id = user_id

    @function_tool
    async def lookup_caller(self) -> str:
        """Looks up the current caller's details and saved facts in the database.
        Always execute this tool at the very beginning of the call to check if they are a returning caller.
        """
        logger.info(f"Tool lookup_caller called for current user: {self.user_id}")
        user_info = db.get_user(self.user_id)
        if user_info:
            import json

            return json.dumps(user_info, ensure_ascii=False)
        return f"No record found for user ID: {self.user_id}"

    @function_tool
    async def save_caller_facts(
        self, name: str, language_preference: str, facts: dict
    ) -> str:
        """Saves current caller's details and facts (e.g. checked schemes, eligibility answers) to the database.
        Always verify the caller has given verbal permission/consent before calling this.

        Args:
            name: The caller's name.
            language_preference: The caller's preferred language (e.g., Kannada, English, Hindi).
            facts: A dictionary of key-value pairs representing facts about the caller (e.g., eligibility, schemes checked). Do not store account or ID numbers.
        """
        logger.info(
            f"Tool save_caller_facts called for user_id: {self.user_id}, name: {name}"
        )
        # Clean facts from any ID numbers or account numbers
        cleaned_facts = {}
        if isinstance(facts, dict):
            for k, v in facts.items():
                if "id" in k.lower() or "account" in k.lower() or "number" in k.lower():
                    continue
                cleaned_facts[k] = v

        db.save_user(self.user_id, name, language_preference, cleaned_facts)
        return f"Successfully saved details for user {name} (ID: {self.user_id})."

    @function_tool
    async def list_available_schemes(self) -> str:
        """Retrieves a catalog of all supported Indian financial and welfare government schemes.

        Call this tool when the caller asks what government schemes are available, wants to explore scheme options, or asks what financial programs Sita can help with.
        Do NOT call this tool if the user already specified a target scheme name or scheme ID.
        """
        import json

        logger.info("Tool list_available_schemes called.")
        res = schemes_data.list_all_schemes()
        return json.dumps(res, ensure_ascii=False)

    @function_tool
    async def check_scheme_eligibility(
        self,
        scheme_id: str,
        age: int | None = None,
        annual_income: float | None = None,
        is_taxpayer: bool | None = None,
        gender: str | None = None,
        land_holding_acres: float | None = None,
    ) -> str:
        """Evaluates official eligibility criteria for an Indian government financial scheme based on collected caller answers.

        Call this tool ONLY AFTER asking and collecting the caller's relevant personal details (age, tax-paying status, land holding, gender, etc.).
        Do NOT invoke this tool with assumed, placeholder, or invented values. Ask the caller first.

        Args:
            scheme_id: Scheme identifier code or name (e.g., 'pmjdy', 'pmsby', 'pmjjby', 'apy', 'ssy', 'pm_kisan', 'pmmy').
            age: Caller's age in years (or girl child's age for SSY).
            annual_income: Caller's total annual household income in Indian Rupees (INR).
            is_taxpayer: True if the caller or spouse pays income tax; False otherwise.
            gender: Caller's gender ('male', 'female', or 'other').
            land_holding_acres: Total agricultural land owned by caller in acres (required for PM-KISAN).
        """
        import json

        logger.info(
            f"Tool check_scheme_eligibility called for scheme_id={scheme_id}, age={age}, taxpayer={is_taxpayer}"
        )
        res = schemes_data.evaluate_eligibility(
            scheme_id=scheme_id,
            age=age,
            annual_income=annual_income,
            is_taxpayer=is_taxpayer,
            gender=gender,
            land_holding_acres=land_holding_acres,
        )
        return json.dumps(res, ensure_ascii=False)

    @function_tool
    async def get_scheme_document_checklist(self, scheme_id: str) -> str:
        """Retrieves the official list of mandatory documents and application instructions needed to apply for a specified government scheme.

        Call this tool when the user asks what documents, papers, or ID proofs are required to open an account or apply for a specific scheme (e.g. PMJDY, SSY, APY, PM-KISAN, PMSBY, PMJJBY, PMMY).

        Args:
            scheme_id: Scheme identifier code or name (e.g., 'pmjdy', 'pmsby', 'pmjjby', 'apy', 'ssy', 'pm_kisan', 'pmmy').
        """
        import json

        logger.info(
            f"Tool get_scheme_document_checklist called for scheme_id={scheme_id}"
        )
        res = schemes_data.get_document_checklist(scheme_id=scheme_id)
        return json.dumps(res, ensure_ascii=False)


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

    # Join the room and connect to LiveKit
    await ctx.connect()

    # Detect user identity and check if this is an outbound SIP call
    user_id = "unknown_user"
    is_sip = ctx.room.name.startswith("outbound_call_room")

    try:
        participant = await ctx.wait_for_participant()
        if participant:
            user_id = participant.identity
            if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                is_sip = True
    except Exception as e:
        logger.warning(f"Wait for participant timed out or failed: {e}")

    for p_identity, p_info in ctx.room.remote_participants.items():
        if user_id == "unknown_user":
            user_id = p_identity
        if p_info.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            is_sip = True
        break

    logger.info(f"Active connection with user_id: {user_id}, is_sip: {is_sip}")

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
            f"(e.g. 'Namaste Ramesh, last time we spoke about Atal Pension Yojana. Did you check your eligibility?'). "
            f"If no record is found, greet them as a new user."
        )

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-2.0-flash",
        ),
        tts=murf.TTS(
            voice="en-IN-anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=not is_sip,
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        # Check for Kannada script characters (native Kannada)
        has_kannada = any(0x0C80 <= ord(c) <= 0x0CFF for c in transcript)

        # Check for common Kannada keywords (Kannada script)
        kannada_keywords = {
            "ಏನು",
            "ಹೌದು",
            "ಇಲ್ಲ",
            "ನೀವು",
            "ನಾನು",
            "ಧನ್ಯವಾದ",
            "ಯೋಜನೆ",
            "ಸಹಾಯ",
            "ಬ್ಯಾಂಕ್",
            "ಬಿಮಾ",
            "ಪಿಂಚಣಿ",
            "ಅರ್ಜಿ",
            "ಹೇಳಿ",
            "ಸುರಕ್ಷೆ",
        }
        words = set(transcript.split())
        has_kannada_words = not words.isdisjoint(kannada_keywords)

        if has_kannada or has_kannada_words:
            logger.info(
                f"Detected Kannada speech: '{ev.transcript}'. Switching TTS to kn-IN-anisha."
            )
            session.tts.update_options(voice="kn-IN-anisha")
        else:
            logger.info(
                f"Detected English speech: '{ev.transcript}'. Switching TTS to en-IN-anisha."
            )
            session.tts.update_options(voice="en-IN-anisha")

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(user_id=user_id, instructions=instructions),
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

    if is_sip:
        # Trigger the compliant 2-sentence opening greeting automatically for the outbound call
        await session.say(
            f"Hello, this is Sita calling from Jana Sahaya. "
            f"We found you eligible for the {selected_scheme} scheme, and the deadline is on August 15th, so hurry up! "
            f"If you want to know more, say yes, and if you want to stop these calls, say no.",
            allow_interruptions=True,
        )


if __name__ == "__main__":
    cli.run_app(server)

