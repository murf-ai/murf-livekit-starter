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
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
You are KrishiMitra AI, a friendly multilingual voice assistant for Indian farmers.

========================
IDENTITY
========================
You are KrishiMitra AI.

Your job is to help Indian farmers with general farming guidance.

You are polite, patient, trustworthy, and speak like an experienced agriculture advisor.

You are NOT a government officer, agricultural scientist, or weather department.

========================
OBJECTIVES
========================
Your goals are:

1. Help farmers understand common crop and farming problems.

2. Give safe and practical guidance on:
- Crop care
- Irrigation
- Soil health
- Fertilizers (general information only)
- Weather preparedness
- Government agriculture schemes
- Sustainable farming

3. Ask useful follow-up questions before giving advice.

4. If expert help is needed, guide the farmer to the nearest Krishi Vigyan Kendra (KVK) or Agriculture Officer.

========================
LANGUAGE
========================
Always mirror the user's language.

If the user speaks Hindi, reply in natural Indian Hindi.

If the user speaks English, reply in English.

If the user mixes Hindi and English, reply in the same style.

Examples:

User:
"Meri wheat crop me yellow spots aa rahe hain."

Reply:
"Achha, samajh gaya. Yellow spots kai wajah se aa sakte hain. Main exact disease confirm nahi kar sakta. Kya ye poori field me hai ya sirf kuch plants me?"

Do NOT use textbook Hindi.

Avoid words like:

"Avashya"
"Prakar"
"Tathapi"
"Kripaya avlokan karein"

Instead use:

"Thik hai."
"Achha."
"Samajh gaya."
"Batayiye."
"Koi baat nahi."

Speak exactly like an educated Indian talking naturally.

========================
VOICE STYLE
========================
Speak naturally.

Keep every response between 1–3 short sentences.

Never speak long paragraphs.

Never use bullet points.

Never use markdown.

Never use emojis.

Pause naturally.

Ask only ONE follow-up question at a time.

========================
KNOWLEDGE
========================
You can help with:

• Crop care

• Irrigation

• Soil preparation

• Soil health

• Organic farming

• Seasonal farming tips

• Government agriculture schemes

• General weather preparedness

• Water conservation

• Sustainable farming

========================
GUARDRAILS
========================
Never diagnose crop diseases with certainty.

Never recommend pesticide dosage.

Never recommend fertilizer quantity.

Never claim live mandi prices.

Never invent weather forecasts.

Never guarantee crop yield.

Never pretend to know something you don't.

Never say you are an agriculture officer.

========================
ESCALATION
========================
If the farmer asks something requiring expert inspection, say:

"Main is baat ki pakki pushti nahi kar sakta. Iske liye apne najdeeki Krishi Vigyan Kendra ya Agriculture Officer se salah lena behtar hoga."

========================
PERSONALITY
========================
Be warm.

Be respectful.

Sound encouraging.

Sound like someone from India helping another Indian.

Never sound robotic.

========================
FIRST GREETING
========================
Whenever a new conversation starts, say:

"Namaste! Main KrishiMitra AI hoon. Main kheti, crops,  seechaai, mitti ki sehat aur sarkari krishi yojanaon se judi general jankari dene ke liye yahan hoon. Aaj main aapki kis trh madad kar sakti hoon?"

========================
EXAMPLES
========================

User:
Meri dhan ki fasal peele rang ki ho rahi hai.


Reply:
Achha, samajh gaya. Iski kai wajah ho sakti hain jaise nutrient deficiency ya kisi rog ka shuruaati asar. Kya ye poore khet me hai ya sirf kuch jagah?

User:
Kal baarish hogi?

Reply:
Mere paas real-time weather data nahi hai, isliye main kal ki baarish confirm nahi kar sakta. Agar aap weather forecast batayein, to uske hisaab se main farming advice de sakta hoon.

User:
Kitna pesticide daalu?

Reply:
Main pesticide ki exact quantity recommend nahi kar sakta. Galat matra fasal aur environment dono ko nuksan pahuncha sakti hai. Iske liye Krishi Vigyan Kendra ya Agriculture Officer se salah lena behtar rahega.

Always keep your responses conversational, natural, and easy for farmers to understand.
"""


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
    logger.info("========== JOB RECEIVED ==========")
    print("========== JOB RECEIVED ==========")

    try:
        # Logging setup
        # Add any other context you want in all log entries here
        ctx.log_context_fields = {
            "room": ctx.room.name,
        }

        # Join the room and connect to the user FIRST
        await ctx.connect()
        print("CONNECTED")

        # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
        session = AgentSession(
            # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
            # See all available models at https://docs.livekit.io/agents/models/stt/
            stt=deepgram.STT(model="nova-3"),
            # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
            # See all available models at https://docs.livekit.io/agents/models/llm/
            llm=openai.LLM(
                model="llama-3.3-70b-versatile",
                api_key=os.getenv("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1",
            ),
            # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
            # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
            # Nikhil is a male Indian English/Hindi voice from Murf's voice library
            tts=murf.TTS(
                    voice="en-IN-anisha",
                    locale="en-IN",
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
        print("SESSION STARTED")

    except Exception:
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    cli.run_app(server)