"""Outbound SIP agent — Day 6 scheme reminders + Day 7 escalation resolve notify.

Places a SIP call (Twilio trunk or Linphone mobile client), opens with
who/why/how-to-stop, then either:
  - Day 6: reminds about an approaching scheme deadline, or
  - Day 7: notifies that a human-escalated case was resolved (reference ID).

Run worker:
    uv run python src/telephony/outbound/agent.py dev

Dial (Day 6):
    uv run python src/telephony/outbound/dial.py --to <number|linphone-user> \\
      --name Ramesh --scheme pmsby --lang hi

Resolve + notify (Day 7):
    uv run python src/telephony/outbound/resolve_notify.py \\
      --ref JS-A1B2C3D4 --to <linphone-user> --notes "…"

Trunk setup: src/telephony/README.md (Linphone mobile path recommended).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
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

# Load backend/.env.local, then src/test/.env.local overrides for telephony.
_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_SRC_ROOT = Path(__file__).resolve().parents[2]
# override=True so a stale shell OPENAI_API_KEY cannot mask the nvapi key
load_dotenv(_BACKEND_ROOT / ".env.local", override=True)
load_dotenv(_SRC_ROOT / "test" / ".env.local", override=True)
load_dotenv(".env.local", override=True)

# Day 6/7 telephony (Linphone free path or Twilio)
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

OUTBOUND_SYSTEM_SCHEME = """
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

OUTBOUND_SYSTEM_RESOLUTION = """
IDENTITY: You are Jan Sahay (जन सहाय) — authoritative, empathetic, professional
financial customer service for a top-tier institution, speaking over mobile SIP
(Linphone). You are on an OUTBOUND resolution-notification call.

OPENING (already spoken once — do not re-introduce fully):
- Who you are, that a specialist reviewed their escalated case, the reference ID,
  and that they can say "stop calling" / "कॉल बंद" to end.

MISSION (Day 7):
- Confirm the case status (resolved) and read the reference ID clearly.
- Share the scrubbed resolution outcome from CALL CONTEXT — never invent extra claims.
- Never promise immediate live-agent pickup, refunds, or limit changes on this call.
- Never ask for OTP, PIN, password, CVV, full account number, or Aadhaar.
- If they still need help: offer bank branch / CSC / helpline, or transfer_to_human if available.
- Keep replies under ~35 spoken words. No markdown, bullets, or emojis.
- Match the call language from session context.
- If voicemail: use detected_answering_machine. When done: goodbye then end_call.
"""


def _parse_metadata(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"phone_number": raw.strip()}
    except json.JSONDecodeError:
        return {"phone_number": raw.strip()} if raw.strip() else {}


