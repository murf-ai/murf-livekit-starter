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
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, location TEXT, household_size INTEGER, mobility_needs TEXT, last_interaction TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS escalations (ref_id TEXT PRIMARY KEY, user_id TEXT, caller_name TEXT, issue_summary TEXT, checked_info TEXT, urgency TEXT, language_preferred TEXT, contact_method TEXT, created_at TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS call_logs (call_id TEXT PRIMARY KEY, channel TEXT, status TEXT, started_at TEXT, ended_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

# -------------------------------------------------------------
# 1. THE MAIN AGENT (RAKSHA)
# -------------------------------------------------------------
class RakshaMainAgent(Agent):
    def __init__(self, instructions: str, call_id: str, is_outbound: bool, handoff_trigger, return_context: str = "") -> None:
        # If returning from Vikram, inject the context and skip the initial greeting
        if return_context:
            instructions += f"\n\n[RETURN CONTEXT]: You are returning to this call from Vikram. The user needs you again because: {return_context}. Do NOT give your standard 'Namaste' greeting again. Just acknowledge you are back and help them."
        
        super().__init__(instructions=instructions)
        self.call_id = call_id
        self.is_outbound = is_outbound
        self.handoff_trigger = handoff_trigger

    def mark_call_success(self):
        """Helper function for Day 8 Analytics."""
        if self.is_outbound:
            conn = sqlite3.connect("raksha_triage.db")
            c = conn.cursor()
            c.execute('UPDATE call_logs SET status = "SUCCESS" WHERE call_id = ?', (self.call_id,))
            conn.commit()
            conn.close()

    @function_tool
    async def save_caller_info(self, context: RunContext, user_id: str, name: str, location: str, household_size: int, mobility_needs: str):
        """Save caller triage info. EXPLICITLY ASK FOR CONSENT BEFORE CALLING THIS."""
        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        c.execute('''INSERT INTO users (user_id, name, location, household_size, mobility_needs, last_interaction)
                     VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET name=excluded.name, location=excluded.location, household_size=excluded.household_size, mobility_needs=excluded.mobility_needs, last_interaction=excluded.last_interaction''', 
                  (user_id, name, location, household_size, mobility_needs, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        self.mark_call_success()
        return "User data successfully saved."

    @function_tool
    async def create_escalation(self, context: RunContext, user_id: str, caller_name: str, issue_summary: str, checked_info: str, urgency: str, language_preferred: str, contact_method: str):
        """Escalate to a human NDRF dispatch or emergency officer."""
        ref_id = "ESC-" + "".join(random.choices(string.digits, k=5))
        conn = sqlite3.connect("raksha_triage.db")
        c = conn.cursor()
        c.execute('''INSERT INTO escalations (ref_id, user_id, caller_name, issue_summary, checked_info, urgency, language_preferred, contact_method, created_at, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                  (ref_id, user_id, caller_name, issue_summary, checked_info, urgency, language_preferred, contact_method, datetime.now().isoformat(), "OPEN"))
        conn.commit()
        conn.close()
        self.mark_call_success()
        return f"Escalation ticket created: {ref_id}."

    @function_tool
    async def transfer_to_shelter_specialist(self, context: RunContext, caller_summary: str):
        """Hands off the conversation to Vikram, the Shelter Specialist. Use when caller needs food or camps."""
        self.mark_call_success()
        # Trigger the engine swap
        asyncio.create_task(self.handoff_trigger(caller_summary))
        return "Please wait a moment while I transfer you to Vikram."


# -------------------------------------------------------------
# 2. THE SPECIALIST AGENT (VIKRAM)
# -------------------------------------------------------------
class VikramSpecialistAgent(Agent):
    def __init__(self, summary: str, handoff_back_trigger):
        super().__init__(instructions=f"""
        You are VIKRAM, a male Shelter Information Specialist in India.
        Communicate calmly and speak in natural "Hinglish".

        YOUR STRICT ROLE & RULES:
        1. In your VERY FIRST response ONLY, introduce yourself: "Namaste, this is Vikram, the Shelter Specialist." Do NOT introduce yourself again in later responses.
        2. Your ONLY job is to provide information on relief camps, food distribution centers, and safe evacuation routes.
        3. Do NOT perform emergency triage or save caller details.
        4. If the caller says they are injured, trapped, or changes the topic back to medical/rescue, you MUST immediately use the `transfer_back_to_raksha` tool. Say: "I will transfer you back to Raksha for emergency rescue."
        
        Caller Context from Raksha: {summary}
        """)
        self.handoff_back_trigger = handoff_back_trigger

    @function_tool
    async def transfer_back_to_raksha(self, context: RunContext, reason_summary: str):
        """Hands the conversation back to Raksha (the Triage Specialist). Use when caller needs rescue, medical help, or is done with shelter info."""
        # Trigger the engine swap backwards
        asyncio.create_task(self.handoff_back_trigger(reason_summary))
        return "Please wait, I am transferring you back to Raksha."


server = AgentServer()
def prewarm(proc: JobProcess): proc.userdata["vad"] = silero.VAD.load()
server.setup_fnc = prewarm

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    call_id = ctx.room.name
    is_outbound = call_id.startswith("emergency-room")
    channel = "SIP" if is_outbound else "WEB"
    
    if is_outbound:
        conn = sqlite3.connect("raksha_triage.db")
        conn.execute('INSERT INTO call_logs (call_id, channel, status, started_at) VALUES (?, ?, ?, ?) ON CONFLICT(call_id) DO NOTHING', 
                     (call_id, channel, "IN_PROGRESS", datetime.now().isoformat()))
        conn.commit()
        conn.close()

    @ctx.room.on("disconnected")
    def on_disconnected(*args, **kwargs):
        if is_outbound:
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

    ctx.log_context_fields = {"room": call_id}
    
    raksha_prompt = """
    You are Raksha, an automated disaster response triage assistant in India.
    DAY 9 HANDOFF RULES:
    1. If the caller is SAFE but asks about relief camps or food, you MUST use the `transfer_to_shelter_specialist` tool.
    2. You MUST say: "I will connect you to our shelter specialist, Vikram."
    """
    if is_outbound:
        raksha_prompt += "\nOUTBOUND CALL RULE: Greet with: 'Namaste, this is Raksha. To stop receiving alerts, say Opt out. Are you safe?'"
    else:
        raksha_prompt += "\nWEB BROWSER RULE: Greet warmly and ask how you can help."

    # STATE MANAGER: Tracks the currently running session so we can close it properly
    active_session = None

    # -------------------------------------------------------------
    # TRUE HANDOFF ENGINE: RAKSHA -> VIKRAM
    # -------------------------------------------------------------
    async def switch_to_vikram(summary: str):
        nonlocal active_session
        logger.info("Executing True Handoff: Raksha -> Vikram")
        await asyncio.sleep(4) # Give Raksha time to finish speaking
        
        if active_session:
            await active_session.aclose()

        vikram = VikramSpecialistAgent(summary, handoff_back_trigger=switch_to_raksha)
        vikram_session = AgentSession(
            stt=deepgram.STT(model="nova-3", language="multi"),
            llm=google.LLM(model="gemini-3.5-flash-lite"),
            tts=murf.TTS(
                voice="Samar",          # Vikram's Male Voice
                locale="en-IN",
                style="Conversational",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True,
            ),
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=True,
        )
        
        active_session = vikram_session
        await vikram_session.start(agent=vikram, room=ctx.room)
        logger.info("Vikram is now active.")

    # -------------------------------------------------------------
    # TRUE HANDOFF ENGINE: VIKRAM -> RAKSHA (Advanced Day 9 feature)
    # -------------------------------------------------------------
    async def switch_to_raksha(return_context: str):
        nonlocal active_session
        logger.info("Executing True Handoff Return: Vikram -> Raksha")
        await asyncio.sleep(4) # Give Vikram time to finish speaking
        
        if active_session:
            await active_session.aclose()

        raksha = RakshaMainAgent(instructions=raksha_prompt, call_id=call_id, is_outbound=is_outbound, handoff_trigger=switch_to_vikram, return_context=return_context)
        raksha_session = AgentSession(
            stt=deepgram.STT(model="nova-3", language="multi"),
            llm=google.LLM(model="gemini-3.5-flash-lite"),
            tts=murf.TTS(
                voice="Pooja",          # Back to Raksha's Female Voice!
                locale="en-IN",
                style="Conversational",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True,
            ),
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=True,
        )
        
        active_session = raksha_session
        await raksha_session.start(agent=raksha, room=ctx.room)
        logger.info("Raksha is now back active.")

    # -------------------------------------------------------------
    # BOOT UP RAKSHA INITIALLY
    # -------------------------------------------------------------
    initial_raksha = RakshaMainAgent(instructions=raksha_prompt, call_id=call_id, is_outbound=is_outbound, handoff_trigger=switch_to_vikram)
    
    initial_session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            voice="Pooja",              # Raksha starts with female voice
            locale="en-IN",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    active_session = initial_session
    await active_session.start(agent=initial_raksha, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)