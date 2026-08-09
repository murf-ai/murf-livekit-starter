import json
import logging
import re

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    UserInputTranscribedEvent,
    cli,
    function_tool,
    llm,
    room_io,
)
from livekit.agents.llm import StopResponse
from livekit.plugins import deepgram, google, murf, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db
from prompt import SYSTEM_PROMPT

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Intro speech disabled — users found the long greeting slow and interruptive.
# Keep empty so session starts listening immediately.
FIRST_GREETING = ""

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
    "\n\nLANGUAGE NOW: User spoke English. Reply in English ONLY. "
    "Use zero Hindi words and zero Devanagari script. "
    "Do not greet in Hindi. Match English this turn even if history was Hindi.\n"
    "SAFETY: Never ask for OTP, PIN, or account number. "
    "Never promise scheme approval.\n"
)

VOICE_HI = "hi-IN-anisha"
VOICE_EN = "en-IN-anisha"
LOCALE_HI = "hi-IN"
LOCALE_EN = "en-IN"

# Common English function words — used to beat noisy multilingual STT.
_ENGLISH_MARKERS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "am",
    "was",
    "were",
    "be",
    "been",
    "what",
    "which",
    "who",
    "how",
    "when",
    "where",
    "why",
    "tell",
    "about",
    "please",
    "can",
    "could",
    "would",
    "should",
    "you",
    "your",
    "me",
    "my",
    "i",
    "we",
    "our",
    "want",
    "need",
    "help",
    "hello",
    "hi",
    "thanks",
    "thank",
    "scheme",
    "schemes",
    "government",
    "bank",
    "account",
    "insurance",
    "pension",
    "eligibility",
    "apply",
    "application",
    "some",
    "any",
    "this",
    "that",
    "with",
    "from",
    "for",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "do",
    "does",
    "did",
    "have",
    "has",
    "had",
    "know",
    "explain",
    "describe",
    "list",
    "give",
    "show",
}

# Marker used only inside chat context; stripped if re-seen so locks never stack.
_LANG_LOCK_PREFIX = "[[LANG_LOCK]]"
_MEMORY_PREFIX = "[[CALLER_MEMORY]]"


def detect_reply_language(transcript: str, stt_language: str | None = None) -> str:
    """Return 'hi' or 'en' from user transcript + optional STT language tag.

    Ignores non-Latin STT garbage (CJK etc.) so English speech is not forced to Hindi.
    """
    text = (transcript or "").strip()
    if not text:
        return "hi"

    # Devanagari script -> Hindi
    if DEVANAGARI_RE.search(text):
        return "hi"

    # Only Latin tokens count — drop Japanese/Korean STT hallucinations.
    latin_words = re.findall(r"[a-zA-Z']+", text.lower())
    if not latin_words:
        lang = (stt_language or "").lower().replace("_", "-")
        if lang.startswith("en"):
            return "en"
        return "hi"

    hindi_hits = sum(1 for w in latin_words if w in HINDI_KEYWORDS)
    en_hits = sum(1 for w in latin_words if w in _ENGLISH_MARKERS)

    # Clear English intent
    if en_hits >= 2 and hindi_hits <= 1:
        return "en"
    # Clear romanized Hindi / Hinglish
    if hindi_hits >= 2 and hindi_hits >= en_hits:
        return "hi"
    if hindi_hits >= 1 and en_hits == 0:
        return "hi"
    # Mostly Latin, no Hindi keywords -> English
    if hindi_hits == 0 and len(latin_words) >= 2:
        return "en"

    lang = (stt_language or "").lower().replace("_", "-")
    if lang.startswith("en"):
        return "en"
    if lang.startswith("hi"):
        return "hi"
    # Prefer English when mixed Latin text is ambiguous (better UX for English users).
    if en_hits >= 1:
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


# Extract a person name from common English/Hindi intro phrases.
_NAME_PATTERNS = [
    re.compile(
        r"(?:my name is|i am|i'm|this is|call me)\s+([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s'.-]{1,40})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:mera naam|meri naam|main|mai)\s+([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s'.-]{1,40})"
        r"(?:\s+hoon|\s+hun|\s+hu|\s+hai)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:naam hai|naam hain)\s+([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s'.-]{1,40})",
        re.IGNORECASE,
    ),
]

_NAME_STOPWORDS = {
    "jan",
    "sahay",
    "hello",
    "hi",
    "hey",
    "namaste",
    "please",
    "help",
    "here",
    "looking",
    "calling",
    "user",
    "agent",
    "yes",
    "no",
    "ok",
    "okay",
    "the",
    "a",
    "an",
}


