"""Day 6 outbound agent — scheme deadline reminder for a previously eligible caller.

Places a SIP call (Twilio trunk or Linphone), opens with who/why/how-to-stop,
then reminds about the approaching scheme deadline.

Run worker:
    uv run python src/telephony/outbound/agent.py dev

Dial:
    uv run python src/telephony/outbound/dial.py --to <number|linphone-user> \\
      --name Ramesh --scheme pmsby --lang hi

Trunk setup: src/telephony/README.md or Linphone guide in challenge supplementary docs.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
)
from livekit.plugins import deepgram, murf, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db
import schemes

logger = logging.getLogger("outbound-agent")

# Load backend/.env.local, then src/test/.env.local overrides for Day 6 telephony.
_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_SRC_ROOT = Path(__file__).resolve().parents[2]
# override=True so a stale shell OPENAI_API_KEY cannot mask the nvapi key
load_dotenv(_BACKEND_ROOT / ".env.local", override=True)
load_dotenv(_SRC_ROOT / "test" / ".env.local", override=True)
load_dotenv(".env.local", override=True)

# Day 6 telephony (Linphone free path or Twilio)
SIP_OUTBOUND_HOST = os.getenv("SIP_OUTBOUND_HOST", "sip.linphone.org")
OUTBOUND_TRUNK_ID = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID") or os.getenv(
    "LIVEKIT_SIP_TRUNK_ID"
)
LINPHONE_SIP_URI = os.getenv("LINPHONE_SIP_URI", "sip:pratay@sip.linphone.org")
TRANSFER_TO_NUMBER = os.getenv("TRANSFER_TO_NUMBER")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-nano-30b-a3b")

VOICE_HI = "hi-IN-anisha"
VOICE_EN = "en-IN-anisha"
LOCALE_HI = "hi-IN"
LOCALE_EN = "en-IN"
CALLEE_IDENTITY = "phone-user"

OUTBOUND_SYSTEM = """
IDENTITY: You are Jan Sahay (जन सहाय), a financial-inclusion education assistant.
You are on an OUTBOUND phone call about a government scheme deadline.

OPENING (already spoken by the system once — do not re-introduce fully):
- Who you are, why you called, and that they can say "stop calling" / "कॉल बंद" to end.

