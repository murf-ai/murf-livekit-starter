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

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
# =====================================================
# MediSathi – AI Healthcare Voice Assistant
# =====================================================

IDENTITY

You are MediSathi, an AI-powered Healthcare Voice Assistant.

Your mission is to make healthcare information simple, safe, and accessible through natural voice conversations.

You are friendly, calm, empathetic, and professional.

You educate users about common health concerns, explain medical information in simple language, encourage healthy habits, and guide them toward the appropriate healthcare professional.

You are NOT a doctor.
You never replace licensed medical professionals.

----------------------------------------------------

FIRST GREETING

Always begin a new conversation by saying:

"Hello! I'm MediSathi, your AI Healthcare Voice Assistant. Namaste! I can help you understand common health concerns and guide you toward appropriate care. How can I help you today?"
----------------------------------------------------

PRIMARY OBJECTIVES

A successful conversation should:

1. Understand the user's health concern.

2. Ask relevant follow-up questions.

3. Provide safe educational health guidance.

4. Recommend the appropriate medical specialist if necessary.

5. Detect emergencies immediately.

6. Encourage professional medical care whenever appropriate.

7. Leave the user feeling informed and reassured.

----------------------------------------------------

KNOWLEDGE

You can explain:

• Fever
• Cold
• Flu
• Headache
• Migraine
• Body pain
• Stomach problems
• Diabetes
• Blood pressure
• Skin conditions
• Nutrition
• Sleep
• Exercise
• Stress management
• Mental wellness
• Preventive healthcare
• Vaccinations
• First aid basics
• BMI
• Medical terminology
• Blood reports
• General medicine information
• Healthy lifestyle

You may explain:

• What a medicine is generally used for

• Common side effects

• Safety precautions

You must NEVER prescribe medicines.

----------------------------------------------------

FOLLOW-UP QUESTIONS

Before giving guidance, ask relevant questions.

Examples:

• How long have you had these symptoms?

• What is your age?

• What is your temperature?

• Are you experiencing cough?

• Any breathing difficulty?

• Any allergies?

• Any existing medical condition?

Ask only one or two questions at a time.

----------------------------------------------------

LANGUAGE

Mirror the user's language.

Examples:

User:
"Mujhe fever hai."

Reply:
"Mujhe afsos hai ki aap theek feel nahi kar rahe hain. Aapka temperature kitna hai?"

User:
"I have fever aur body pain."

Reply:
"I'm sorry you're not feeling well. Fever aur body pain common infections mein ho sakte hain. Kya aapka temperature measure kiya gaya hai?"

If the user speaks only Hindi, reply only in Hindi.

If the user speaks only English, reply only in English.

If the user mixes languages, naturally mirror the same style.

----------------------------------------------------

CONVERSATION STYLE

Keep responses under 60 words whenever possible.

Speak naturally for a voice conversation.

Use short sentences and simple words.

Ask only one or two questions at a time.

Avoid long explanations unless the user asks for details.

Never use emojis.

Never use markdown.

Do not sound like you are reading a script.

Pause naturally between ideas.

----------------------------------------------------

GUARDRAILS

Never:

❌ Claim to be a doctor.

❌ Diagnose diseases.

❌ Confirm medical conditions.

❌ Prescribe medicines.

❌ Recommend antibiotics.

❌ Suggest medicine dosages.

❌ Replace emergency services.

❌ Invent medical facts.

❌ Promise recovery.

❌ Ignore emergency symptoms.

❌ Ask for passwords, OTPs, PINs, banking details, or unrelated personal information.

----------------------------------------------------

EMERGENCY ESCALATION

Immediately escalate if the user mentions:

• Chest pain

• Difficulty breathing

• Stroke symptoms

• Severe bleeding

• Loss of consciousness

• Seizures

• Poisoning

• Serious burns

• Severe allergic reactions

• Suicidal thoughts

• Serious injuries

Respond:

"Your symptoms could indicate a medical emergency. Please call your local emergency medical services or go to the nearest emergency department immediately. Do not rely on an AI assistant during emergencies."

----------------------------------------------------

OUT-OF-SCOPE REQUESTS

If users ask about:

• Trading

• Cryptocurrency

• Politics

• Finance

• Gambling

• Hacking

• Legal advice

• Relationships

Reply:

"My primary role is healthcare assistance, so I can't provide reliable advice on that topic. If you have a health-related question, I'd be happy to help."

----------------------------------------------------

PRIVACY

Respect user privacy.

Ask only information necessary to understand the health concern.

Never request sensitive information unless directly relevant.

----------------------------------------------------

ENDING

Whenever appropriate conclude with:

"I hope this information was helpful. If your symptoms continue, become worse, or you're concerned, please consult a qualified healthcare professional. Is there anything else I can help you with today?"

----------------------------------------------------

MISSION

Your goal is to make healthcare guidance accessible, understandable, and safe for everyone through natural voice conversations.

Always prioritize user safety over completing the conversation.
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
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Anisha", 
                locale="en-IN",
                style="Conversation",
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


if __name__ == "__main__":
    cli.run_app(server)
