import json
import logging
import os
import re
import time

from dotenv import load_dotenv
from livekit import rtc
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
from livekit.agents.voice.generation import (
    update_instructions as patch_chat_instructions,
)
from livekit.plugins import deepgram, murf, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db
import escalation
import metrics
import schemes
from prompt import SYSTEM_PROMPT

logger = logging.getLogger("agent")

# override=True so a stale shell OPENAI_API_KEY cannot mask .env.local (Nemotron nvapi key)
load_dotenv(".env.local", override=True)

# NVIDIA Nemotron via OpenAI-compatible Integrate API
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/nemotron-3-nano-30b-a3b"

# Spoken once when the session starts — short so it is not interruptive.
# Long intros made the call feel slow; empty greeting made the agent feel dead.
FIRST_GREETING = "नमस्ते! मैं जन सहाय हूँ। आज कैसे मदद करूँ?"

# Short greets that must NOT be treated as STT noise (single-word is fine).
_ALLOWED_SHORT_GREETS = {
    "hi",
    "hello",
    "hey",
    "yo",
    "namaste",
    "namaskar",
    "hola",
    "thanks",
    "thank you",
    "धन्यवाद",
    "शुक्रिया",
    "नमस्ते",
    "नमस्कार",
    "हां",
    "हाँ",
    "जी",
    "yes",
    "no",
    "ok",
    "okay",
    "theek",
    "thik",
    "accha",
    "achha",
    "yep",
    "yup",
    "sure",
    "haan",
    "na",
    "naah",
    "nahi",
    "nahin",
    "save",
}

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
    "haan",
    "han",
    "ji",
    "lagenge",
    "lagega",
    "bare",
    "baare",
    "mein",
    "main",
    "liye",
    "ke",
    "ko",
    "se",
    "ka",
    "ki",
    "hoon",
    "hun",
    "hu",
    "paatrata",
    "patrata",
    "yojnaein",
    "sarkari",
}

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

# Compact language directives — kept short to avoid instruction thrash.
# OUTPUT RULE is critical: Nemotron otherwise narrates the instructions out loud.
_OUTPUT_RULE = (
    "OUTPUT RULE: Speak ONLY the final user-facing answer. "
    "Never narrate instructions, never say 'we need to respond', "
    "never mention policy/system/prompt/language lock. "
    "No English meta-commentary.\n"
)

REPLY_LANG_HI = (
    "\n\nLANGUAGE NOW: User spoke Hindi/Hinglish. Reply in Hindi only. "
    "Do not use full English. Match this turn, not older English turns.\n"
    + _OUTPUT_RULE
    + "SAFETY: Never ask for OTP, PIN, or account number. "
    "Never promise scheme approval.\n"
)

REPLY_LANG_EN = (
    "\n\nLANGUAGE NOW: User spoke English. Reply in English ONLY. "
    "Use zero Hindi words and zero Devanagari script. "
    "Do not greet in Hindi. Match English this turn even if history was Hindi.\n"
    + _OUTPUT_RULE
    + "SAFETY: Never ask for OTP, PIN, or account number. "
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
    "i'm",
    "i am",
}

# Marker used only inside chat context; stripped if re-seen so locks never stack.
_LANG_LOCK_PREFIX = "[[LANG_LOCK]]"
_HIDDEN_LANG_PREFIX = "[[HIDDEN_LANG_LOCK]]"
_MEMORY_PREFIX = "[[CALLER_MEMORY]]"


def detect_reply_language(transcript: str, stt_language: str | None = None) -> str:
    """Return 'hi' or 'en' from user transcript + optional STT language tag.

    Ignores non-Latin STT garbage (CJK etc.) so English speech is not forced to Hindi.
    """
    text = (transcript or "").strip()
    stt = (stt_language or "").lower().replace("_", "-")
    if not text:
        if stt.startswith("en"):
            return "en"
        return "hi"

    # Devanagari script -> Hindi (strongest signal)
    if DEVANAGARI_RE.search(text):
        return "hi"

    text_lower = text.lower()
    # Hindi short affirmations / particles (must not fall through as English)
    _hi_short = {
        "haan",
        "han",
        "ji",
        "nahi",
        "nahin",
        "theek",
        "thik",
        "accha",
        "achha",
    }
    text_norm = re.sub(r"[^\w\s]", "", text_lower).strip()
    if text_norm in _hi_short or text_norm in {
        "namaste",
        "namaskar",
        "dhanyavad",
        "shukriya",
    }:
        return "hi"

    # English short greets / yes-no
    _en_short = {"hi", "hello", "hey", "yes", "no", "ok", "okay", "thanks", "thank you"}
    if text_norm in _en_short:
        return "en"

    # Only Latin tokens count — drop Japanese/Korean STT hallucinations.
    latin_words = re.findall(r"[a-zA-Z']+", text_lower)
    if not latin_words:
        if stt.startswith("en"):
            return "en"
        return "hi"

    hindi_hits = sum(1 for w in latin_words if w in HINDI_KEYWORDS)
    en_hits = sum(1 for w in latin_words if w in _ENGLISH_MARKERS)

    logger.debug(
        "Lang detect: text=%r, latin_words=%d, hindi_hits=%d, en_hits=%d, stt=%s",
        text[:100],
        len(latin_words),
        hindi_hits,
        en_hits,
        stt_language,
    )

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

    # Trust STT language tag when transcript is ambiguous
    if stt.startswith("en"):
        return "en"
    if stt.startswith("hi"):
        return "hi"

    # Short English self-intro / yes-no (not Hindi particles — handled above)
    if any(w in text_lower for w in ["i'm", "i am", "yes", "no"]):
        return "en"

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
            if text.startswith(_LANG_LOCK_PREFIX) or text.startswith(
                _HIDDEN_LANG_PREFIX
            ):
                continue
        keep.append(item)
    if len(keep) != len(items):
        items[:] = keep


# Extract a person name from common English/Hindi intro phrases.
# STT is usually lowercase — do NOT require an uppercase first letter.
_NAME_TOKEN = r"([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s'.-]{0,39})"
_NAME_PATTERNS = [
    re.compile(
        rf"(?:my name is|my name's|i am|i'm|this is|call me)\s+{_NAME_TOKEN}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?:mera naam|meri naam|mera name|main|mai)\s+{_NAME_TOKEN}"
        rf"(?:\s+hoon|\s+hun|\s+hu|\s+hai)?",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?:naam hai|naam hain|naam)\s+{_NAME_TOKEN}",
        re.IGNORECASE,
    ),
    # "Save it under Raj" / "remember me as Priya"
    re.compile(
        rf"(?:save (?:it |this )?(?:under|as|for)|remember (?:me )?as)\s+{_NAME_TOKEN}",
        re.IGNORECASE,
    ),
]

