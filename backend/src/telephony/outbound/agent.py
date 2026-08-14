"""Outbound telephony agent for Dhan Rakshak — places calls via Linphone/SIP and
informs recipients about government scheme deadlines.

Run the worker:
    uv run python src/telephony/outbound/agent.py dev

Trigger a call (from another terminal):
    uv run python src/telephony/outbound/dial.py --to abhiram05

See the supplementary guide for Linphone trunk setup.
"""

import json
import logging
import os
import random

from livekit.api.twirp_client import TwirpError

from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("dhan-rakshak-outbound")

# Always resolve .env.local relative to the backend/ directory
# (this file lives at: backend/src/telephony/outbound/agent.py → 3 levels up)
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(_BACKEND_DIR, ".env.local"))

# Required — set LIVEKIT_SIP_TRUNK_ID in .env.local (from LiveKit Cloud → SIP Trunks)
OUTBOUND_TRUNK_ID = os.getenv("LIVEKIT_SIP_TRUNK_ID")

# The identity LiveKit will give the SIP participant we are calling
CALLEE_IDENTITY = "sip-callee"

SCHEMES_LIST = [
    "Pradhan Mantri Jan Dhan Yojana",
    "Pradhan Mantri Suraksha Bima Yojana",
    "Pradhan Mantri Jeevan Jyoti Bima Yojana",
    "Atal Pension Yojana",
    "Sukanya Samriddhi Yojana",
]

SYSTEM_PROMPT = (
    "You are Shreya, a voice assistant calling from Dhan Rakshak. "
    "Your purpose: notify the person about a government scheme deadline and answer "
    "basic eligibility questions if they are interested. "
    "Rules:\n"
    "- You placed this call, so the person did NOT ask for it. Open with exactly "
    "  the two-sentence greeting provided to you. Wait for their response.\n"
    "- Keep all responses extremely short — under 15 words.\n"
    "- If they say 'yes' or show interest, briefly explain (one sentence) the "
    "  scheme you mentioned.\n"
    "- If they say 'no' or want to opt out, respond: "
    "  'To stop these calls, press or say 1.' Then say goodbye and use end_call.\n"
    "- If they ask a question you cannot answer, say you'll have someone follow up.\n"
    "- Never read out long paragraphs. No bullet points, emojis, or formatting.\n"
    "- When the conversation is naturally over, call end_call."
)


class DhanRakshakOutboundAgent(Agent):
    def __init__(self, ctx: JobContext, selected_scheme: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.ctx = ctx
        self.selected_scheme = selected_scheme

    @function_tool
    async def end_call(self, context: RunContext) -> None:
        """End the current phone call. Call this when the conversation is complete or the user opts out."""
        logger.info("Ending outbound call — deleting room.")
        await context.session.generate_reply(
            instructions="Say a polite goodbye in one short sentence."
        )
        await self.ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=self.ctx.room.name)
        )


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server = AgentServer()
server.setup_fnc = prewarm


@server.rtc_session(agent_name="dhan-rakshak-outbound")
async def outbound_agent(ctx: JobContext) -> None:
    """Entry point dispatched by dial.py. Reads phone number from job metadata."""

    # Parse the phone number / SIP target from job metadata
    try:
        dial_info = json.loads(ctx.job.metadata or "{}")
    except (json.JSONDecodeError, AttributeError):
        dial_info = {}

    sip_target = dial_info.get("phone_number", "")
    if not sip_target:
        logger.error("No phone_number in job metadata — cannot place outbound call.")
        ctx.shutdown()
        return

    logger.info(f"Placing outbound SIP call to: {sip_target}")

    selected_scheme = random.choice(SCHEMES_LIST)

    # LiveKit's sip_call_to only accepts:
    #   - A bare E.164 phone number:  +91XXXXXXXXXX
    #   - A SIP *username* only:      abhiram05   (NO domain, NO 'sip:' prefix)
    # The trunk already knows the SIP server address (sip.linphone.org),
    # so passing the domain causes a 400 "full SIP URI" error.
    raw = sip_target.removeprefix("sip:")
    # If it contains @domain, keep only the user part (unless it's a phone number)
    if "@" in raw and not raw.startswith("+"):
        sip_call_to = raw.split("@")[0]   # e.g. abhiram05
    else:
        sip_call_to = raw                  # e.g. +91XXXXXXXXXX
    logger.info(f"sip_call_to resolved to: '{sip_call_to}'")

    # 1. Dial the number via LiveKit SIP and wait for the recipient to answer
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=OUTBOUND_TRUNK_ID,
                sip_call_to=sip_call_to,
                participant_identity=CALLEE_IDENTITY,
                participant_name="Callee",
                wait_until_answered=True,
            )
        )
        logger.info("Call answered successfully.")
    except TwirpError as e:
        logger.error(f"Outbound call failed (TwirpError): {e}")
        ctx.shutdown()
        return
    except Exception as e:
        logger.error(f"Outbound call failed (unexpected): {e}")
        ctx.shutdown()
        return

    # Step 2: Connect the agent to the LiveKit room.
    # This MUST happen before wait_for_participant() — the room must be
    # connected for the agent to observe participants joining.
    await ctx.connect()
    logger.info("Agent connected to room.")

    # Step 3: Wait for the SIP participant to fully appear in the room.
    participant = await ctx.wait_for_participant(identity=CALLEE_IDENTITY)
    logger.info(f"SIP participant joined: {participant.identity}")

    # Step 4: Build and start the voice pipeline session.
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.6-flash"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
    )

    await session.start(
        agent=DhanRakshakOutboundAgent(ctx, selected_scheme),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Step 5: On outbound calls the agent speaks first.
    # Deliver the Day-6 compliant 2-sentence opening:
    #   1. Who is calling and from where
    #   2. Why they are calling + how to opt out
    await session.say(
        f"Hello, this is Shreya calling from Dhan Rakshak. "
        f"We found you eligible for the {selected_scheme} scheme, and the deadline is on August 15th, so hurry up! "
        f"If you want to know more, say yes, and if you want to stop these calls, say no.",
        allow_interruptions=True,
    )



if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)
