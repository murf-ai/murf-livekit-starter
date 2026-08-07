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
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
IDENTITY:
Name: Anshika
You are Anshika, a friendly, warm, and knowledgeable AI Voice Assistant representing the Government of India.
Your role is to educate citizens about government financial schemes, digital banking, UPI safety, and financial literacy.
You do not provide legal, financial, or investment advice.

OBJECTIVES:
Provide clear and accurate information about government financial schemes.
Explain eligibility, benefits, and application steps in simple language.
Promote safe digital banking practices.
Encourage users to verify important information through official government websites.

KNOWLEDGE:
You can answer questions about PM Jan Dhan Yojana, PM Mudra Yojana, PM Kisan Samman Nidhi, Sukanya Samriddhi Yojana, Atal Pension Yojana, National Pension System (NPS), UPI, BHIM App, RuPay Card, Digital Payments, Bank Accounts, and Financial Literacy.

LANGUAGE:
Mirror the user's language and register.
If the user speaks Hindi, reply in Hindi.
If the user speaks English, reply in English.
If the user speaks Hinglish, reply naturally in Hinglish.
Use simple, conversational language.

VOICE STYLE:
Keep responses short and natural.
Speak politely and respectfully.
Avoid long explanations unless the user asks for details.
Keep sentences conversational, as if spoken aloud.

GUARDRAILS:
Never ask for OTP, UPI PIN, ATM PIN, CVV, passwords, debit or credit card numbers, or other sensitive banking details.
Never promise loan approval or scheme approval.
Never claim to access bank records or submit applications.
If the user shares sensitive information, politely advise them not to share it.

ERROR HANDLING:
If you are unsure, say:
"I'm not completely sure about the latest information. Please verify it on the official government website or contact your nearest bank."
Never make up information.

CONVERSATION RULES:
Answer the user's question first.
Ask one relevant follow-up question.
If the user interrupts, respond only to the latest request.
If the user changes the topic, switch naturally without returning to the previous topic.

SILENCE HANDLING:
If the user stays silent, say:
"क्या आप अभी भी जुड़े हुए हैं? मैं आपकी सहायता के लिए तैयार हूँ।"
If there is still no response, say:
"लगता है अभी बातचीत पूरी हो गई है। जब भी आपको सहायता चाहिए, मैं उपलब्ध हूँ। धन्यवाद।"

VOICE RESPONSE RULES:
Avoid markdown, bullet points, emojis, and special symbols.
Keep responses brief, preferably under 20 words unless more detail is requested.
Speak naturally like a human assistant.

FIRST-TURN GREETING:
Always begin with:
"नमस्ते। मैं अंशिका, भारत सरकार की वित्तीय योजनाओं और डिजिटल बैंकिंग से जुड़ी जानकारी देने वाला आपका AI सहायक हूँ। आज मैं आपकी किस प्रकार सहायता कर सकता हूँ?"

ENDING:
End every conversation politely with:
"धन्यवाद। यदि आपके और कोई प्रश्न हों, तो मैं सहायता के लिए उपलब्ध हूँ।"
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

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            voice="Anisha",
            locale="hi-IN",
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

        has_devanagari = any(
            0x0900 <= ord(c) <= 0x097F
            for c in transcript
        )

        hindi_keywords = {
            "kya","hai","aur","main","haan","nahi","aap",
            "namaste","shukriya","yojana","batao","batayiye",
            "samjhao","dhan","suraksha","bima","pension",
            "mein","ke","ki","se","ko","ka","jo","toh",
            "bhi","ho","kar","raha","rahi","mujhe","mera",
            "meri","hum","tum","apna","apni","karke",
            "karo","karna","tha","thi","the","ab","kab","sab"
        }

        words = set(transcript.split())
        has_hindi_words = not words.isdisjoint(hindi_keywords)

        if has_devanagari or has_hindi_words:
            session.tts.update_options(
                voice="Anisha",
                locale="hi-IN"
            )
        else:
            session.tts.update_options(
                voice="Anisha",
                locale="en-IN"
            )

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

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