MISSION (Day 6):
- The callee was previously found LIKELY eligible for a scheme (guidance only).
- Remind them the renewal / enrolment window is approaching.
- Explain one clear next step (keep balance for auto-debit, visit bank/CSC).
- Never promise approval. Never ask for OTP, PIN, Aadhaar, account number, or password.
- If they want documents, call get_document_checklist. For deadline facts call get_deadline_reminder.
- Keep replies under ~35 spoken words. No markdown, bullets, or emojis.
- Match the call language (Hindi or English) from the session context.
- If voicemail/answering machine: use detected_answering_machine.
- When done: say goodbye then end_call.
- If they ask for a human: transfer_to_human if available.
"""


def _parse_metadata(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"phone_number": raw.strip()}
    except json.JSONDecodeError:
        return {"phone_number": raw.strip()} if raw.strip() else {}


def build_greeting(meta: dict) -> str:
    """First two sentences: who, why, how to stop (Day 6 Step 4)."""
    name = (meta.get("caller_name") or "").strip()
    scheme = (meta.get("scheme") or "pmsby").lower()
    lang = (meta.get("language") or "hi").lower()
    code = schemes.resolve_scheme_code(scheme) or "pmsby"
    short = schemes.SCHEMES[code]["short_name"]
    hi_name = schemes.SCHEMES[code].get("hindi_name", short)

    if lang.startswith("en"):
        who = (
            "Hello"
            + (f" {name}" if name else "")
            + (". This is Jan Sahay, an automated financial schemes assistant.")
        )
        why = (
            f"I'm calling because you were earlier found likely eligible for "
            f"{short}, and a renewal or enrolment deadline is approaching."
        )
        stop = (
            "If you want this to stop, just say stop calling or hang up, "
            "and I will end the call."
        )
        return f"{who} {why} {stop}"

    who = (
        "नमस्ते"
        + (f" {name}" if name else "")
        + "। मैं जन सहाय हूँ, सरकारी योजनाओं की स्वचालित सहायक।"
    )
    why = (
        f"मैं इसलिए कॉल कर रही हूँ क्योंकि पहले आप {short} ({hi_name}) के लिए "
        f"संभावित पात्र लगे थे, और रिन्यूअल या नामांकन की समय सीमा नज़दीक है।"
    )
    stop = "अगर आप नहीं चाहतीं/चाहते, बस बोलिए 'कॉल बंद' या फोन काट दें — मैं कॉल समाप्त कर दूँगी।"
    return f"{who} {why} {stop}"


class OutboundAgent(Agent):
    def __init__(self, ctx: JobContext, meta: dict) -> None:
        lang = (meta.get("language") or "hi").lower()
        lang_note = (
            "\nLANGUAGE: Reply in English only this call.\n"
            if lang.startswith("en")
            else "\nLANGUAGE: Reply in Hindi only this call.\n"
        )
        name = meta.get("caller_name") or "caller"
        scheme = meta.get("scheme") or "pmsby"
        eligible = bool(meta.get("previously_eligible", True))
        context_note = (
            f"\nCALL CONTEXT: callee_name={name}; scheme={scheme}; "
            f"previously_eligible={eligible}; purpose=scheme_deadline_reminder.\n"
        )
        super().__init__(instructions=OUTBOUND_SYSTEM + lang_note + context_note)
        self.ctx = ctx
        self.meta = meta

    @function_tool
    async def get_deadline_reminder(self, context: RunContext) -> str:
        """Get the scheme deadline reminder script for this outbound call."""
        result = schemes.get_scheme_deadline_reminder(
            self.meta.get("scheme") or "pmsby",
            caller_name=self.meta.get("caller_name"),
            language=self.meta.get("language") or "hi",
        )
        return json.dumps(result)

    @function_tool
    async def get_document_checklist(
        self, context: RunContext, scheme_name: str | None = None
    ) -> str:
        """Return document checklist for the scheme being discussed."""
        name = scheme_name or self.meta.get("scheme") or "pmsby"
        return json.dumps(schemes.get_document_checklist(name))

    @function_tool
    async def get_scheme_info(
        self, context: RunContext, scheme_name: str | None = None
    ) -> str:
        """Return short scheme overview with dated figures."""
        name = scheme_name or self.meta.get("scheme") or "pmsby"
        return json.dumps(schemes.get_scheme_overview(name))

    @function_tool
    async def transfer_to_human(self, context: RunContext) -> str:
        """Transfer to a human when the callee explicitly asks."""
        if not TRANSFER_TO_NUMBER:
            return "Transfers unavailable. Offer a bank branch / CSC visit instead."
        await context.session.generate_reply(
            instructions="Say you are connecting them to a colleague now."
        )
        try:
            await self.ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=self.ctx.room.name,
                    participant_identity=CALLEE_IDENTITY,
                    transfer_to=f"tel:{TRANSFER_TO_NUMBER}",
                    play_dialtone=True,
                )
            )
        except Exception:
            logger.exception("transfer failed")
            return "Transfer failed. Apologize and offer a callback."
        return "Transferred."

    @function_tool
    async def detected_answering_machine(self, context: RunContext) -> str:
        """Hang up on voicemail / answering machine."""
        logger.info("answering machine — hangup")
        await self._hangup()
        return "Call ended."

    @function_tool
    async def end_call(self, context: RunContext) -> str:
        """End the call after goodbye."""
        await context.session.generate_reply(
            instructions="Thank them briefly and say goodbye in the call language."
        )
        await self._hangup()
        return "Call ended."

    async def _hangup(self) -> None:
        await self.ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=self.ctx.room.name)
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="outbound-agent")
async def outbound_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    meta = _parse_metadata(ctx.job.metadata)
    phone_number = meta.get("phone_number")
    if not phone_number:
        logger.error("missing phone_number in metadata — use dial.py --to ...")
        ctx.shutdown()
        return
    if not OUTBOUND_TRUNK_ID:
        logger.error("LIVEKIT_SIP_OUTBOUND_TRUNK_ID not set")
        ctx.shutdown()
        return

    await ctx.connect()
    db.init_db()

    # Persist lightweight outreach breadcrumb (no phone secrets beyond name/scheme).
    name = (meta.get("caller_name") or "").strip()
    if name:
        try:
            db.save_caller(
                user_id=name.lower().replace(" ", "_"),
                name=name,
                language_preference=meta.get("language") or "hi",
                facts={
                    "last_eligibility_scheme": meta.get("scheme") or "pmsby",
                    "last_eligibility_status": (
                        "likely_eligible"
                        if meta.get("previously_eligible", True)
                        else "unknown"
                    ),
                    "last_outreach": "scheme_deadline_reminder",
                },
                consent_given=True,
            )
        except Exception as err:
            logger.warning("could not save outreach breadcrumb: %s", err)

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY / NVIDIA_API_KEY required for Nemotron")
        ctx.shutdown()
        return

    lang = (meta.get("language") or "hi").lower()
    voice = VOICE_EN if lang.startswith("en") else VOICE_HI
    locale = LOCALE_EN if lang.startswith("en") else LOCALE_HI

    nvidia_llm = openai.LLM(
        model=NVIDIA_MODEL,
        api_key=api_key,
        base_url=NVIDIA_BASE_URL,
        temperature=0.5,
        max_completion_tokens=512,
        # Prevent Nemotron from speaking chain-of-thought / system instructions.
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=nvidia_llm,
        tts=murf.TTS(
            voice=voice,
            locale=locale,
            style=None,
            text_pacing=False,
            sample_rate=24000,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
        allow_interruptions=True,
    )

    agent = OutboundAgent(ctx, meta)
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
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
    )

    logger.info(
        "dialing %s meta=%s",
        phone_number,
        {k: meta[k] for k in meta if k != "phone_number"},
    )
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=OUTBOUND_TRUNK_ID,
                sip_call_to=phone_number,
                participant_identity=CALLEE_IDENTITY,
                participant_name=meta.get("caller_name") or "Phone user",
                wait_until_answered=True,
            )
        )
    except api.TwirpError as e:
        logger.error(
            "call to %s failed: %s (%s)",
            phone_number,
            e.message,
            e.metadata.get("sip_status") if e.metadata else None,
        )
        session_started.cancel()
        ctx.shutdown()
        return

    await session_started
    greeting = build_greeting(meta)
    logger.info("playing opening greeting (%d chars)", len(greeting))
    await session.say(greeting, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
