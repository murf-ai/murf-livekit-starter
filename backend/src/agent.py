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
    function_tool,
    RunContext
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import sqlite3
from datetime import datetime

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# 1. Initialize SQLite Database
def init_db():
    conn = sqlite3.connect("raksha_triage.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            location TEXT,
            household_size INTEGER,
            mobility_needs TEXT,
            last_interaction TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

SYSTEM_PROMPT = """
You are Raksha, a real-time disaster response triage assistant in India. 
Communicate calmly and urgently. 

You MUST speak in "Hinglish" — a natural, conversational mix of English and Hindi. 
Do not use pure, highly formal Hindi. Use common English words for context.

MEMORY & CONSENT RULES:
1. When a user connects, always call `lookup_caller` first using a default ID like 'user_123'. 
2. If they are returning, greet them by name and confirm their safety status.
3. If they are new, ask for their name, location, household size, and mobility needs.
4. STRICT RULE: You MUST ask for their permission before saving their data. If they say yes, call `save_caller_info`. If no, do not save.
5. FORGET ME RULE: If a user asks you to delete, forget, or erase their data, you MUST call `delete_caller_info` to wipe their record.

LANGUAGE & SCRIPT RULES:
Always write every language in its own native script.
- For Hindi words → Use Devanagari (नमस्ते), NEVER romanize Hindi words (never "namaste").
- For English words → Use the standard English alphabet (e.g., "Emergency", "Location").

Example of the perfect Hinglish response:
"नमस्ते! Emergency situation में आपकी location क्या है? क्या आप safe हैं?"
"""

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_caller(self, context: RunContext, user_id: str):
        """Look up a returning caller by their phone number or user_id."""
        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        c.execute("SELECT name, location, household_size, mobility_needs FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return f"Found caller: Name={result[0]}, Location={result[1]}, Household Size={result[2]}, Mobility Needs={result[3]}. Welcome them back!"
        return "Caller not found. This is a new user. You must ask for their details."

    @function_tool
    async def save_caller_info(
        self, 
        context: RunContext,
        user_id: str,
        name: str,
        location: str,
        household_size: int,
        mobility_needs: str
    ):
        """Save caller triage info. YOU MUST EXPLICITLY ASK FOR CONSENT BEFORE CALLING THIS."""
        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        last_interaction = datetime.now().isoformat()
        
        c.execute('''
            INSERT INTO users (user_id, name, location, household_size, mobility_needs, last_interaction)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                location=excluded.location,
                household_size=excluded.household_size,
                mobility_needs=excluded.mobility_needs,
                last_interaction=excluded.last_interaction
        ''', (user_id, name, location, household_size, mobility_needs, last_interaction))
        conn.commit()
        conn.close()
        return "User data successfully saved to the emergency database."

    @function_tool
    async def delete_caller_info(self, context: RunContext, user_id: str):
        """Delete the caller's saved information from the database when they ask to be forgotten."""
        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        rows_deleted = c.rowcount
        conn.close()
        
        if rows_deleted > 0:
            return "User data successfully deleted from the emergency database."
        return "No data found for this user."


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
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
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