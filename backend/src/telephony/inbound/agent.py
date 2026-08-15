"""Inbound telephony agent — answers incoming phone calls.

A caller dials your phone number, your SIP provider forwards the call to LiveKit,
and LiveKit's dispatch rule routes it to this agent by name ("inbound-agent").

Run it with:

    uv run python src/telephony/inbound/agent.py dev

See src/telephony/README.md for the trunk and dispatch rule setup.
"""

import logging
import os

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
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("inbound-agent")

load_dotenv(".env.local")

# Optional — a phone number to transfer callers to when they ask for a human.
# Leave unset and the transfer tool politely declines instead.
TRANSFER_TO_NUMBER = os.getenv("TRANSFER_TO_NUMBER")

# Change this prompt to change what your phone agent does.
SYSTEM_PROMPT = """You are a friendly receptionist answering calls for a small business. Help callers with questions about hours, services, and locations, and take messages when needed. You are speaking on a phone call, so keep responses short and conversational — no formatting, emojis, or symbols. If the caller asks for a human, use the transfer_to_human tool. When the conversation is finished and the caller says goodbye, use the end_call tool."""

# The first thing the caller hears when they pick up.
GREETING = "Thanks for calling! How can I help you today?"


class InboundAgent(Agent):
    def __init__(self, ctx: JobContext, caller_identity: str | None) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.ctx = ctx
        # The LiveKit participant identity of the caller — needed to transfer them.
        self.caller_identity = caller_identity

    @function_tool
    async def transfer_to_human(self, context: RunContext) -> str:
        """Transfer the caller to a human colleague.

        Use this when the caller explicitly asks for a person, or when you cannot
        help them with their request.
        """
        if not TRANSFER_TO_NUMBER or not self.caller_identity:
            return "Transfers are not available on this line. Offer to take a message instead."

        # Tell the caller before transferring — the SIP transfer cuts off the audio.
        await context.session.generate_reply(
            instructions="Tell the caller you're connecting them to a colleague now."
        )

        logger.info("transferring caller to %s", TRANSFER_TO_NUMBER)
        try:
            await self.ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=self.ctx.room.name,
                    participant_identity=self.caller_identity,
                    transfer_to=f"tel:{TRANSFER_TO_NUMBER}",
                    play_dialtone=True,
                )
            )
        except Exception:
            logger.exception("transfer failed")
            return "The transfer did not go through. Apologize and offer to take a message."

        return "Transferred."

    @function_tool
    async def end_call(self, context: RunContext) -> str:
        """Hang up the call.

        Use this only once the caller has said goodbye or the conversation is clearly over.
        """
        # Let the agent finish its closing line before the call drops.
        await context.session.generate_reply(
            instructions="Say a short, warm goodbye to the caller."
        )

        logger.info("ending call")
        await self.ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=self.ctx.room.name)
        )
        return "Call ended."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


def caller_phone_number(participant: rtc.RemoteParticipant) -> str | None:
    """The caller's phone number, if this participant arrived over SIP.

    LiveKit puts the caller ID in a participant attribute. Browser participants
    (i.e. anyone testing from the frontend) will not have it.
    """
    if participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        return None
    return participant.attributes.get("sip.phoneNumber")


@server.rtc_session(agent_name="inbound-agent")
async def inbound_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Join the room first so we can read the caller's details before greeting them.
    await ctx.connect()
    participant = await ctx.wait_for_participant()

    phone_number = caller_phone_number(participant)
    logger.info(
        "inbound call answered",
        extra={"caller": phone_number or "unknown", "identity": participant.identity},
    )

    # Same voice pipeline as src/agent.py — see that file for the annotated version.
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(
            model="gemini-2.5-flash",
        ),
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=InboundAgent(ctx, participant.identity),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                # BVCTelephony is tuned for the narrow frequency range of phone audio.
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Speak first — the caller dialled you, so they expect to be greeted.
    await session.say(GREETING, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
