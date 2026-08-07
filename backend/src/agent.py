import logging
import re

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    UserInputTranscribedEvent,
    cli,
    llm,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from prompt import SYSTEM_PROMPT

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Spoken once when the session starts — not on every user turn.
FIRST_GREETING = (
    "नमस्ते! मैं जन सहाय हूँ। मुझे अपनी फाइनेंशियल दोस्त समझिए। "
    "मैं सरकारी वित्तीय योजनाओं और सुरक्षित डिजिटल बैंकिंग के बारे में आपकी मदद कर सकता हूँ। "
    "बताइए, आज मैं आपकी कैसे मदद करूँ?"
)

# Strong romanized Hindi / Hinglish markers (avoid English-only words).
HINDI_KEYWORDS = {
    "yojana",
    "yojna",
    "batao",
    "bataye",
    "bataiye",
    "samjhao",
    "samjhaao",
    "samjha",
    "dhan",
    "suraksha",
    "bima",
    "mujhe",
    "mera",
    "meri",
    "mere",
    "apna",
    "apni",
    "apne",
    "namaste",
    "namaskar",
    "kaise",
    "kaisa",
    "kaisi",
    "kya",
    "kyun",
    "kyu",
    "hai",
    "hain",
    "nahi",
    "nahin",
    "mat",
    "madad",
    "sahayata",
    "khata",
    "kripya",
    "dhanyavad",
    "shukriya",
    "accha",
    "achha",
    "theek",
    "thik",
    "bilkul",
    "zaroor",
    "jaroor",
    "chahiye",
    "chaahiye",
    "karo",
    "kariye",
    "bata",
    "suniye",
    "sunao",
    "aap",
    "aapka",
    "aapki",
}

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

# Compact language directives — kept short to avoid instruction thrash.
REPLY_LANG_HI = (
    "\n\nLANGUAGE NOW: User spoke Hindi/Hinglish. Reply in Hindi only. "
    "Do not use full English. Match this turn, not older English turns.\n"
    "SAFETY: Never ask for OTP, PIN, or account number. "
    "Never promise scheme approval.\n"
)

REPLY_LANG_EN = (
    "\n\nLANGUAGE NOW: User spoke English. Reply in English only. "
    "No Hindi or Devanagari, even if your greeting was Hindi.\n"
    "SAFETY: Never ask for OTP, PIN, or account number. "
    "Never promise scheme approval.\n"
)

VOICE_HI = "hi-IN-anisha"
VOICE_EN = "en-IN-anisha"

# Marker used only inside chat context; stripped if re-seen so locks never stack.
_LANG_LOCK_PREFIX = "[[LANG_LOCK]]"


def detect_reply_language(transcript: str, stt_language: str | None = None) -> str:
    """Return 'hi' or 'en' from user transcript + optional STT language tag."""
    text = (transcript or "").strip()
    if not text:
        return "hi"

    if DEVANAGARI_RE.search(text):
        return "hi"

    lang = (stt_language or "").lower().replace("_", "-")
    words = set(re.findall(r"[a-zA-Z']+", text.lower()))
    has_hindi_kw = not words.isdisjoint(HINDI_KEYWORDS)

    if lang.startswith("en") and not has_hindi_kw:
        return "en"
    if lang.startswith("hi"):
        return "hi"
    if has_hindi_kw:
        return "hi"
    if lang.startswith("en"):
        return "en"
    if text.isascii() and not has_hindi_kw:
        return "en"
    return "hi"


def _strip_lang_locks(turn_ctx: llm.ChatContext) -> None:
    """Remove previous language-lock system messages so they never accumulate."""
    items = getattr(turn_ctx, "items", None)
    if not items:
        return
    keep = []
    for item in list(items):
        if (
            getattr(item, "type", None) == "message"
            and getattr(item, "role", None) == "system"
        ):
            text = item.text_content or ""
            if text.startswith(_LANG_LOCK_PREFIX):
                continue
        keep.append(item)
    if len(keep) != len(items):
        items[:] = keep


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT + REPLY_LANG_HI,
            # Let the user barge in freely so the agent does not "get stuck" talking.
        )
        self._reply_lang = "hi"
        self._last_stt_language: str | None = None
        self._voice = VOICE_HI

    def note_stt_language(self, language: str | None, transcript: str) -> None:
        if language:
            self._last_stt_language = str(language)

    async def apply_language(
        self, transcript: str, stt_language: str | None = None
    ) -> str:
        lang_hint = stt_language or self._last_stt_language
        reply_lang = detect_reply_language(transcript, lang_hint)
        logger.info(
            "Language detect: lang=%s stt=%s text=%r",
            reply_lang,
            lang_hint,
            (transcript or "")[:120],
        )

        # Only refresh instructions / voice when language actually changes.
        # Constant updates race the LLM/TTS and can stall or double-speak.
        if reply_lang != self._reply_lang:
            self._reply_lang = reply_lang
            directive = REPLY_LANG_HI if reply_lang == "hi" else REPLY_LANG_EN
            await self.update_instructions(SYSTEM_PROMPT + directive)
            logger.info("Updated instructions for language=%s", reply_lang)

            voice = VOICE_HI if reply_lang == "hi" else VOICE_EN
            if voice != self._voice:
                tts = self.session.tts if self.session else None
                if tts is not None and hasattr(tts, "update_options"):
                    tts.update_options(voice=voice)
                    self._voice = voice
                    logger.info("Switched TTS voice to %s", voice)

        return reply_lang

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Lock language for this turn without polluting history or stacking locks."""
        text = new_message.text_content or ""
        # Ignore empty / noise turns so we do not thrash language state.
        if not text.strip():
            return

        reply_lang = await self.apply_language(text, self._last_stt_language)

        # Keep at most ONE ephemeral language lock in context (replace, never stack).
        _strip_lang_locks(turn_ctx)
        if reply_lang == "en":
            lock = (
                f"{_LANG_LOCK_PREFIX} Reply in English only for this turn. "
                "Never ask for OTP, PIN, or account number. "
                "Never promise scheme approval."
            )
        else:
            lock = (
                f"{_LANG_LOCK_PREFIX} Reply in Hindi only for this turn. "
                "OTP, PIN, ya account number kabhi mat mango. "
                "Scheme approval kabhi guarantee mat karo."
            )
        turn_ctx.add_message(role="system", content=lock)
        logger.info("Turn language lock set once: %s", reply_lang)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        # Free-tier quotas are per model. gemini-2.5-flash / 2.0-flash hit 429
        # (20 req/day). gemini-flash-lite-latest still has quota and works.
        llm=google.LLM(
            model="gemini-flash-lite-latest",
        ),
        tts=murf.TTS(
            voice=VOICE_HI,
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # Avoid racing a second reply before the user finished speaking.
        preemptive_generation=False,
    )

    agent = Assistant()

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        if not ev.is_final:
            return
        language = str(ev.language) if ev.language else None
        agent.note_stt_language(language, ev.transcript)
        logger.info(
            "STT final transcript lang=%s text=%r",
            language,
            (ev.transcript or "")[:120],
        )

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            text_input=True,
            text_output=True,
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

    # One greeting only; user can interrupt immediately.
    await session.say(FIRST_GREETING, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