_NAME_STOPWORDS = {
    # Existing stopwords
    "jan",
    "sahay",
    "hello",
    "hi",
    "hey",
    "namaste",
    "namaskar",
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
    "i",
    "am",
    "i'm",
    "eligible",
    "32",
    "thirty",
    "two",
    "conversation",
    "details",
    "chat",
    "info",
    "data",
    "record",
    "account",
    "bank",
    "scheme",
    "yojana",
    "anything",
    "something",
    "everything",
    "me",
    "us",
    "this",
    "that",
    "it",
    "my",
    "your",
    "our",
    "who",
    "what",
    "where",
    "when",
    "why",
    "how",
    "tell",
    "save",
    "store",
    "remember",
    "keep",
    "know",
    "explain",
    "describe",
    "list",
    "give",
    "show",
    # Additional pronouns, determiners, prepositions, articles, conjunctions
    "you",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "some",
    "any",
    "many",
    "much",
    "all",
    "both",
    "each",
    "every",
    "other",
    "another",
    "such",
    "whose",
    "which",
    "whom",
    "whoever",
    "whatever",
    "whichever",
    "about",
    "above",
    "across",
    "after",
    "against",
    "along",
    "around",
    "at",
    "before",
    "behind",
    "below",
    "beneath",
    "beside",
    "between",
    "beyond",
    "but",
    "by",
    "during",
    "except",
    "for",
    "from",
    "in",
    "inside",
    "into",
    "like",
    "near",
    "of",
    "off",
    "on",
    "onto",
    "out",
    "outside",
    "over",
    "past",
    "since",
    "through",
    "throughout",
    "till",
    "to",
    "toward",
    "under",
    "until",
    "up",
    "upon",
    "with",
    "within",
    "without",
    "and",
    "or",
    "so",
    "than",
    "as",
    # Common helper/auxiliary/common verbs
    "do",
    "does",
    "did",
    "done",
    "doing",
    "have",
    "has",
    "had",
    "having",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "can",
    "could",
    "will",
    "would",
    "shall",
    "should",
    "may",
    "might",
    "must",
    "want",
    "wants",
    "wanted",
    "wanting",
    "need",
    "needs",
    "needed",
    "needing",
    "knows",
    "knew",
    "known",
    "thinking",
    "thought",
    "thinks",
    "remembers",
    "remembered",
    "say",
    "says",
    "said",
    "saying",
    "tells",
    "told",
    "asking",
    "asked",
    "asks",
    "find",
    "finds",
    "found",
    "get",
    "gets",
    "got",
    "make",
    "makes",
    "made",
    "go",
    "goes",
    "went",
    "going",
    "gone",
    # Domain specific terms (case, ticket, progress, chance, etc.)
    "case",
    "cases",
    "ticket",
    "tickets",
    "progress",
    "status",
    "update",
    "updates",
    "reference",
    "chance",
    "chances",
    "change",
    "changes",
    "opportunity",
    "issue",
    "issues",
    "problem",
    "problems",
    # Hindi/Hinglish question / pronoun / helper particles
    "kya",
    "kyu",
    "kyun",
    "kaise",
    "kab",
    "kahan",
    "kon",
    "kaun",
    "mera",
    "meri",
    "mere",
    "naam",
    "nam",
    "apna",
    "apni",
    "apne",
    "aap",
    "aapka",
    "aapki",
    "aapke",
    "tum",
    "tumhara",
    "tu",
    "tera",
    "hoon",
    "hun",
    "hu",
    "hai",
    "hain",
    "ho",
    "tha",
    "thi",
    "ko",
    "se",
    "ka",
    "ki",
    "ke",
    "ne",
    "par",
    "pe",
    "mein",
    "main",
    "han",
    "haan",
    "ji",
    "nahi",
    "nahin",
    "mat",
    "karo",
    "kariye",
    "batao",
    "bataiye",
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
        # Drop leading articles ("I am a Raj" → ["Raj"])
        while parts and parts[0].lower() in {"a", "an", "the"}:
            parts.pop(0)
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


def _extract_bare_name(text: str) -> str | None:
    """Extract a bare name when explicitly awaiting one (no 'my name is' prefix needed)."""
    raw = re.sub(r"[.,!?:;\"']+", "", (text or "").strip()).strip()
    if not raw or len(raw) < 2:
        return None
    parts = [p for p in re.split(r"\s+", raw) if p and len(p) >= 2]
    _bare_stops = _NAME_STOPWORDS | {
        "is",
        "its",
        "name",
        "mera",
        "naam",
        "hai",
        "hoon",
        "hun",
        "hu",
        "and",
        "or",
        "but",
        "so",
        "just",
        "only",
        "please",
        "can",
        "could",
        "you",
        "sure",
        "thank",
        "thanks",
        "im",
    }
    candidates = [p for p in parts if p.lower() not in _bare_stops]
    if not candidates:
        return None
    name_parts = candidates[:2]
    name = " ".join(name_parts).strip()
    if 2 <= len(name) <= 40:
        return name.title() if name.isascii() else name
    return None


def _welcome_back_line(caller: dict, lang: str = "en") -> str:
    """Exact spoken welcome for a returning caller (only real topic + open ticket)."""
    name = caller.get("name") or caller.get("user_id") or "there"
    facts = caller.get("facts") or {}
    last_topic = (facts.get("last_topic") or "").strip()
    ref = (facts.get("last_escalation_ref") or "").strip()
    status = (facts.get("last_escalation_status") or "").strip().lower()
    open_ticket = bool(ref) and status in {"", "open", "in_progress"}

    if (lang or "en").lower().startswith("hi"):
        line = f"Namaste {name}! "
        if last_topic and last_topic not in {
            "government schemes",
            "government scheme",
            "schemes",
        }:
            line += f"Pichhli baar humne {last_topic} ke baare mein baat ki thi. "
        line += (
            f"Aapka open ticket {ref} abhi bhi review mein hai." if open_ticket else ""
        )
        line += " Aaj main aapki kya madad karoon?"
        return line

    line = f"Hello {name}! "
    if last_topic and last_topic not in {
        "government schemes",
        "government scheme",
        "schemes",
    }:
        line += f"We discussed about {last_topic}. "
    if open_ticket:
        line += f"Your open case reference {ref} is still with our specialist team. "
    line += "How can I help you today?"
    return line


def _format_memory_note(caller: dict) -> str:
    """System note for a returning caller on a NEW call session."""
    name = caller.get("name") or caller.get("user_id") or "caller"
    facts = caller.get("facts") or {}
    last_topic = facts.get("last_topic") or ""
    ref = facts.get("last_escalation_ref") or ""
    
    msg = f"{_MEMORY_PREFIX} RETURNING_CALLER (new call only): name={name}; "
    if last_topic:
        msg += f"last_topic={last_topic}; You MUST welcome them back and mention that last time you talked about {last_topic}. "
    else:
        msg += "No last topic found; Greet them simply: 'Welcome back [Name]! How can I help you today?'. "
        
    if ref:
        msg += f"last_escalation_ref={ref}; You MUST mention their open case reference {ref} is under review. "
        
    msg += "Do NOT say you just saved anything."
    return msg


def _wants_recall(text: str) -> bool:
    """True if user is asking whether we remember them / past chat."""
    t = (text or "").lower()
    keys = (
        "do you remember",
        "you remember",
        "remember me",
        "yaad hai",
        "yaad ho",
        "pehchante",
        "pehchaan",
        "remember our",
        "last time",
        "pichhli baar",
        "previous conversation",
        "do you recall",
        "you recall",
    )
    return any(k in t for k in keys)


def _format_passive_memory(caller: dict) -> str:
    """Passive context note for turns after initial greeting."""
    name = caller.get("name") or caller.get("user_id") or "caller"
    facts = caller.get("facts") or {}
    facts_bits = []
    for key, value in list(facts.items())[:4]:
        facts_bits.append(f"{key}={value}")
    facts_txt = "; ".join(facts_bits) if facts_bits else "none"
    return (
        f"{_MEMORY_PREFIX} CALLER_CONTEXT: name={name}; facts=[{facts_txt}]. "
        f"Do NOT say welcome back again. Answer the current user question directly."
    )


def _save_confirm_line(name: str, lang: str) -> str:
    """Spoken confirmation after save — exact requested string."""
    clean = (name or "there").strip() or "there"
    if (lang or "hi").lower().startswith("hi"):
        return f"Dhanyavad {clean}! Maine aapki baatcheet save kar li hai."
    return f"Thank you {clean}! I have saved the conversation."


def _format_just_saved_note(name: str, lang: str) -> str:
    line = _save_confirm_line(name, lang)
    return (
        f"{_MEMORY_PREFIX} JUST_SAVED: Saved under {name}. "
        f'Speak ONLY this confirmation once: "{line}" '
        f"Do NOT say welcome back. Do NOT mention past topics. Wait for next user question."
    )


def _wants_save(text: str) -> bool:
    """True if user asked to save/remember the conversation.

    'do you remember me?' and 'remember me?' are recall requests, NOT save.
    """
    t = (text or "").lower()
    # Explicit save keywords (never ambiguous)
    save_keys = (
        "save",
        "store",
        "yaad rakh",
        "yaad rakho",
        "save karo",
        "save kar",
        "yaad rakhna",
        "बातचीत सेव",
        "सेव कर",
        "याद रख",
    )
    if any(k in t for k in save_keys):
        return True
    # "remember" is ambiguous — only treat as save if NOT a recall phrase
    if "remember" in t:
        recall = (
            "do you remember",
            "you remember",
            "can you remember",
            "remember me",
            "remember our",
            "remember my",
            "remember past",
            "remember previous",
            "remember the conversation",
            "remember our conversation",
        )
        # "remember this", "remember my conversation" → save; recall phrases → not save
        return not any(r in t for r in recall)
    return False


def extract_ticket_ref(text: str) -> str | None:
    match = re.search(r"\bJS-[0-9A-Z]{8}\b", (text or "").upper())
    if match:
        return match.group(0)
    return None


def _wants_case_recall(text: str) -> bool:
    """True if user is asking about progress, status, or recall of their ticket/case."""
    t = (text or "").lower()
    keys = (
        "progress on my case",
        "progress of my case",
        "progress on my ticket",
        "status of my case",
        "status of my ticket",
        "update on my case",
        "update on my ticket",
        "remember my case",
        "remember my ticket",
        "remember the case",
        "remember the ticket",
        "what happened to my case",
        "what happened to my ticket",
        "what is my ticket status",
        "my case status",
        "case status",
        "ticket status",
        "apne case",
        "mera case",
        "mere case",
        "mera ticket",
        "mere ticket",
        "case ka kya hua",
        "ticket ka kya hua",
        "case ki progress",
        "ticket ki progress",
        "case yaad hai",
        "ticket yaad hai",
    )
    # Also check if it contains a ticket ID pattern
    if re.search(r"\bjs-[0-9a-z]{8}\b", t):
        return True
    return any(k in t for k in keys)


def _format_ticket_status_response(
    ticket: dict, lang: str, name: str | None = None
) -> str:
    ref = ticket.get("reference_id")
    status = (ticket.get("status") or "open").lower()
    notes = ticket.get("resolution_notes") or ""
    urgency = ticket.get("urgency") or "medium"

    sla = {
        "emergency": "within a few hours",
        "high": "within one business day",
        "medium": "within one to two business days",
        "low": "within two to three business days",
    }.get(urgency, "within one to two business days")

    name_part = f" {name}" if name else ""

    if (lang or "hi").lower().startswith("hi"):
        status_hi = {
            "open": "open (review mein)",
            "in_progress": "in progress (work chal raha hai)",
            "resolved": "resolved (suljha liya gaya hai)",
        }.get(status, "open")

        if status == "resolved":
            res = f"Namaste{name_part}! Aapka case {ref} resolve ho chuka hai. "
            if notes:
                res += f"Specialist ke notes hain: {notes}."
            else:
                res += "Specialist team ne isse close kar diya hai."
            return res

        res = f"Namaste{name_part}! Aapka case {ref} abhi {status_hi} hai. "
        res += f"Humare specialist ise {sla} mein review karenge."
        return res

    # English
    if status == "resolved":
        res = f"Hello{name_part}! Your case {ref} has been resolved. "
        if notes:
            res += f"The specialist notes say: {notes}"
        else:
            res += "The specialist team has marked it as completed."
        return res

    res = f"Hello{name_part}! Your case {ref} is currently {status}. "
    res += f"A specialist is scheduled to review it {sla}."
    return res


_CONSENT_YES = {
    "yes",
    "yeah",
    "yep",
    "yup",
    "ok",
    "okay",
    "sure",
    "please",
    "go ahead",
    "proceed",
    "permission",
    "haan",
    "haa",
    "han",
    "ji",
    "haaji",
    "bilkul",
    "zaroor",
    "jaroor",
    "theek",
    "thik",
    "sahi",
    "karo",
    "kariye",
    "haanji",
    "ha ji",
    "हां",
    "हाँ",
    "जी",
    "ठीक",
    "बिल्कुल",
}

_CONSENT_NO = {
    "no",
    "nope",
    "nah",
    "naah",
    "nahi",
    "nahin",
    "mat",
    "cancel",
    "stop",
    "don't",
    "dont",
    "do not",
    "refuse",
    "denied",
    "ruko",
    "band",
    "chhodo",
    "mat bhejo",
    "मत",
    "नहीं",
    "ना",
}


def _is_consent_yes(text: str) -> bool:
    t = re.sub(r"[^\w\s]", "", (text or "").lower()).strip()
    if not t:
        return False
    if any(n in t for n in ("no ", "not ", "don't", "dont", "nahi", "mat ")):
        # "no problem" / "not sure" edge — still treat explicit no words carefully
        if any(
            p in t
            for p in (
                "no",
                "nope",
                "nahi",
                "nahin",
                "don't",
                "dont",
                "do not",
                "mat",
                "cancel",
                "refuse",
            )
        ) and not any(p in t for p in ("no problem", "no worries", "not a problem")):
            # If both yes and strong no, prefer no handled elsewhere
            if t in _CONSENT_YES or t.startswith("yes") or t.startswith("haan"):
                return True
            return False
    if t in _CONSENT_YES:
        return True
    words = set(re.findall(r"[a-zA-Z\u0900-\u097F']+", t))
    return bool(words & _CONSENT_YES) and not bool(words & _CONSENT_NO)


def _is_consent_no(text: str) -> bool:
    t = re.sub(r"[^\w\s]", "", (text or "").lower()).strip()
    if not t:
        return False
    if any(
        p in t
        for p in (
            "don't share",
            "dont share",
            "do not share",
            "don't proceed",
            "dont proceed",
            "no permission",
            "mat bhejo",
            "mat karo",
            "nahi bhejo",
            "no thanks",
            "no thank",
        )
    ):
        return True
    if t in _CONSENT_NO:
        return True
    words = set(re.findall(r"[a-zA-Z\u0900-\u097F']+", t))
    # Pure refusal words without yes
    if words & _CONSENT_NO and not (words & _CONSENT_YES):
        return True
    return False


def _prepare_pending_escalation(
    text: str, reply_lang: str, known_name: str | None
) -> dict:
    """Build a pending escalation draft from the user utterance."""
    trigger = escalation.detect_escalation_trigger(text) or "user_requested"
    urgency = escalation.suggest_urgency(trigger, text)
    name = known_name or "Caller"
    return {
        "issue_description": escalation.scrub_pii(text),
        "trigger_type": trigger,
        "urgency": urgency,
        "requester_name": name,
        "preferred_language": reply_lang,
        "follow_up_method": "voice_callback",
        "diagnostic_steps": [
            "Caller reported an issue requiring human review.",
            f"Detected trigger: {trigger}.",
            "Awaiting explicit consent before dispatch.",
        ],
    }


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
        self._last_user_topic = "government schemes"
        # Session flags — stop welcome-back spam after a same-call save
        self._saved_this_session = False
        self._welcomed_this_session = False
        self._awaiting_name_for_save = False
        # Day 7 escalation consent gate
        self._awaiting_escalation_consent = False
        self._pending_escalation: dict | None = None
        self._last_escalation_ref: str | None = None
        self._awaiting_name_or_ref_for_recall = False
        self._call_room_id: str | None = None
        self._last_user_final_at: float | None = None

    @function_tool
    async def lookup_caller(self, ctx: RunContext, name_or_id: str) -> str:
        """Lookup stored caller on a NEW call when they give their name or ask if you remember them.
        Do NOT call this right after save_caller_memory in the same call.
        """
        clean = (name_or_id or "").strip()
        if not clean:
            return json.dumps({"found": False, "message": "Name is required."})
        clean_title = clean.title() if clean.isascii() else clean

        # Same session after a save: never "welcome back"
        if (
            self._saved_this_session
            and self._known_caller_name
            and (
                clean.lower() == self._known_caller_name.lower()
                or clean_title.lower() == self._known_caller_name.lower()
            )
        ):
            return json.dumps(
                {
                    "found": True,
                    "already_in_session": True,
                    "instruction": (
                        "You already saved them this call. "
                        "Do NOT welcome back. Just continue helping briefly."
                    ),
                }
            )

        caller = db.get_caller(clean) or (
            db.get_caller(clean_title) if clean.isascii() else None
        )
        if not caller:
            return json.dumps(
                {
                    "found": False,
                    "message": f"No record found for '{clean}'.",
                    "instruction": (
                        f"Say you do not have a saved record for {clean_title} yet. "
                        "Offer to save if they want. Keep under 15 words."
                    ),
                }
            )

        self._known_caller_name = caller.get("name") or clean_title
        self._memory_loaded = True
        name = self._known_caller_name
        payload = dict(caller)
        payload["found"] = True

        if self._welcomed_this_session or self._saved_this_session:
            payload["instruction"] = (
                f"Name {name} already handled this call. "
                "Do NOT welcome back again. Answer their question briefly."
            )
        else:
            self._welcomed_this_session = True
            last_topic = (caller.get("facts") or {}).get("last_topic", "")
            if last_topic:
                payload["instruction"] = (
                    f"RETURNING caller {name} on a NEW call. "
                    f"Say EXACTLY: 'Welcome back {name}! I remember we were talking about {last_topic}. How can I help you today?' "
                    f"Keep under 25 words. Do NOT ask to save."
                )
            else:
                payload["instruction"] = (
                    f"RETURNING caller {name} on a NEW call. "
                    f"Say: 'Welcome back {name}! How can I help you today?' "
                    f"Keep under 15 words."
                )
        return json.dumps(payload)

    @function_tool
    async def save_caller_memory(
        self,
        ctx: RunContext,
        name: str,
        facts: str | None = None,
        language_preference: str | None = None,
    ) -> str:
        """Save caller profile and conversation facts keyed by name.

        Call IMMEDIATELY when the user gives their name to save (e.g. 'My name is Raj',
        'Mera naam Priya hai', or after they said 'save this' and then gave a name).
        After this tool returns, you MUST speak the speak_out_loud line to the user
        (e.g. "Thanks, I've saved the conversation, Raj.").
        STRICT PRIVACY RULE: Do NOT store account numbers, Aadhaar, PAN, PIN, or OTP.
        """
        clean_name = (name or "").strip()
        if not clean_name:
            return json.dumps({"saved": False, "message": "Name is required."})
        # Title-case Latin names so "raj" -> "Raj"
        if clean_name.isascii():
            clean_name = clean_name.title()
        user_id = clean_name.lower().replace(" ", "_")
        lang = language_preference or self._reply_lang

        facts_dict = {
            "saved_conversation": True,
            "last_topic": self._last_user_topic,
        }
        if facts:
            if isinstance(facts, dict):
                facts_dict.update(facts)
            elif isinstance(facts, str):
                try:
                    parsed = json.loads(facts)
                    if isinstance(parsed, dict):
                        facts_dict.update(parsed)
                    else:
                        facts_dict["notes"] = facts
                except json.JSONDecodeError:
                    facts_dict["notes"] = facts

        res = db.save_caller(
            user_id=user_id,
            name=clean_name,
            language_preference=lang,
            facts=facts_dict,
            consent_given=True,
        )
        self._known_caller_name = clean_name
        self._memory_loaded = True
        speak = _save_confirm_line(clean_name, lang or "hi")
        res["saved"] = bool(res.get("saved", res.get("status") == "success"))
        res["speak_out_loud"] = speak
        res["instruction"] = (
            f"Speak this confirmation out loud now, then continue: {speak}"
        )
        logger.info("save_caller_memory saved profile for %s: %s", clean_name, res)
        # Speak confirmation immediately so the user always hears it.
        try:
            await ctx.session.say(speak, allow_interruptions=True)
        except Exception as err:
            logger.warning("Could not speak save confirmation: %s", err)
        return json.dumps(res)

    @function_tool
    async def check_scheme_eligibility(
        self,
        ctx: RunContext,
        scheme_name: str,
        age: int | None = None,
        has_bank_account: bool | None = None,
        is_indian_resident: bool | None = None,
        monthly_income_inr: int | None = None,
        already_has_scheme: bool | None = None,
    ) -> str:
        """Check if a caller is likely eligible for an Indian financial scheme
        (PMJDY, PMSBY, PMJJBY, or APY) using answers already collected in this call.

        WHEN TO CALL:
        - User asks "Am I eligible for …?", "Can I apply for …?", "Mera PMSBY
          ke liye paatrata check karo", or similar.
        - You already have (or the user just gave) age and other needed facts.
        - After you collected missing fields from a previous need_more_info result.

        WHEN NOT TO CALL:
        - User only wants a general scheme explanation (use get_scheme_info instead).
        - User only wants the document list (use get_document_checklist instead).
        - You still have zero facts — first ask age (and bank-account status if
          the scheme needs one), then call this tool.

        FAILURE PATH (speak out loud, never invent eligibility):
        - If the tool returns ok=false or status=need_more_info, read the
          message / speak_summary to the user and ask only the missing fields.
        - Never promise bank or government approval. Always say the data vintage
          from data_as_of (e.g. "figures as of April 2025 local dataset").
        """
        try:
            result = schemes.check_eligibility(
                scheme_name=scheme_name,
                age=age,
                has_bank_account=has_bank_account,
                is_indian_resident=is_indian_resident,
                monthly_income_inr=monthly_income_inr,
                already_has_scheme=already_has_scheme,
            )
            if self._call_room_id:
                db.record_eligibility_result(self._call_room_id, result)
            # Persist a light non-sensitive breadcrumb if we know the caller.
            if self._known_caller_name and result.get("ok"):
                try:
                    db.save_caller(
                        user_id=self._known_caller_name.lower().replace(" ", "_"),
                        name=self._known_caller_name,
                        language_preference=self._reply_lang,
                        facts={
                            "last_eligibility_scheme": result.get(
                                "scheme_short_name", scheme_name
                            ),
                            "last_eligibility_status": result.get("status"),
                        },
                        consent_given=True,
                    )
                except Exception as err:
                    logger.warning("Could not save eligibility breadcrumb: %s", err)
            return json.dumps(result)
        except Exception as err:
            logger.exception("check_scheme_eligibility failed: %s", err)
            if self._call_room_id:
                db.record_tool_error(self._call_room_id)
            return json.dumps(
                {
                    "ok": False,
                    "error": "tool_failure",
                    "message": (
                        "The eligibility checker is temporarily unavailable. "
                        "Apologise out loud, do NOT invent eligibility, and suggest "
                        "the caller confirm at their bank branch, CSC, or the "
                        "official scheme portal. You may still explain general "
                        "scheme basics from your knowledge."
                    ),
                    "data_as_of": schemes.DATA_AS_OF,
                    "data_source": schemes.DATA_SOURCE,
                }
            )

    @function_tool
    async def get_document_checklist(
        self,
        ctx: RunContext,
        scheme_name: str,
    ) -> str:
        """Return the document checklist a caller should carry when applying for
        PMJDY, PMSBY, PMJJBY, or APY.

        WHEN TO CALL:
        - User asks "What documents do I need for …?", "Kaun se documents lagenge?",
          "Checklist for Jan Dhan", or similar application-prep questions.
        - After an eligibility check succeeds and the user wants next steps.

        WHEN NOT TO CALL:
        - User is only asking about eligibility (use check_scheme_eligibility).
        - User wants premium / cover numbers (use get_scheme_info).

        FAILURE PATH (speak out loud):
        - If ok=false, tell the user which schemes you support and ask them to
          restate the scheme name. Never invent a document list.
        - Always mention data_as_of so the listener knows the list vintage.
          Banks may still ask for extra KYC — say that too.
        """
        try:
            result = schemes.get_document_checklist(scheme_name)
            if self._call_room_id:
                db.record_document_list_result(self._call_room_id, result)
            return json.dumps(result)
        except Exception as err:
            logger.exception("get_document_checklist failed: %s", err)
            if self._call_room_id:
                db.record_tool_error(self._call_room_id)
            return json.dumps(
                {
                    "ok": False,
                    "error": "tool_failure",
                    "message": (
                        "The document checklist is temporarily unavailable. "
                        "Apologise out loud, do NOT invent documents, and guide "
                        "the caller to confirm the list at their bank branch or CSC."
                    ),
                    "data_as_of": schemes.DATA_AS_OF,
                    "data_source": schemes.DATA_SOURCE,
                }
            )

    @function_tool
    async def get_scheme_info(
        self,
        ctx: RunContext,
        scheme_name: str,
    ) -> str:
        """Fetch structured facts (summary, age band, premium, benefits) for
        PMJDY, PMSBY, PMJJBY, or APY from the local scheme dataset.

        WHEN TO CALL:
        - User asks "Tell me about PMSBY", "APY kya hai?", premium/cover amounts,
          or wants a quick scheme overview with dated figures.

        WHEN NOT TO CALL:
        - User already gave personal details and wants a personal eligibility
          decision (use check_scheme_eligibility).
        - User wants only the document list (use get_document_checklist).

        Always speak the data_as_of vintage. On failure, apologise and do not invent numbers.
        """
        try:
            result = schemes.get_scheme_overview(scheme_name)
            return json.dumps(result)
        except Exception as err:
            logger.exception("get_scheme_info failed: %s", err)
            return json.dumps(
                {
                    "ok": False,
                    "error": "tool_failure",
                    "message": (
                        "Scheme info lookup failed. Apologise out loud, do NOT invent "
                        "premiums or cover amounts, and suggest the official portal "
                        "or bank branch for current figures."
                    ),
                    "data_as_of": schemes.DATA_AS_OF,
                    "data_source": schemes.DATA_SOURCE,
                }
            )

    @function_tool
    async def create_escalation(
        self,
        ctx: RunContext,
        issue_description: str,
        user_consent: bool,
        trigger_type: str = "other",
        urgency: str = "medium",
        requester_name: str | None = None,
        diagnostic_steps: str | None = None,
        preferred_language: str | None = None,
        follow_up_method: str | None = "voice_callback",
        contact_hint: str | None = None,
    ) -> str:
        """Create a human-specialist escalation ticket (Day 7).

        WHEN TO CALL (only after the caller explicitly consents):
        - Trigger A: suspected fraud / unauthorized account access.
        - Trigger B: complex disputes, limit overrides, or decisions beyond
          agent authority (claims stuck, supervisor request, etc.).

        CONSENT GATE (HARD RULE):
        - First ask permission using the standard consent script.
        - Call this tool with user_consent=true ONLY if the caller said yes.
        - If the caller said no, do NOT call this tool (or pass user_consent=false).
          Offer bank branch / CSC / official portal / helpline instead.

        PII RULE:
        - Never put passwords, OTPs, PINs, full account numbers, CVVs, Aadhaar,
          or PAN into any argument. The backend scrubs free text, but do not
          collect those secrets at all.

        AFTER SUCCESS:
        - Speak speak_out_loud_en or speak_out_loud_hi (match session language).
        - Always read the reference_id and realistic next steps.
        - Do NOT promise immediate live-agent pickup.
        """
        name = (requester_name or self._known_caller_name or "Caller").strip()
        user_id = name.lower().replace(" ", "_")
        lang = preferred_language or self._reply_lang or "hi"

        steps: list[str] | str | None = diagnostic_steps
        if not steps:
            steps = [
                "Agent detected escalation trigger from conversation.",
                f"Last topic discussed: {self._last_user_topic}.",
                "Agent requested explicit consent before sharing summary.",
            ]

        try:
            result = escalation.create_escalation(
                user_id=user_id,
                issue_description=issue_description,
                user_consent=bool(user_consent),
                trigger_type=trigger_type,
                requester_name=name,
                diagnostic_steps=steps,
                urgency=urgency,
                preferred_language=lang,
                follow_up_method=follow_up_method or "voice_callback",
                contact_hint=contact_hint,
            )
        except Exception as err:
            logger.exception("create_escalation failed: %s", err)
            return json.dumps(
                {
                    "ok": False,
                    "error": "tool_failure",
                    "message": (
                        "Escalation system temporarily unavailable. Apologise, "
                        "do not invent a reference ID, and offer bank helpline / "
                        "branch / CSC as alternatives."
                    ),
                }
            )

        self._awaiting_escalation_consent = False
        self._pending_escalation = None
        if result.get("ok") and result.get("reference_id"):
            if self._call_room_id:
                db.record_escalation(self._call_room_id)
            self._last_escalation_ref = result["reference_id"]
            topic = (
                "fraud / unauthorized access"
                if trigger_type == "fraud_suspected"
                else "complex transaction / human review"
            )
            self._last_user_topic = topic
            if name and name.lower() != "caller":
                self._persist_caller_breadcrumb(
                    name,
                    extra_facts={
                        "last_escalation_ref": result["reference_id"],
                        "last_escalation_status": result.get("status") or "open",
                        "last_escalation_trigger": trigger_type,
                        "last_topic": topic,
                    },
                    lang=lang,
                )

            speak = (
                result.get("speak_out_loud_en")
                if (lang or "").startswith("en")
                else result.get("speak_out_loud_hi")
            )
            if speak:
                try:
                    await ctx.session.say(speak, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak escalation confirm: %s", err)

        elif result.get("status") == "consent_denied":
            speak = (
                result.get("speak_out_loud_en")
                if (lang or "").startswith("en")
                else result.get("speak_out_loud_hi")
            )
            if speak:
                try:
                    await ctx.session.say(speak, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak consent-denied path: %s", err)

        return json.dumps(result)

    def _persist_caller_breadcrumb(
        self,
        name: str | None = None,
        *,
        extra_facts: dict | None = None,
        lang: str | None = None,
    ) -> None:
        """Write last_topic ONLY if it's a real discussed topic (never invent 'government schemes')."""
        clean = (name or self._known_caller_name or "").strip()
        if not clean or clean.lower() == "caller":
            return
        if clean.isascii():
            clean = clean.title()
        user_id = clean.lower().replace(" ", "_")
        facts: dict = {"saved_conversation": True}
        real_topic = self._last_user_topic or ""
        if real_topic and real_topic not in {
            "government schemes",
            "government scheme",
            "schemes",
        }:
            facts["last_topic"] = real_topic
        if self._last_escalation_ref:
            facts["last_escalation_ref"] = self._last_escalation_ref
            facts["last_escalation_status"] = "open"
        if extra_facts:
            facts.update(extra_facts)
        try:
            db.save_caller(
                user_id=user_id,
                name=clean,
                language_preference=lang or self._reply_lang,
                facts=facts,
                consent_given=True,
            )
            self._known_caller_name = clean
            self._memory_loaded = True
            
            # Link any in-session escalation ticket to the caller's real identity
            if self._last_escalation_ref:
                try:
                    from datetime import datetime, timezone
                    with db.get_db_connection() as conn:
                        conn.execute(
                            """
                            UPDATE escalations SET
                                user_id = ?,
                                requester_name = ?,
                                updated_at = ?
                            WHERE reference_id = ?
                            """,
                            (user_id, clean, datetime.now(timezone.utc).isoformat(), self._last_escalation_ref)
                        )
                        conn.commit()
                    logger.info("Updated escalation ticket %s with requester name: %s", self._last_escalation_ref, clean)
                except Exception as escalation_err:
                    logger.warning("Could not link escalation ticket to requester name: %s", escalation_err)
        except Exception as err:
            logger.warning("Could not persist caller breadcrumb for %s: %s", clean, err)

    def _lookup_returning_caller(self, text: str) -> dict | None:
        """Find stored profile from an intro / recall utterance."""
        name = extract_caller_name(text) or _extract_bare_name(text)
        if not name:
            return None
        caller = db.get_caller(name)
        if caller:
            return caller
        # Title-case Latin fallback (sam → Sam)
        if name.isascii():
            return db.get_caller(name.title()) or db.get_caller(name.lower())
        return None

    def _auto_memory_for_turn(self, turn_ctx: llm.ChatContext, text: str) -> None:
        """Auto-load returning caller memory for a NEW call session only.

        Prefer the hard welcome intercept in on_user_turn_completed; this is a
        fallback system note if the LLM path still runs.
        """
        if self._saved_this_session or self._welcomed_this_session:
            return

        text_lower = (text or "").lower()
        if any(
            w in text_lower
            for w in ["don't save", "dont save", "do not save", "no thanks", "naah"]
        ):
            return

        existing = self._lookup_returning_caller(text)
        if existing:
            self._known_caller_name = existing.get("name") or extract_caller_name(text)
            self._memory_loaded = True
            self._welcomed_this_session = True
            _strip_lang_locks(turn_ctx)
            turn_ctx.add_message(role="system", content=_format_memory_note(existing))
            logger.info(
                "Auto-loaded returning caller memory for %s", self._known_caller_name
            )

    def note_stt_language(self, language: str | None, transcript: str) -> None:
        if language:
            self._last_stt_language = str(language)

    async def apply_language(
        self,
        transcript: str,
        stt_language: str | None = None,
        turn_ctx: llm.ChatContext | None = None,
    ) -> str:
        """Detect reply language, update instructions + TTS for this turn.

        IMPORTANT: LiveKit passes a *copy* of chat_ctx into on_user_turn_completed.
        Agent.update_instructions() only patches the agent's main chat_ctx — NOT that
        copy — so the current turn would keep the old language unless we also patch
        turn_ctx here. That was the root cause of Hindi/English not switching.
        """
        lang_hint = stt_language or self._last_stt_language
        reply_lang = detect_reply_language(transcript, lang_hint)
        logger.info(
            "Language detect: lang=%s stt=%s text=%r",
            reply_lang,
            lang_hint,
            (transcript or "")[:120],
        )

        self._reply_lang = reply_lang
        directive = REPLY_LANG_HI if reply_lang == "hi" else REPLY_LANG_EN
        full_instructions = SYSTEM_PROMPT + directive

        # 1) Persist on the agent (affects subsequent turns / main chat_ctx)
        await self.update_instructions(full_instructions)

        # 2) Patch THIS turn's context copy so the LLM about to run sees the new language
        if turn_ctx is not None:
            try:
                patch_chat_instructions(
                    turn_ctx, instructions=full_instructions, add_if_missing=True
                )
                logger.info("Patched turn_ctx instructions for language=%s", reply_lang)
            except Exception as err:
                logger.warning("Could not patch turn_ctx instructions: %s", err)

        # 3) Switch Murf TTS voice/locale to match (only when agent is running)
        voice = VOICE_HI if reply_lang == "hi" else VOICE_EN
        locale = LOCALE_HI if reply_lang == "hi" else LOCALE_EN
        tts = None
        try:
            sess = self.session  # raises RuntimeError if agent not running
            tts = sess.tts if sess else None
        except RuntimeError:
            tts = None
        if tts is not None and hasattr(tts, "update_options"):
            try:
                tts.update_options(voice=voice, locale=locale, style=None)
                if voice != self._voice:
                    logger.info("Switched TTS voice=%s locale=%s", voice, locale)
                self._voice = voice
            except Exception as err:
                logger.warning("TTS voice update failed: %s", err)

        return reply_lang

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Lock language for this turn without polluting history or stacking locks."""
        was_welcomed_before_turn = self._welcomed_this_session
        text = new_message.text_content or ""
        text_clean = text.strip().lower()
        words = re.findall(r"[a-zA-Z\u0900-\u097F']+", text_clean)

        # Drop empty / filler / ultra-short STT hallucinations.
        # Allow short yes/no/haan/nahi etc. so "Yes." and "Hello?" are not ignored.
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
        # Normalize for punctuation so "yes.", "hello?", "haan." work
        text_norm = re.sub(r"[^\w\s]", "", text_clean).lower().strip()
        is_short_greet = text_norm in _ALLOWED_SHORT_GREETS or any(
            text_norm == g or text_norm.startswith(g + " ")
            for g in _ALLOWED_SHORT_GREETS
        )
        if not text_clean or text_clean in noise:
            logger.info("Ignoring noise/echo transcript: %r", text)
            raise StopResponse()
        is_awaiting_input = (
            self._awaiting_name_for_save
            or self._awaiting_name_or_ref_for_recall
            or self._awaiting_escalation_consent
        )
        has_extracted_data = (
            bool(_extract_bare_name(text))
            or bool(extract_ticket_ref(text_clean))
        )
        if (
            not is_short_greet
            and not is_awaiting_input
            and not _wants_save(text_norm)
            and not has_extracted_data
            and (len(words) < 2 or len(text_clean) < 6)
        ):
            logger.info("Ignoring ultra-short non-greet transcript: %r", text)
            raise StopResponse()

        # Pass turn_ctx so instructions are patched on the copy used for THIS reply.
        reply_lang = await self.apply_language(
            text, self._last_stt_language, turn_ctx=turn_ctx
        )

        # Auto-extract and set caller name if not already known
        if not self._known_caller_name or self._known_caller_name.lower() == "caller":
            introduced_name = extract_caller_name(text) or _extract_bare_name(text)
            if introduced_name and introduced_name.lower() not in {"caller", "unknown"}:
                self._known_caller_name = introduced_name
                logger.info("Auto-extracted and set caller name: %s", introduced_name)

        # ── ESCALATION CONSENT INTERCEPT (Day 7) ───────────────────
        # (Runs before recall so fraud/dispute utterances still escalate.)
        if self._awaiting_escalation_consent and self._pending_escalation:
            if _is_consent_no(text_clean):
                self._awaiting_escalation_consent = False
                self._pending_escalation = None
                refuse = escalation.refusal_self_service(reply_lang)
                logger.info("Escalation consent denied by user")
                try:
                    await self.session.say(refuse, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak escalation refusal: %s", err)
                raise StopResponse()

            if _is_consent_yes(text_clean):
                pending = dict(self._pending_escalation)
                self._awaiting_escalation_consent = False
                self._pending_escalation = None
                name = (
                    pending.get("requester_name") or self._known_caller_name or "Caller"
                )
                user_id = str(name).lower().replace(" ", "_")
                result = escalation.create_escalation(
                    user_id=user_id,
                    issue_description=pending.get("issue_description") or text,
                    user_consent=True,
                    trigger_type=pending.get("trigger_type") or "other",
                    requester_name=name,
                    diagnostic_steps=pending.get("diagnostic_steps"),
                    urgency=pending.get("urgency") or "medium",
                    preferred_language=reply_lang,
                    follow_up_method=pending.get("follow_up_method")
                    or "voice_callback",
                    contact_hint=pending.get("contact_hint"),
                )
                if result.get("ok") and result.get("reference_id"):
                    self._last_escalation_ref = result["reference_id"]
                    topic = (
                        "fraud / unauthorized access"
                        if (pending.get("trigger_type") == "fraud_suspected")
                        else "complex transaction / human review"
                    )
                    self._last_user_topic = topic
                    # Persist under real name when known; otherwise keep ref on agent
                    # until the caller introduces themselves later.
                    if name and str(name).lower() != "caller":
                        self._persist_caller_breadcrumb(
                            str(name),
                            extra_facts={
                                "last_escalation_ref": result["reference_id"],
                                "last_escalation_status": result.get("status")
                                or "open",
                                "last_escalation_trigger": pending.get("trigger_type"),
                                "last_topic": topic,
                            },
                            lang=reply_lang,
                        )
                    else:
                        logger.info(
                            "Escalation %s created without caller name — "
                            "will attach when name is known",
                            result["reference_id"],
                        )
                speak = (
                    result.get("speak_out_loud_en")
                    if reply_lang == "en"
                    else result.get("speak_out_loud_hi")
                ) or result.get("message", "Escalation processed.")
                # If we still don't know the caller, ask for a name so the ticket
                # attaches to their profile for next-call recall.
                if result.get("ok") and (
                    not self._known_caller_name
                    or str(self._known_caller_name).lower() == "caller"
                ):
                    speak += (
                        " Please tell me your name so I can attach this ticket to your profile."
                        if reply_lang == "en"
                        else " Kripya apna naam bataiye taaki main yeh ticket aapke profile se jod sakoon."
                    )
                    self._awaiting_name_for_save = True
                logger.info(
                    "Escalation after consent: ok=%s ref=%s",
                    result.get("ok"),
                    result.get("reference_id"),
                )
                try:
                    await self.session.say(speak, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak escalation result: %s", err)
                raise StopResponse()

            # Unclear answer — re-ask consent, do not dispatch
            reask = escalation.consent_prompt(reply_lang)
            try:
                await self.session.say(reask, allow_interruptions=True)
            except Exception as err:
                logger.warning("Could not re-ask escalation consent: %s", err)
            raise StopResponse()

        # Auto-detect mandatory escalation triggers and open consent gate.
        # Skip if already mid-save flow or pure greets.
        detected_trigger = escalation.detect_escalation_trigger(text)
        if detected_trigger and not self._awaiting_name_for_save:
            self._pending_escalation = _prepare_pending_escalation(
                text, reply_lang, self._known_caller_name
            )
            self._awaiting_escalation_consent = True
            self._last_user_topic = (
                "fraud / unauthorized access"
                if detected_trigger == "fraud_suspected"
                else "complex transaction / human review"
            )
            ack = (
                "I understand this needs a human specialist. "
                + escalation.CONSENT_PROMPT_EN
                if reply_lang == "en"
                else "Main samajh gayi, iske liye human specialist chahiye. "
                + escalation.CONSENT_PROMPT_HI
            )
            logger.info("Escalation trigger=%s — asking consent", detected_trigger)
            try:
                await self.session.say(ack, allow_interruptions=True)
            except Exception as err:
                logger.warning("Could not speak escalation consent prompt: %s", err)
            raise StopResponse()
        # ── END ESCALATION CONSENT INTERCEPT ───────────────────────

        # ── RETURNING CALLER RECALL INTERCEPT ──────────────────────
        # Bypass LLM so we always speak last_topic + open ticket ref.
        # Skipped when this turn already matched an escalation trigger above.
        if not self._welcomed_this_session and not self._awaiting_name_for_save:
            existing = self._lookup_returning_caller(text)
            name_from_text = extract_caller_name(text) or _extract_bare_name(text)
            wants_recall = _wants_recall(text_clean)
            # Intro with known profile, or explicit "do you remember?"
            if existing and (wants_recall or name_from_text):
                self._known_caller_name = existing.get("name") or name_from_text
                self._memory_loaded = True
                self._welcomed_this_session = True
                facts = existing.get("facts") or {}
                if facts.get("last_topic"):
                    self._last_user_topic = str(facts["last_topic"])
                if facts.get("last_escalation_ref"):
                    self._last_escalation_ref = str(facts["last_escalation_ref"])

                # Add memory note to context so it is persisted in chat history
                turn_ctx.add_message(
                    role="system", content=_format_memory_note(existing)
                )

                welcome = _welcome_back_line(existing, reply_lang)
                logger.info(
                    "Recall intercept: name=%s topic=%s ref=%s",
                    self._known_caller_name,
                    facts.get("last_topic"),
                    facts.get("last_escalation_ref"),
                )
                try:
                    await self.session.say(welcome, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak welcome-back: %s", err)
                raise StopResponse()
        # ── END RETURNING CALLER RECALL INTERCEPT ──────────────────

        # ── CASE RECALL INTERCEPT ──────────────────────────────────
        # Handle cases where the user asks about their case status or progress.
        # This can happen at any time (even after welcomed).
        if _wants_case_recall(text_clean) or self._awaiting_name_or_ref_for_recall:
            if self._awaiting_name_or_ref_for_recall:
                _refusal = {
                    "no",
                    "nahi",
                    "nahin",
                    "nah",
                    "naah",
                    "mat",
                    "cancel",
                    "skip",
                    "ruko",
                    "band",
                    "chhodo",
                }
                text_words = set(re.findall(r"[a-zA-Z\u0900-\u097F']+", text_clean))
                is_refusal = (
                    bool(text_words & _refusal)
                    or "don't" in text_clean
                    or "dont" in text_clean
                )
                if is_refusal:
                    self._awaiting_name_or_ref_for_recall = False
                    logger.info("Case recall check cancelled by user")
                    ack = (
                        "Theek hai, koi baat nahi! Aur kya madad karoon?"
                        if reply_lang == "hi"
                        else "No problem! How else can I help you?"
                    )
                    try:
                        await self.session.say(ack, allow_interruptions=True)
                    except Exception as err:
                        logger.warning("Could not speak cancel ack: %s", err)
                    raise StopResponse()

            ref = extract_ticket_ref(text)

            # If the user provided a reference ID
            if ref:
                self._awaiting_name_or_ref_for_recall = False
                ticket = escalation.get_escalation(ref)
                if ticket:
                    # Retrieve status & issue details
                    speak = _format_ticket_status_response(ticket, reply_lang)
                    logger.info(
                        "Case recall by ref: %s -> %s", ref, ticket.get("status")
                    )
                else:
                    speak = (
                        f"I couldn't find any ticket with reference ID {ref}. "
                        "Please double check the reference ID and try again."
                        if reply_lang == "en"
                        else f"Mujhe reference ID {ref} ka koi ticket nahi mila. "
                        "Kripya reference ID check karke phir se koshish karein."
                    )
                try:
                    await self.session.say(speak, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak ticket status: %s", err)
                raise StopResponse()

            # If the user did not provide a ref, check if we have a known caller name
            known_name = self._known_caller_name
            # If we were awaiting a name/ref and they just gave a name
            if self._awaiting_name_or_ref_for_recall and not known_name:
                extracted_name = extract_caller_name(text) or _extract_bare_name(text)
                if extracted_name:
                    known_name = extracted_name
                    # Also link it as our known caller name for the session
                    self._known_caller_name = extracted_name
                    self._memory_loaded = True
                    # Check if caller has a profile
                    caller_profile = db.get_caller(extracted_name)
                    if caller_profile:
                        # Merge facts if needed
                        facts = caller_profile.get("facts") or {}
                        if facts.get("last_topic"):
                            self._last_user_topic = str(facts["last_topic"])
                        if facts.get("last_escalation_ref"):
                            self._last_escalation_ref = str(
                                facts["last_escalation_ref"]
                            )

            if known_name and known_name.lower() != "caller":
                self._awaiting_name_or_ref_for_recall = False
                # Look up tickets for this user
                user_id = known_name.lower().replace(" ", "_")
                tickets = escalation.list_escalations(user_id=user_id)
                if tickets:
                    # Speak status of the most recent ticket
                    most_recent = tickets[0]
                    speak = _format_ticket_status_response(
                        most_recent, reply_lang, known_name
                    )
                    logger.info(
                        "Case recall by name: %s -> %s",
                        known_name,
                        most_recent.get("reference_id"),
                    )
                else:
                    speak = (
                        f"I see you are {known_name}, but I couldn't find any registered cases "
                        "under your name. Would you like me to create a new ticket for you?"
                        if reply_lang == "en"
                        else f"Main dekh sakti hoon ki aap {known_name} hain, par mujhe aapke naam par "
                        "koi case nahi mila. Kya aap naya ticket banana chahte hain?"
                    )
                try:
                    await self.session.say(speak, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak ticket status: %s", err)
                raise StopResponse()

            # If we have a session escalation ref
            if self._last_escalation_ref:
                self._awaiting_name_or_ref_for_recall = False
                ticket = escalation.get_escalation(self._last_escalation_ref)
                if ticket:
                    speak = _format_ticket_status_response(ticket, reply_lang)
                    logger.info(
                        "Case recall by session ref: %s", self._last_escalation_ref
                    )
                    try:
                        await self.session.say(speak, allow_interruptions=True)
                    except Exception as err:
                        logger.warning("Could not speak ticket status: %s", err)
                    raise StopResponse()

            # If we don't know the name or ref, ask for it
            self._awaiting_name_or_ref_for_recall = True
            speak = (
                "I'd be happy to check your case status. Could you please tell me your name "
                "or the case reference ID?"
                if reply_lang == "en"
                else "Main aapke case ka status check kar sakti hoon. Kripya apna naam "
                "ya case reference ID bataiye?"
            )
            try:
                await self.session.say(speak, allow_interruptions=True)
            except Exception as err:
                logger.warning("Could not ask for name/ref: %s", err)
            raise StopResponse()
        # ── END CASE RECALL INTERCEPT ──────────────────────────────

        # ── SAVE INTERCEPT: bypass LLM entirely for save flow ──────
        # This prevents the agent from spamming previous topic answers
        # when the user is trying to save the conversation.
        if self._awaiting_name_for_save:
            _refusal = {
                "no",
                "nahi",
                "nahin",
                "nah",
                "naah",
                "mat",
                "cancel",
                "skip",
                "ruko",
                "band",
                "chhodo",
            }
            text_words = set(re.findall(r"[a-zA-Z\u0900-\u097F']+", text_clean))
            is_refusal = (
                bool(text_words & _refusal)
                or "don't save" in text_clean
                or "dont save" in text_clean
            )
            if is_refusal:
                self._awaiting_name_for_save = False
                logger.info("Save cancelled by user")
                ack = (
                    "Theek hai, koi baat nahi! Aur kya madad karoon?"
                    if reply_lang == "hi"
                    else "No problem! How else can I help you?"
                )
                try:
                    await self.session.say(ack, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak cancel ack: %s", err)
                raise StopResponse()

            name = extract_caller_name(text) or _extract_bare_name(text)
            if name:
                self._awaiting_name_for_save = False
                extra = {}
                if self._last_escalation_ref:
                    extra = {
                        "last_escalation_ref": self._last_escalation_ref,
                        "last_escalation_status": "open",
                    }
                self._persist_caller_breadcrumb(
                    name, extra_facts=extra, lang=reply_lang
                )
                self._saved_this_session = True
                confirm = _save_confirm_line(name, reply_lang)
                logger.info("Save intercept: saved %s", name)
                try:
                    await self.session.say(confirm, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak save confirm: %s", err)
                raise StopResponse()
            else:
                # Could not extract name — re-ask without letting LLM run
                ask = (
                    "Kripya apna naam bataiye."
                    if reply_lang == "hi"
                    else "Could you please tell me your name?"
                )
                try:
                    await self.session.say(ask, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not re-ask name: %s", err)
                raise StopResponse()

        if _wants_save(text_clean):
            name = extract_caller_name(text) or self._known_caller_name
            if name:
                extra = {}
                if self._last_escalation_ref:
                    extra = {
                        "last_escalation_ref": self._last_escalation_ref,
                        "last_escalation_status": "open",
                    }
                self._persist_caller_breadcrumb(
                    name, extra_facts=extra, lang=reply_lang
                )
                self._saved_this_session = True
                self._awaiting_name_for_save = False
                confirm = _save_confirm_line(name, reply_lang)
                logger.info("Save intercept: saved %s directly", name)
                try:
                    await self.session.say(confirm, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not speak save confirm: %s", err)
                raise StopResponse()
            else:
                self._awaiting_name_for_save = True
                ask = (
                    "Zaroor! Kripya apna naam bataiye taaki main conversation save kar sakoon."
                    if reply_lang == "hi"
                    else "Sure! Please tell me your name so I can save this conversation."
                )
                logger.info("Save intercept: awaiting name")
                try:
                    await self.session.say(ask, allow_interruptions=True)
                except Exception as err:
                    logger.warning("Could not ask for name: %s", err)
                raise StopResponse()
        # ── END SAVE INTERCEPT ─────────────────────────────────────

        # Track active topic for caller memory recall
        text_lower = text.lower()
        if (
            "bank account" in text_lower
            or "bank" in text_lower
            or "khata" in text_lower
        ):
            self._last_user_topic = "opening a bank account"
        elif bool(re.search(r"\bfd\b", text_lower)) or "fixed deposit" in text_lower:
            self._last_user_topic = "Fixed Deposits"
        elif "pmjdy" in text_lower or "jan dhan" in text_lower:
            self._last_user_topic = "PMJDY scheme"
        elif "pmsby" in text_lower or "suraksha" in text_lower:
            self._last_user_topic = "PMSBY insurance"
        elif "pmjjby" in text_lower or "jeevan jyoti" in text_lower:
            self._last_user_topic = "PMJJBY life insurance"
        elif "apy" in text_lower or "pension" in text_lower:
            self._last_user_topic = "Atal Pension Yojana"
        elif any(w in text_lower for w in ["upi", "gpay", "google pay", "phonepe", "paytm", "g pay", "digital payment"]):
            self._last_user_topic = "Gpay and digital payments"
        elif any(w in text_lower for w in ["fraud", "unauthorized", "stole", "stolen", "scam", "scammed", "hack", "hacked", "suspicious"]):
            self._last_user_topic = "fraud / unauthorized access"
        elif any(w in text_lower for w in ["escalat", "case", "ticket", "nodal", "specialist", "dispute", "chargeback"]):
            self._last_user_topic = "human escalation case"
        elif "lost" in text_lower and "card" in text_lower:
            self._last_user_topic = "lost card / account security"
        elif "loan" in text_lower or "emi" in text_lower:
            self._last_user_topic = "loans"
        elif "insurance" in text_lower or "bima" in text_lower:
            self._last_user_topic = "insurance"
        elif "scheme" in text_lower or "yojana" in text_lower:
            self._last_user_topic = "government schemes"

        # If caller just gave their name mid-call (not save, not already welcomed),
        # attach any in-session escalation + topic to their profile.
        intro_name = extract_caller_name(text)
        if (
            intro_name
            and not self._awaiting_name_for_save
            and (
                not self._known_caller_name
                or intro_name.lower() != self._known_caller_name.lower()
            )
        ):
            self._persist_caller_breadcrumb(intro_name, lang=reply_lang)
            logger.info("Linked session state to caller name %s", intro_name)

        # Cross-call memory: auto lookup returning caller on NEW call.
        try:
            self._auto_memory_for_turn(turn_ctx, text)
        except Exception as err:
            logger.warning("Auto memory hook failed: %s", err)

        # Keep at most ONE ephemeral language lock in context (replace, never stack).
        # Hidden so the UI never shows it (otherwise it pollutes the chat log with instructions).
        _strip_lang_locks(turn_ctx)
        if reply_lang == "en":
            lock = (
                f"{_HIDDEN_LANG_PREFIX} CRITICAL: Reply in English ONLY this turn. "
                "No Hindi words. No Devanagari. No Hinglish. "
                "Ignore any earlier Hindi replies in history for language choice. "
                "Never ask for OTP, PIN, or account number. "
                "Never promise scheme approval."
            )
        else:
            lock = (
                f"{_HIDDEN_LANG_PREFIX} CRITICAL: Reply in Hindi only this turn. "
                "Ignore any earlier English replies in history for language choice. "
                "OTP, PIN, ya account number kabhi mat mango. "
                "Scheme approval kabhi guarantee mat karo."
            )
        turn_ctx.add_message(role="system", content=lock)

        # Re-attach memory note AFTER lang lock strip so it survives this turn.
        if self._known_caller_name and self._memory_loaded:
            caller = db.get_caller(self._known_caller_name)
            if caller:
                if was_welcomed_before_turn or self._saved_this_session:
                    turn_ctx.add_message(
                        role="system", content=_format_passive_memory(caller)
                    )
                elif not self._welcomed_this_session:
                    self._welcomed_this_session = True
                    turn_ctx.add_message(
                        role="system", content=_format_memory_note(caller)
                    )

        logger.info("Turn language lock set once: %s", reply_lang)


# Keep one warm process so the next call after END CALL joins quickly.
# HTTP health port for the worker (not the voice UI). Frontend is on :3000.
server = AgentServer(num_idle_processes=1, port=8081)
metrics.start_metrics_server_thread()


def _detect_call_channel(room) -> str:
    try:
        for participant in room.remote_participants.values():
            if getattr(participant, "kind", None) == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                return "sip"
    except Exception:
        logger.debug("Could not inspect participants for channel", exc_info=True)
    return "browser"


def prewarm(proc: JobProcess):
    # Stricter VAD so speaker echo / room noise is less likely to start a turn.
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.5,
        min_silence_duration=0.8,
        activation_threshold=0.75,
        prefix_padding_duration=0.3,
    )


server.setup_fnc = prewarm


import asyncio


@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # NVIDIA Nemotron (OpenAI-compatible Integrate API) — replaces Gemini
    nvidia_api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get(
        "NVIDIA_API_KEY", ""
    )
    if not nvidia_api_key:
        raise RuntimeError(
            "Set OPENAI_API_KEY (or NVIDIA_API_KEY) to your nvapi-… key for Nemotron."
        )
    nvidia_llm = openai.LLM(
        model="nvidia/nemotron-3-nano-30b-a3b",
        api_key=nvidia_api_key,
        base_url=os.environ.get(
            "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
        ),
        temperature=0.6,
        max_completion_tokens=512,
        # Without this, Nemotron dumps chain-of-thought into content and speaks it aloud.
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    logger.info("Using NVIDIA Nemotron-3-Nano-30B on Integrate API (thinking off)")

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=nvidia_llm,
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
    agent._call_room_id = ctx.room.name

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        if not ev.is_final:
            return
        language = str(ev.language) if ev.language else None
        agent.note_stt_language(language, ev.transcript)
        agent._last_user_final_at = time.monotonic()
        db.note_user_turn(ctx.room.name)
        logger.info(
            "STT final transcript lang=%s text=%r",
            language,
            (ev.transcript or "")[:120],
        )




    @session.on("agent_state_changed")
    def on_agent_state_changed(ev) -> None:
        new_state = getattr(ev, "new_state", None) or getattr(ev, "state", None)
        state_name = str(getattr(new_state, "value", new_state) or "").lower()
        if "speak" not in state_name or agent._last_user_final_at is None:
            return
        latency_ms = int((time.monotonic() - agent._last_user_final_at) * 1000)
        db.note_reply_latency_ms(ctx.room.name, latency_ms)
        agent._last_user_final_at = None

    # CRITICAL: connect to room FIRST, then start session
    await ctx.connect()
    db.init_db()
    escalation.init_escalation_db()
    db.start_call(ctx.room.name, _detect_call_channel(ctx.room))
    logger.info("Room connected, starting agent session for %s", ctx.room.name)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            text_input=True,
            text_output=True,
        ),
    )
    db.mark_call_connected(ctx.room.name)

    async def cleanup():
        # Always persist last_topic + open ticket so the NEXT call can recall them.
        if agent._known_caller_name:
            try:
                agent._persist_caller_breadcrumb(
                    agent._known_caller_name,
                    extra_facts={"last_room": ctx.room.name},
                    lang=agent._reply_lang,
                )
            except Exception as err:
                logger.warning("Failed to persist session breadcrumb: %s", err)
        try:
            # If the call was connected (has started_at), it's success. Cancel before connect = failure.
            db.end_call(ctx.room.name, _detect_call_channel(ctx.room))
        except Exception as err:
            logger.warning("Failed to record call outcome: %s", err)
        logger.info("Session finished cleanly for room: %s", ctx.room.name)

    ctx.add_shutdown_callback(cleanup)

    # Short spoken intro so the caller knows the agent is live (empty greeting
    # made calls feel dead / "not replying when call starts").
    if FIRST_GREETING.strip():
        try:
            await session.say(FIRST_GREETING, allow_interruptions=True)
            logger.info("Played initial greeting")
        except Exception as err:
            logger.error("Error playing initial greeting: %s", err)
    else:
        logger.info("Skipping intro speech; agent is listening immediately")


if __name__ == "__main__":
    cli.run_app(server)
