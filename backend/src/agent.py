import asyncio
import logging
import sqlite3
import aiohttp
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
import sys
from pathlib import Path

# Force the script to look for .env.local in the backend folder
backend_dir = Path(__file__).resolve().parent.parent
env_path = backend_dir / ".env.local"
load_dotenv(dotenv_path=env_path)
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
You are Raksha, an automated disaster response triage assistant in India.
Communicate calmly, urgently, and speak in natural "Hinglish".

OUTBOUND CALL OPENING RULE (CRITICAL):
When the user picks up the phone and says hello, you MUST start with this EXACT greeting:
"Namaste, this is Raksha, the automated emergency alert system. I am calling because a severe flood warning has been issued for your area. To stop receiving these alerts, just say 'Opt out'. Are you and your family currently safe?"

OUTBOUND RULES & CONVERSATION FLOW:
1. If they say they are safe: Advise them to stay indoors and hang up gracefully.
2. If they need help/rescue: Immediately ask for their location, household size, and mobility needs.
3. If they say "Opt out" or "Stop": Politely confirm they are unsubscribed from emergency alerts, then stop speaking and end the conversation.

MEMORY & TOOL CHAINING RULES:
1. If they provide their location or user ID, you can use `lookup_caller` or `check_realtime_hazards` if requested, but your primary goal is to assess their immediate safety.
2. If they need to be rescued, use `save_caller_info` to log their details for the NDRF. 

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

    @function_tool
    async def check_realtime_hazards(self, context: RunContext, district: str):
        """Fetch real-time internet weather and flood hazards for the user's location.
        Call this immediately after learning the user's location to check if they are in immediate danger.
        """
        import aiohttp # Ensures aiohttp is available
        try:
            # 1. The Video Demo Trigger (Graceful Failure)
            safe_district = district.lower().replace(" ", "")
            if "networkdown" in safe_district or "offline" in safe_district:
                raise Exception("CRITICAL: National Hazard API Timeout")

            # 2. GEOCODING API: Convert the district name into real Lat/Long coordinates
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={district}&count=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(geocode_url) as resp:
                    geo_data = await resp.json()

            if not geo_data.get("results"):
                return f"Could not locate the district '{district}' in the global database. Advise the user to stay alert."

            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]

            # 3. REAL-TIME WEATHER API: Fetch live precipitation and wind data
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation,wind_speed_10m"
            async with aiohttp.ClientSession() as session:
                async with session.get(weather_url) as resp:
                    weather_data = await resp.json()

            current = weather_data["current"]
            rain_mm = current["precipitation"]
            wind_kmh = current["wind_speed_10m"]
            current_time = datetime.now().strftime("%I:%M %p")

            # 4. Compute the Hazard Logic based on real data
            if rain_mm > 15.0 or wind_kmh > 60.0:
                alert = "RED ALERT: Severe hazard detected. Heavy flooding or cyclonic winds in progress."
            elif rain_mm > 5.0 or wind_kmh > 40.0:
                alert = "ORANGE ALERT: Moderate hazard. Heavy rain or strong winds detected."
            else:
                alert = "NO ALERT: Currently clear, but advise caution as conditions change rapidly."

            return f"Real-time data for {district}: {alert} Current rainfall is {rain_mm} mm and wind speed is {wind_kmh} km/h. Data pulled live from the internet as of {current_time} today."

        except Exception as e:
            logger.error(f"API Error fetching live data: {e}")
            return "CRITICAL ERROR: The live hazard database is currently unreachable due to network failure. DO NOT INVENT WEATHER DATA. Tell the user the system is down and advise them to move to high ground immediately."

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