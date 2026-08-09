import logging

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

    # Join the room and wait for the remote participant to get exact user_id
    await ctx.connect()
    participant = await ctx.wait_for_participant()
    user_id = participant.identity if participant else "unknown_user"

    logger.info(f"Active connection with user_id: {user_id}")

    instructions = (
        f"{SYSTEM_PROMPT}\n\n"
        f"CURRENT USER CALL INFO:\n"
        f"- Current Caller User ID: {user_id}\n"
        f"- IMPORTANT: You MUST immediately call `lookup_caller` at the very start of the conversation. "
        f"If a record is returned, welcome the user back by name and reference their previous interaction "
        f"(e.g. 'Namaste Ramesh, last time we spoke about Atal Pension Yojana. Did you check your eligibility?'). "
        f"If no record is found, greet them as a new user."
    )

    # Set up a voice AI pipeline using Murf Falcon, Gemini 2.0 Flash, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash",
        ),
        tts=murf.TTS(
            voice="kn-IN-anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        # Check for Kannada script characters (native Kannada)
        has_kannada = any(ord(c) >= 0x0C80 and ord(c) <= 0x0CFF for c in transcript)

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


if __name__ == "__main__":
    cli.run_app(server)
