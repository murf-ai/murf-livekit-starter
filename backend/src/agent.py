import asyncio
import logging
import sqlite3
from datetime import datetime
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

MEMORY & TOOL CHAINING RULES (CRITICAL):
1. When a user connects, call `lookup_caller` first using a default ID like 'user_123'. 
2. TOOL CHAINING: If they are a returning user and you found their location, IMMEDIATELY call `get_disaster_alerts_and_shelters` using their saved location before you even say hello.
3. Greet them by name, confirm their safety, and instantly provide the real-time shelter data you just looked up. 
4. ALWAYS state out loud when the shelter data was updated (e.g., "This data is current as of...").

GRACEFUL FAILURES:
If a tool returns a network error, DO NOT invent an answer. Honestly state that the system is currently down and provide general safety advice (like moving to high ground).

CONSENT & FORGET:
- You MUST ask for permission before calling `save_caller_info`. 
- If they ask to be forgotten, call `delete_caller_info`.

LANGUAGE & SCRIPT RULES:
Always write every language in its own native script.
- For Hindi words → Use Devanagari (नमस्ते), NEVER romanize Hindi words.
- For English words → Use the standard English alphabet.
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

    # INDENTED PROPERLY INSIDE Assistant CLASS NOW:
    @function_tool
    async def get_disaster_alerts_and_shelters(self, context: RunContext, district: str):
        """Fetch the real-time disaster alert level and nearest active NDRF shelter for a given district.
        Call this immediately after learning the user's location, either from 'lookup_caller' or by asking them.
        """
        try:
            # HIDDEN TRIGGER FOR YOUR VIDEO DEMO:
            # We remove spaces so "network down" or "networkdown" both trigger it!
            safe_district = district.lower().replace(" ", "")
            if "networkdown" in safe_district or "offline" in safe_district:
                raise Exception("CRITICAL: National Disaster API Timeout")
            await asyncio.sleep(1)

            MOCK_DISASTER_DATA = {
                "mumbai": {"status": "Red Alert - Severe Flooding", "shelter": "Bandra Kurla Complex Relief Camp", "capacity": "250 beds available"},
                "chennai": {"status": "Orange Alert - Cyclone Warning", "shelter": "Chennai Trade Centre", "capacity": "120 beds available"},
                "delhi": {"status": "Yellow Alert - Heatwave", "shelter": "Pragati Maidan Hall 3", "capacity": "500+ beds available"}
            }

            district_key = district.lower().strip()
            current_time = datetime.now().strftime("%I:%M %p")

            if district_key in MOCK_DISASTER_DATA:
                data = MOCK_DISASTER_DATA[district_key]
                return f"Alert Status: {data['status']}. Nearest Shelter: {data['shelter']} ({data['capacity']}). Data pulled live as of {current_time} today."
            else:
                return f"No severe alerts currently active for {district}. Data current as of {current_time} today. Advise user to stay alert."
                
        except Exception as e:
            logger.error(f"API Error fetching disaster data: {e}")
            return "CRITICAL ERROR: The live disaster database is currently unreachable due to network failure. DO NOT INVENT A SHELTER. Tell the user the system is down, advise them to move to high ground immediately, and tune into local emergency radio."

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
            voice="Anusha",
            locale="en-IN",
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