def extract_caller_name(text: str) -> str | None:
    """Best-effort name extraction from a user utterance."""
    raw = (text or "").strip()
    if not raw:
        return None

    for pattern in _NAME_PATTERNS:
        match = pattern.search(raw)
        if not match:
            continue
        candidate = match.group(1).strip(" .,!?:;\"'")
        # Keep first 3 tokens max (e.g. "Raj Kumar Sharma")
        parts = [p for p in re.split(r"\s+", candidate) if p]
        parts = parts[:3]
        if not parts:
            continue
        # Drop trailing filler words
        while parts and parts[-1].lower() in {
            "hoon",
            "hun",
            "hu",
            "hai",
            "and",
            "ji",
            "sir",
            "madam",
        }:
            parts.pop()
        if not parts:
            continue
        if any(p.lower() in _NAME_STOPWORDS for p in parts):
            continue
        if all(len(p) <= 1 for p in parts):
            continue
        name = " ".join(parts).strip()
        if 1 < len(name) <= 40:
            return name.title() if name.isascii() else name
    return None


def _format_memory_note(caller: dict) -> str:
    """Compact system note so the LLM can greet returning callers."""
    name = caller.get("name") or caller.get("user_id") or "caller"
    facts = caller.get("facts") or {}
    facts_bits = []
    for key, value in list(facts.items())[:6]:
        facts_bits.append(f"{key}={value}")
    facts_txt = "; ".join(facts_bits) if facts_bits else "no saved scheme facts yet"
    lang = caller.get("language_preference") or "unknown"
    return (
        f"{_MEMORY_PREFIX} RETURNING CALLER MEMORY: name={name}; "
        f"language_preference={lang}; facts=[{facts_txt}]. "
        f"Greet them by name, mention you remember them, and reference useful facts briefly."
    )


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT + REPLY_LANG_HI,
            # Let the user barge in freely so the agent does not "get stuck" talking.
        )
        self._reply_lang = "hi"
        self._last_stt_language: str | None = None
        self._voice = VOICE_HI
        self._known_caller_name: str | None = None
        self._memory_loaded = False

    @function_tool
    async def lookup_caller(self, ctx: RunContext, name_or_id: str) -> str:
        """Lookup stored caller profile and memory facts by name or user_id (e.g. 'Ramesh').
        Call this tool when a caller introduces themselves by name or asks if you remember them.
        """
        caller = db.get_caller(name_or_id)
        if not caller:
            return f"No record found for '{name_or_id}'."
        self._known_caller_name = caller.get("name") or name_or_id
        self._memory_loaded = True
        return json.dumps(caller)

    @function_tool
    async def save_caller_memory(
        self,
        ctx: RunContext,
        name: str,
        facts: dict | None = None,
        language_preference: str | None = None,
    ) -> str:
        """Save caller profile and facts (such as schemes checked, eligibility answers) keyed by name.
        Call this tool when the user provides their name to save the conversation (e.g. 'My name is Raj').
        STRICT PRIVACY RULE: Do NOT store account numbers, Aadhaar, PAN, PIN, or OTP.
        """
        clean_name = (name or "").strip()
        if not clean_name:
            return json.dumps({"saved": False, "message": "Name is required."})
        user_id = clean_name.lower().replace(" ", "_")
        res = db.save_caller(
            user_id=user_id,
            name=clean_name,
            language_preference=language_preference or self._reply_lang,
            facts=facts or {},
            consent_given=True,
        )
        self._known_caller_name = clean_name
        self._memory_loaded = True
        logger.info("save_caller_memory saved profile for %s: %s", clean_name, res)
        return json.dumps(res)

    def _auto_memory_for_turn(
        self, turn_ctx: llm.ChatContext, text: str
    ) -> None:
        """Lookup/save memory from name phrases without waiting on the LLM tool call."""
        name = extract_caller_name(text)
        if not name:
            # If caller already known this session, still touch last_interaction lightly
            return

        existing = db.get_caller(name)
        if existing:
            self._known_caller_name = existing.get("name") or name
            self._memory_loaded = True
            _strip_lang_locks(turn_ctx)
            turn_ctx.add_message(role="system", content=_format_memory_note(existing))
            # Refresh last_interaction timestamp
            db.save_caller(
                user_id=existing["user_id"],
                name=existing.get("name") or name,
                language_preference=existing.get("language_preference")
                or self._reply_lang,
                facts={},
                consent_given=True,
            )
            logger.info("Auto-loaded returning caller memory for %s", name)
            return

        # First-time name mention: create a lightweight profile so next call can recall them.
        user_id = name.lower().replace(" ", "_")
        res = db.save_caller(
            user_id=user_id,
            name=name,
            language_preference=self._reply_lang,
            facts={"introduced_via": "auto_name_detect"},
            consent_given=True,
        )
        self._known_caller_name = name
        self._memory_loaded = True
        logger.info("Auto-saved new caller profile for %s: %s", name, res)

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
            locale = LOCALE_HI if reply_lang == "hi" else LOCALE_EN
            if voice != self._voice:
                tts = self.session.tts if self.session else None
                if tts is not None and hasattr(tts, "update_options"):
                    # style=None = default Murf style (Conversation style caused beeps)
                    tts.update_options(voice=voice, locale=locale, style=None)
                    self._voice = voice
                    logger.info("Switched TTS voice=%s locale=%s", voice, locale)

        return reply_lang

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Lock language for this turn without polluting history or stacking locks."""
        text = new_message.text_content or ""
        text_clean = text.strip().lower()
        words = re.findall(r"[a-zA-Z\u0900-\u097F']+", text_clean)

        # Drop empty / filler / ultra-short STT hallucinations (often echo fragments).
        noise = {
            "[music]",
            "[applause]",
            "[noise]",
            ".",
            "..",
            "...",
            "huh",
            "uh",
            "um",
            "hmm",
            "mm",
            "mhm",
            "ah",
            "oh",
        }
        if (
            not text_clean
            or text_clean in noise
            or len(words) < 2
            or len(text_clean) < 6
        ):
            logger.info("Ignoring noise/echo transcript: %r", text)
            raise StopResponse()

        reply_lang = await self.apply_language(text, self._last_stt_language)

        # Cross-call memory: auto lookup/save when user shares a name.
        try:
            self._auto_memory_for_turn(turn_ctx, text)
        except Exception as err:  # noqa: BLE001 - never block the reply path
            logger.warning("Auto memory hook failed: %s", err)

        # Keep at most ONE ephemeral language lock in context (replace, never stack).
        # If a returning-caller memory note was just injected, keep it (same prefix family
        # is stripped only for pure LANG locks below via content check).
        _strip_lang_locks(turn_ctx)
        if reply_lang == "en":
            lock = (
                f"{_LANG_LOCK_PREFIX} CRITICAL: Reply in English ONLY this turn. "
                "No Hindi words. No Devanagari. No Hinglish. "
                "Never ask for OTP, PIN, or account number. "
                "Never promise scheme approval."
            )
        else:
            lock = (
                f"{_LANG_LOCK_PREFIX} CRITICAL: Reply in Hindi only this turn. "
                "OTP, PIN, ya account number kabhi mat mango. "
                "Scheme approval kabhi guarantee mat karo."
            )
        turn_ctx.add_message(role="system", content=lock)

        # Re-attach memory note AFTER lang lock strip so it survives this turn.
        if self._known_caller_name and self._memory_loaded:
            caller = db.get_caller(self._known_caller_name)
            if caller:
                turn_ctx.add_message(role="system", content=_format_memory_note(caller))

        logger.info("Turn language lock set once: %s", reply_lang)


# Keep one warm process so the next call after END CALL joins quickly.
server = AgentServer(num_idle_processes=1)


def prewarm(proc: JobProcess):
    # Stricter VAD so speaker echo / room noise is less likely to start a turn.
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.5,
        min_silence_duration=0.8,
        activation_threshold=0.75,
        prefix_padding_duration=0.3,
    )


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Prefer models that still have free-tier quota (2.0-flash* is exhausted).
    gemini_models = (
        "gemini-2.5-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
    )
    # Gemini rejects deadlines under 10s ("Manually set deadline is too short").
    llm_stack = llm.FallbackAdapter(
        [google.LLM(model=name) for name in gemini_models],
        attempt_timeout=20.0,
        max_retry_per_llm=1,
        retry_interval=0.5,
    )
    logger.info("LLM fallback stack: %s", ", ".join(gemini_models))

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=llm_stack,
        tts=murf.TTS(
            voice=VOICE_HI,
            locale=LOCALE_HI,
            style=None,  # default style — Conversation caused audio beeps/glitches
            text_pacing=False,  # pacing can introduce choppy/beepy audio
            min_buffer_size=50,  # smoother stream chunks
            max_buffer_delay_in_ms=200,
            sample_rate=24000,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
        allow_interruptions=True,
        min_interruption_duration=0.6,
        min_interruption_words=2,
        min_endpointing_delay=0.5,
        max_endpointing_delay=2.5,
        false_interruption_timeout=1.5,
        resume_false_interruption=True,
        aec_warmup_duration=3.0,
        discard_audio_if_uninterruptible=True,
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

    # CRITICAL: connect to room FIRST, then start session
    await ctx.connect()
    db.init_db()
    logger.info("Room connected, starting agent session for %s", ctx.room.name)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            text_input=True,
            text_output=True,
        ),
    )

    async def cleanup():
        # Persist a light breadcrumb if we learned a name this call.
        if agent._known_caller_name:
            try:
                db.save_caller(
                    user_id=agent._known_caller_name.lower().replace(" ", "_"),
                    name=agent._known_caller_name,
                    language_preference=agent._reply_lang,
                    facts={"last_room": ctx.room.name},
                    consent_given=True,
                )
            except Exception as err:  # noqa: BLE001
                logger.warning("Failed to persist session breadcrumb: %s", err)
        logger.info("Session finished cleanly for room: %s", ctx.room.name)

    ctx.add_shutdown_callback(cleanup)

    # No spoken intro — jump straight to listening so the call feels instant.
    if FIRST_GREETING.strip():
        try:
            await session.say(FIRST_GREETING, allow_interruptions=True)
        except Exception as err:
            logger.error("Error playing initial greeting: %s", err)
    else:
        logger.info("Skipping intro speech; agent is listening immediately")


if __name__ == "__main__":
    cli.run_app(server)
