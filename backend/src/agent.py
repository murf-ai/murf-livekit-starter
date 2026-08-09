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
    UserInputTranscribedEvent,
    function_tool,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

try:
    from prompt import SYSTEM_PROMPT  # type: ignore
except ImportError:
    from src.prompt import SYSTEM_PROMPT  # type: ignore

try:
    import db  # type: ignore
except ImportError:
    from src import db  # type: ignore


class Assistant(Agent):
    def __init__(self, user_id: str, instructions: str = SYSTEM_PROMPT) -> None:
        super().__init__(instructions=instructions)
        self.user_id = user_id

    @function_tool
    async def lookup_caller(self, user_id: str) -> str:
        """Looks up the current caller's details and saved facts in the database.
        Always execute this tool at the very beginning of the call to check if they are a returning caller.
        
        Args:
            user_id: The ID of the current caller (provided to you in your system prompt).
        """
        logger.info(f"Tool lookup_caller called for current user: {user_id}")
        user_info = db.get_user(user_id)
        if user_info:
            import json
            return json.dumps(user_info)
        return f"No record found for user ID: {user_id}"

    @function_tool
    async def save_caller_facts(self, name: str, language_preference: str, facts: str) -> str:
        """Saves current caller's details and facts (e.g. checked schemes, eligibility answers) to the database.
        Always verify the caller has given verbal permission/consent before calling this.
        
        Args:
            name: The caller's name.
            language_preference: The caller's preferred language (e.g., Hindi, English, Hinglish).
            facts: A JSON string of key-value pairs representing facts about the caller (e.g., eligibility, schemes checked). Do not store account or ID numbers.
        """
        logger.info(f"Tool save_caller_facts called for user_id: {self.user_id}, name: {name}")
        
        import json
        try:
            facts_dict = json.loads(facts)
        except (json.JSONDecodeError, TypeError):
            facts_dict = {}

        # Clean facts from any ID numbers or account numbers
        cleaned_facts = {}
        for k, v in facts_dict.items():
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

    # Join the room first
    await ctx.connect()
    logger.info("Connected to room, waiting for participant...")

    # Wait for the user to actually join before we start the voice pipeline
    participant = await ctx.wait_for_participant()
    user_id = participant.identity or "unknown_user"
    logger.info(f"Participant joined with user_id: {user_id}")

    # Inject the instructions with the dynamic user_id 
    instructions = f"{SYSTEM_PROMPT}\n\nCURRENT USER CALL INFO:\n- Current Caller User ID: {user_id}\n- IMPORTANT: You MUST immediately call `lookup_caller` at the very start of the conversation. If a record is returned, welcome the user back by name and reference their previous interaction (e.g. 'नमस्ते Ramesh जी, पिछली बार हमने आपके Atal Pension Yojana के बारे में बात की थी। क्या उससे जुड़ा कोई सवाल है?'). If no record is found, greet them as a new user."

    # Now that we have the identity, we initialize the Assistant properly
    agent_instance = Assistant(user_id=user_id, instructions=instructions)

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        llm=google.LLM(
                model="gemini-3.5-flash",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        tts=murf.TTS(
                voice="Anisha", 
                locale="en-IN",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=agent_instance,
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
