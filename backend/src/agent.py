import asyncio
import logging
import sqlite3
import aiohttp
import os
import random
import string
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

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

env_path = Path(__file__).resolve().parent.parent / ".env.local"
load_dotenv(dotenv_path=env_path)

def init_db():
    conn = sqlite3.connect("raksha_triage.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, name TEXT, location TEXT, household_size INTEGER, mobility_needs TEXT, last_interaction TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS escalations (
            ref_id TEXT PRIMARY KEY, user_id TEXT, caller_name TEXT, issue_summary TEXT, checked_info TEXT, urgency TEXT, language_preferred TEXT, contact_method TEXT, created_at TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS call_logs (
            call_id TEXT PRIMARY KEY, channel TEXT, status TEXT, started_at TEXT, ended_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

SYSTEM_PROMPT = """
You are Raksha, an automated disaster response triage assistant in India.
Communicate calmly, urgently, and speak in natural "Hinglish".

DAY 7 HUMAN ESCALATION & CONSENT RULES (STRICT):
1. WHEN TO ESCALATE TO HUMAN HELP:
   - If the caller is TRAPPED, INJURED, in immediate physical danger, or needs direct physical rescue (NDRF).
   - If there is structural damage or medical urgency that an automated system cannot resolve.
2. STRICT PERMISSION & CONSENT RULE:
   - Before calling `create_escalation`, you MUST explicitly ask the caller for permission to share their details with human responders.
   - IF THEY SAY NO: Do NOT call `create_escalation`. 
   - IF THEY SAY YES: Call `create_escalation` immediately.
3. AFTER ESCALATION IS CREATED: Provide the user with the generated Reference ID (e.g., ESC-12345) and give an honest next step.

Always write Hindi words in Devanagari script.
"""

class Assistant(Agent):
    def __init__(self, instructions: str, call_id: str) -> None:
        super().__init__(instructions=instructions)
        self.call_id = call_id

    def mark_call_success(self):
        """Helper function to mark the current call as SUCCESS in call_logs."""
        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        c.execute('UPDATE call_logs SET status = "SUCCESS" WHERE call_id = ?', (self.call_id,))
        conn.commit()
        conn.close()

    @function_tool
    async def lookup_caller(self, context: RunContext, user_id: str):
        """Look up a returning caller by their phone number or user_id."""
        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        c.execute("SELECT name, location, household_size, mobility_needs FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return f"Found caller: Name={result[0]}, Location={result[1]}, Household Size={result[2]}, Mobility Needs={result[3]}."
        return "Caller not found. Ask for their details."

    @function_tool
    async def check_realtime_hazards(self, context: RunContext, district: str):
        """Fetch real-time weather and flood hazard warnings for a district.
        SUCCESS CONDITION: Delivers verified disaster information to the caller.
        """
        try:
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={district}&count=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(geocode_url) as resp:
                    geo_data = await resp.json()

            if not geo_data.get("results"):
                return f"Could not locate district '{district}' in database."

            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]

            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation,wind_speed_10m"
            async with aiohttp.ClientSession() as session:
                async with session.get(weather_url) as resp:
                    weather_data = await resp.json()

            current = weather_data["current"]
            rain_mm = current["precipitation"]
            wind_kmh = current["wind_speed_10m"]
            current_time = datetime.now().strftime("%I:%M %p")

            if rain_mm > 15.0 or wind_kmh > 60.0:
                alert = "RED ALERT: Severe flood hazard in progress."
            elif rain_mm > 5.0 or wind_kmh > 40.0:
                alert = "ORANGE ALERT: Moderate rainfall/wind detected."
            else:
                alert = "NO ALERT: Weather conditions currently clear."

            # Mark Call as SUCCESS (Verified Information Provided)
            self.mark_call_success()

            return f"Verified data for {district}: {alert} Rain: {rain_mm} mm, Wind: {wind_kmh} km/h (as of {current_time})."

        except Exception as e:
            logger.error(f"API Error fetching live data: {e}")
            return "Unable to fetch live weather hazard data at this moment."

    @function_tool
    async def save_caller_info(self, context: RunContext, user_id: str, name: str, location: str, household_size: int, mobility_needs: str):
        """Save caller triage info. EXPLICITLY ASK FOR CONSENT BEFORE CALLING THIS.
        SUCCESS CONDITION: Triage details saved to database.
        """
        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        last_interaction = datetime.now().isoformat()
        c.execute('''
            INSERT INTO users (user_id, name, location, household_size, mobility_needs, last_interaction)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name, location=excluded.location, household_size=excluded.household_size,
                mobility_needs=excluded.mobility_needs, last_interaction=excluded.last_interaction
        ''', (user_id, name, location, household_size, mobility_needs, last_interaction))
        conn.commit()
        conn.close()

        # Mark Call as SUCCESS (Triage Data Gathered)
        self.mark_call_success()

        return "User data successfully saved to the emergency database."

    @function_tool
    async def create_escalation(self, context: RunContext, user_id: str, caller_name: str, issue_summary: str, checked_info: str, urgency: str, language_preferred: str, contact_method: str):
        """Escalate to a human NDRF dispatch or emergency officer.
        SUCCESS CONDITION: Human-help request is created.
        """
        ref_id = "ESC-" + "".join(random.choices(string.digits, k=5))
        created_at = datetime.now().isoformat()

        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        c.execute('''
            INSERT INTO escalations (ref_id, user_id, caller_name, issue_summary, checked_info, urgency, language_preferred, contact_method, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ref_id, user_id, caller_name, issue_summary, checked_info, urgency, language_preferred, contact_method, created_at, "OPEN"))
        conn.commit()
        conn.close()

        # Mark Call as SUCCESS (Human-Help Request Created)
        self.mark_call_success()

        # Webhook Alert to Discord (if configured)
        discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if discord_webhook_url:
            color = 15158332 if urgency in ["HIGH", "EMERGENCY"] else 15105570
            payload = {
                "embeds": [{
                    "title": f"🚨 EMERGENCY HUMAN DISPATCH TICKET [{urgency}]: {ref_id}",
                    "color": color,
                    "fields": [
                        {"name": "👤 Caller Name", "value": caller_name, "inline": True},
                        {"name": "⚡ Urgency", "value": urgency, "inline": True},
                        {"name": "📋 Issue Summary", "value": issue_summary, "inline": False},
                        {"name": "🔍 Checked Context", "value": checked_info, "inline": False}
                    ]
                }]
            }
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(discord_webhook_url, json=payload)
            except Exception as e:
                logger.error(f"Webhook error: {e}")

        return f"Human dispatch escalation ticket successfully created! Reference ID: {ref_id}. Inform the caller immediately."

server = AgentServer()
def prewarm(proc: JobProcess): proc.userdata["vad"] = silero.VAD.load()
server.setup_fnc = prewarm

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    call_id = ctx.room.name
    is_outbound = call_id.startswith("emergency-room")
    channel = "SIP" if is_outbound else "WEB"
    
    # Day 8 Step 2: Record call start in DB
    conn = sqlite3.connect("raksha_triage.db")
    conn.execute('INSERT INTO call_logs (call_id, channel, status, started_at) VALUES (?, ?, ?, ?) ON CONFLICT(call_id) DO NOTHING', 
                 (call_id, channel, "IN_PROGRESS", datetime.now().isoformat()))
    conn.commit()
    conn.close()

    # Day 8 Step 2: On disconnect, if no success tool was triggered, mark call as FAILED
    @ctx.room.on("disconnected")
    def on_disconnected(*args, **kwargs):
        db = sqlite3.connect("raksha_triage.db")
        c = db.cursor()
        c.execute('SELECT status FROM call_logs WHERE call_id = ?', (call_id,))
        result = c.fetchone()
        
        if result and result[0] == "IN_PROGRESS":
            c.execute('UPDATE call_logs SET status = "FAILED", ended_at = ? WHERE call_id = ?', (datetime.now().isoformat(), call_id))
        else:
            c.execute('UPDATE call_logs SET ended_at = ? WHERE call_id = ?', (datetime.now().isoformat(), call_id))
        db.commit()
        db.close()
        logger.info(f"Analytics updated: Call {call_id} ended.")

    ctx.log_context_fields = {"room": call_id}
    
    dynamic_prompt = SYSTEM_PROMPT
    if is_outbound:
        dynamic_prompt += "\nOUTBOUND CALL RULE: Greet with: 'Namaste, this is Raksha. To stop receiving alerts, say Opt out. Are you safe?'"
    else:
        dynamic_prompt += "\nWEB BROWSER RULE: Greet warmly and ask how you can help. Do not mention opting out."

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            voice="Pooja",
            locale="en-IN",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(instructions=dynamic_prompt, call_id=call_id),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                )
            )
        )
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)