def _scrub_spoken(text: str | None) -> str:
    """Lightweight secret scrub before TTS on mobile networks."""
    if not text:
        return ""
    cleaned = str(text)
    cleaned = re.sub(
        r"\b(?:otp|pin|password|cvv|cvc)\s*[:=]?\s*\S+",
        "[redacted]",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\b\d{10,18}\b", "[redacted]", cleaned)
    return cleaned.strip()


def build_greeting(meta: dict) -> str:
    """Opening audio: who / why / how-to-stop (Day 6 or Day 7)."""
    purpose = (meta.get("purpose") or "scheme_deadline_reminder").lower()
    if purpose == "escalation_resolution":
        return build_resolution_greeting(meta)
    return build_scheme_greeting(meta)


def build_scheme_greeting(meta: dict) -> str:
    """Day 6 scheme deadline opening."""
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


def build_resolution_greeting(meta: dict) -> str:
    """Day 7 escalation-resolution opening for Linphone / mobile SIP."""
    name = (meta.get("caller_name") or "").strip()
    lang = (meta.get("language") or "hi").lower()
    ref = (meta.get("reference_id") or "unknown").strip()
    notes = _scrub_spoken(meta.get("resolution_notes") or "")

    if lang.startswith("en"):
        who = (
            "Hello"
            + (f" {name}" if name else "")
            + ". This is Jan Sahay from the specialist follow-up desk."
        )
        why = (
            f"I am calling about your escalated case, reference {ref}, "
            "which a human specialist has now marked as resolved."
        )
        if notes:
            why += f" Outcome summary: {notes}."
        stop = (
            "If you want this to stop, say stop calling or hang up. "
            "I will not ask for OTP, PIN, or account numbers."
        )
        return f"{who} {why} {stop}"

    who = (
        "नमस्ते"
        + (f" {name}" if name else "")
        + "। मैं जन सहाय हूँ, specialist follow-up desk से।"
    )
    why = (
        f"मैं आपके escalated case, reference {ref}, के बारे में कॉल कर रही हूँ — "
        "human specialist ने इसे resolved चिन्हित किया है।"
    )
    if notes:
        why += f" संक्षिप्त परिणाम: {notes}."
    stop = (
        "अगर कॉल बंद करनी हो तो 'कॉल बंद' बोलें या फोन काट दें। "
        "OTP, PIN, या account number कभी नहीं माँगे जाएँगे।"
    )
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
        purpose = (meta.get("purpose") or "scheme_deadline_reminder").lower()

        if purpose == "escalation_resolution":
            base = OUTBOUND_SYSTEM_RESOLUTION
            context_note = (
                f"\nCALL CONTEXT: purpose=escalation_resolution; "
                f"callee_name={name}; "
                f"reference_id={meta.get('reference_id') or 'unknown'}; "
                f"resolution_notes={_scrub_spoken(meta.get('resolution_notes'))}; "
                f"issue_description={_scrub_spoken(meta.get('issue_description'))}; "
                f"follow_up_method={meta.get('follow_up_method') or 'voice_callback'}.\n"
            )
        else:
            base = OUTBOUND_SYSTEM_SCHEME
            scheme = meta.get("scheme") or "pmsby"
            eligible = bool(meta.get("previously_eligible", True))
            context_note = (
                f"\nCALL CONTEXT: callee_name={name}; scheme={scheme}; "
                f"previously_eligible={eligible}; purpose=scheme_deadline_reminder.\n"
            )

        super().__init__(instructions=base + lang_note + context_note)
        self.ctx = ctx
        self.meta = meta
        self.purpose = purpose

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
        result = schemes.get_document_checklist(name)
        db.record_document_list_result(self.ctx.room.name, result)
        return json.dumps(result)

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
    # Tuned for mobile SIP / Linphone: reduce false barge-ins from network noise.
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.4,
        min_silence_duration=0.7,
        activation_threshold=0.7,
        prefix_padding_duration=0.25,
    )


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
    db.start_call(ctx.room.name, "sip")

    async def cleanup():
        try:
            # Connected SIP call = success. Cancel before connect = failure.
            db.end_call(ctx.room.name, "sip")
        except Exception as err:
            logger.warning("Failed to record SIP call outcome: %s", err)

    ctx.add_shutdown_callback(cleanup)

    purpose = (meta.get("purpose") or "scheme_deadline_reminder").lower()
    # Persist lightweight outreach breadcrumb (no phone secrets beyond name/scheme).
    name = (meta.get("caller_name") or "").strip()
    if name:
        try:
            facts: dict = {"last_outreach": purpose}
            if purpose == "escalation_resolution":
                facts["last_escalation_ref"] = meta.get("reference_id") or ""
                facts["last_escalation_status"] = "resolved"
            else:
                facts["last_eligibility_scheme"] = meta.get("scheme") or "pmsby"
                facts["last_eligibility_status"] = (
                    "likely_eligible"
                    if meta.get("previously_eligible", True)
                    else "unknown"
                )
            db.save_caller(
                user_id=name.lower().replace(" ", "_"),
                name=name,
                language_preference=meta.get("language") or "hi",
                facts=facts,
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

    # Low-latency mobile SIP pipeline: tighter endpointing, telephony NC later.
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=nvidia_llm,
        tts=murf.TTS(
            voice=voice,
            locale=locale,
            style=None,
            text_pacing=False,
            min_buffer_size=40,
            max_buffer_delay_in_ms=180,
            sample_rate=24000,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
        allow_interruptions=True,
        min_interruption_duration=0.5,
        min_endpointing_delay=0.4,
        max_endpointing_delay=2.0,
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
        db.record_tool_error(ctx.room.name)
        ctx.shutdown()
        return

    db.mark_call_connected(ctx.room.name)
    await session_started
    greeting = build_greeting(meta)
    logger.info("playing opening greeting (%d chars)", len(greeting))
    await session.say(greeting, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
