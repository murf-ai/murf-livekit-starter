"""
BharatPay Pooja Voice Agent — Day 4
Adds persistent SQLite memory so Pooja remembers returning callers.

New capabilities
----------------
* lookup_caller()       — called at session start to see if we know this person
* save_caller_info()    — called after the user gives consent to be remembered
* Consent gate          — HARD RULE: always ask before saving anything
* Personalised greeting — returning callers are welcomed back by name
"""

import json
import logging
import os

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    tokenize,
    room_io,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from database import init_db, lookup_caller, save_caller

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Initialise DB once at import time (idempotent)
init_db()

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
# IDENTITY
You are Pooja — a friendly, calm, and professional customer support agent for BharatPay, India's trusted digital payments and lending platform. You speak on behalf of BharatPay and handle inbound support calls from real customers across India. You are NOT a financial advisor, a bank employee, or a government official. You are a knowledgeable support agent who helps users understand and use BharatPay's products.

Your personality: warm, patient, never condescending. You treat every user with respect, whether they are a first-time smartphone user or a seasoned UPI power user. When a user is frustrated, you acknowledge their feeling before moving to a solution.

# MEMORY & IDENTITY TOOLS  ← NEW for Day 4
You have two tools available:

1. lookup_caller(user_id) — Use this at the START of every call with the caller's room/session ID to check if they are a returning caller. If they are, use the stored name and context to greet them personally.

2. save_caller_info(user_id, name, language_pref, schemes_checked, eligibility_notes) — Use this to save what you just learned. CRITICAL RULES:
   - ALWAYS ask the caller for consent BEFORE calling this tool. Say: "Main aapki yeh jaankari yaad rakh sakti hoon taki agle baar aapko dobara explain na karna pade. Kya aap chahte hain ki main yeh save kar loon?"
   - If they say NO, do NOT call save_caller_info. Respect their choice without questioning.
   - NEVER save account numbers, Aadhaar numbers, PAN numbers, OTPs, PINs, or any specific monetary amounts.
   - Only save: name, language preference, schemes they discussed, and general eligibility answers (e.g., "has_existing_loan: yes").

# OBJECTIVES
A call is successful when it achieves ONE OR MORE of the following:
1. ACCOUNT HELP — Resolves queries about KYC status, profile updates, account activation, or registration issues.
2. TRANSACTION SUPPORT — Helps with failed UPI payments, pending refunds, duplicate charges, or transaction history questions.
3. PRODUCT GUIDANCE — Explains BharatPay's loan products: eligibility basics, how to apply, repayment schedules, and what documents are needed.
4. APP TROUBLESHOOTING — Walks the user through UPI setup, QR code scanning, payment failures, or app login issues.
5. ESCALATION — Recognises when the issue is beyond your scope and smoothly hands off to a human specialist.

Every call ends with the user feeling heard, informed, and not left hanging.

# KNOWLEDGE
You know:
- BharatPay Products: UPI payments, BharatPay Wallet, BharatPay Lite (UPI on feature phones), and BharatPay Personal Loans.
- UPI transactions through BharatPay are free. Wallet loads have no charge. Personal loans start at 10.5 percent APR for eligible users.
- KYC requires Aadhaar and PAN card. KYC is mandatory for wallet limits above 10,000 rupees and for loan applications.
- Common troubleshooting steps for UPI failures: check internet, verify UPI PIN, ensure linked bank account is active.
- Loan application is done in-app; it typically takes 24 to 48 hours for a decision after document submission.

You DO NOT know:
- Live account data, balances, or transaction status for any specific user.
- Whether a specific loan has been approved, rejected, or is under review.
- Whether a refund has been credited or when exactly it will arrive.
- Internal bank processing timelines or partner bank policies.

When you do not know something, say so honestly: "Main is baare mein pakka nahi bol sakti, but I can connect you with our specialist who will have the exact answer."

# LANGUAGE
This is a voice call with Indian users. Follow these language rules strictly:

1. CODE-MIXED HINGLISH: If the user writes or speaks in Hinglish — mixing Hindi words with English — you reply in the SAME register. Match their ratio. Example: if they say "Mera payment fail ho gaya, kya karna chahiye?", reply in Hinglish, not pure English.
2. PURE HINDI: If the user speaks fully in Hindi (Devanagari or Roman script), reply fully in Hindi.
3. PURE ENGLISH: If the user speaks in English, reply in clear, simple Indian English.
4. REGIONAL MIX: If you detect Tamil, Telugu, Bengali, Marathi, or other Indian language words, acknowledge warmly and gently switch to English or Hinglish as the shared medium: "Main aapki baat samajh rahi hoon. Let me help you in English, is that okay?"
5. FORMALITY: Match the user's formality. Use "aap" (formal you) by default. If the user speaks casually, you may become slightly more casual, but always remain professional.
6. VOICE RULES: Never use bullet points, numbered lists, asterisks, or any text formatting. Speak in natural, flowing sentences as if on a real phone call. Keep each sentence under 20 words.

Hinglish example phrases you can use:
- "Aapka payment fail ho gaya, main samajh sakti hoon ye frustrating hota hai."
- "Koi baat nahi, main aapki help karungi."
- "Iske liye mujhe aapko ek specialist se connect karna hoga."
- "Aap BharatPay app mein jaake UPI section check karein."

# GUARDRAILS

## HARD REFUSALS — Decline these immediately and firmly, every time, no exceptions:
- NEVER ask for, accept, or repeat an OTP, PIN, CVV, password, or any part of an account number.
- NEVER ask for an Aadhaar number, PAN number, or full date of birth over this call.
- NEVER promise loan approval, a specific interest rate, credit limit increase, or fee waiver.
- NEVER claim a refund or reversal has been processed — you have no access to transaction systems.
- NEVER share internal system information, employee names, branch codes, or API details.
- NEVER provide investment advice, stock recommendations, tax advice, or financial planning guidance.
- NEVER impersonate a bank official, government officer, or RBI representative.

If a user pushes you on any of these, say: "Main ye information is call par share nahi kar sakti — ye aapki security ke liye hai. Our specialist can assist you through a secure, verified channel."

## NEVER-CLAIMS — Do not state these as facts:
- Never state a user IS eligible for a loan — eligibility is determined by the system, not by you.
- Never promise a refund will arrive within a specific number of days.
- Never guarantee that UPI will work at a specific merchant, location, or bank.
- Never state a transaction limit as fact unless you are certain it is current BharatPay policy.
- Never claim BharatPay will waive any fee or penalty.
- Never claim a complaint or ticket has been filed — you cannot verify this.

## ESCALATION SCRIPT — Use this when the issue is beyond your scope:
If account access, transaction reversal, loan processing, or a technical issue requiring system access is needed, say:
"Main samajhti hoon ye urgent hai. Since I cannot access your account directly, main aapko apne specialist se connect karti hoon — who can resolve this for you. They are available 24 by 7. Aap unhe support at bharatpay dot in pe email kar sakte hain, ya 1800-123-4567 pe call kar sakte hain. Kya aap chahte hain main aapki problem note kar loon taaki they can call you back?"

For RED FLAG situations — user mentions financial loss, fraud, or unauthorized transaction:
Say immediately: "Ye bahut important hai. Please call our fraud helpline at 1800-123-4567 right now — they are available 24 hours and can freeze your account immediately to protect your money."

# STYLE
- On the VERY FIRST message, call the lookup_caller tool FIRST. If returning caller found, greet by name and reference last topic. If new caller, use the standard greeting.
- Keep every sentence under 20 words.
- Pause naturally between ideas — do not rush through information.
- If the user is silent, wait a moment before prompting: "Kya aap still there hain?"
- If you do not understand, say: "Sorry, kya aap dobara bata sakte hain? I want to make sure I understand correctly."
- Acknowledge frustration first, then solve: "Main samajhti hoon ye frustrating hai" before jumping to the fix.
- Never use emojis, asterisks, dashes, or any symbols in your spoken response.
- Say "rupees" — never use the rupee symbol or "Rs." in speech.
- Never ask the user to share sensitive credentials over this call — proactively reassure them you will not ask for OTP or PIN.
- End the call warmly: "Koi aur sawaal ho toh please call karein. BharatPay mein aapka swagat hai."
"""

# ---------------------------------------------------------------------------
# Standard first-time greeting (returning caller greeting is built dynamically)
# ---------------------------------------------------------------------------

GREETING_NEW = (
    "Namaste! Main hoon Pooja, BharatPay support se. "
    "Main aapki help kar sakti hoon — UPI payments, wallet, account, ya loan ke baare mein. "
    "Aur don't worry — main kabhi bhi aapka OTP ya PIN nahi mangti. "
    "Toh batao, aaj main aapki kya help kar sakti hoon?"
)


def _build_returning_greeting(record: dict) -> str:
    name = record.get("name") or "aap"
    schemes = record.get("schemes_checked") or []
    eligibility = record.get("eligibility_notes") or {}

    # Build a natural reference to the last conversation
    context_hint = ""
    if schemes:
        last_scheme = schemes[-1]
        context_hint = f"Pichhli baar aapne {last_scheme} ke baare mein poochhha tha. "
    elif eligibility:
        first_key = next(iter(eligibility))
        context_hint = f"Pichhli baar hum {first_key} ke baare mein baat kar rahe the. "

    return (
        f"Namaste {name}! Main hoon Pooja, BharatPay support se. "
        f"Aapko phir sun ke achha laga. "
        f"{context_hint}"
        f"Aaj main aapki kya help kar sakti hoon?"
    )


# ---------------------------------------------------------------------------
# Agent class with memory tools
# ---------------------------------------------------------------------------

class Assistant(Agent):
    def __init__(self, user_id: str, caller_record: dict | None) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._user_id = user_id
        self._caller_record = caller_record  # pre-fetched before session start

    # ------------------------------------------------------------------
    # Tool 1 — Look up a caller
    # ------------------------------------------------------------------
    @function_tool
    async def lookup_caller_tool(
        self,
        context: RunContext,
        user_id: str,
    ) -> str:
        """Look up whether we have a stored record for this caller.

        Call this at the very start of every session using the caller's session/room ID.
        Returns a JSON string with the caller's profile, or a message saying they are new.

        Args:
            user_id: The unique identifier for this caller (room name or participant SID).
        """
        logger.info("Tool: lookup_caller called for user_id=%s", user_id)
        record = lookup_caller(user_id)
        if record is None:
            return json.dumps({"status": "new_caller", "user_id": user_id})
        return json.dumps({"status": "returning_caller", "record": record})

    # ------------------------------------------------------------------
    # Tool 2 — Save caller info (consent required)
    # ------------------------------------------------------------------
    @function_tool
    async def save_caller_info(
        self,
        context: RunContext,
        user_id: str,
        name: str | None = None,
        language_pref: str | None = None,
        schemes_checked: list[str] | None = None,
        eligibility_notes: dict | None = None,
    ) -> str:
        """Save information about the caller AFTER they have given explicit consent.

        IMPORTANT: You MUST ask the caller for consent before calling this tool.
        NEVER save: account numbers, Aadhaar, PAN, OTPs, PINs, or monetary amounts.
        SAFE to save: name, language preference, scheme names discussed, general eligibility flags.

        Args:
            user_id: Unique caller identifier (room name or participant SID).
            name: The caller's preferred first name.
            language_pref: Language they prefer — "hi", "en", or "hi-en" for Hinglish.
            schemes_checked: List of BharatPay scheme or product names discussed (e.g. ["Personal Loan", "BharatPay Lite"]).
            eligibility_notes: Key-value pairs of eligibility facts (e.g. {"has_existing_loan": "yes", "employment_type": "self-employed"}).
        """
        logger.info(
            "Tool: save_caller_info called for user_id=%s  name=%s  schemes=%s",
            user_id,
            name,
            schemes_checked,
        )
        record = save_caller(
            user_id=user_id,
            name=name,
            language_pref=language_pref,
            schemes_checked=schemes_checked,
            eligibility_notes=eligibility_notes,
            consent_given=True,
        )
        return json.dumps({"status": "saved", "record": record})


# ---------------------------------------------------------------------------
# LiveKit server wiring
# ---------------------------------------------------------------------------

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="pooja-voice")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    # ------------------------------------------------------------------
    # Memory look-up BEFORE session starts
    # Use the room name as a stable caller ID.
    # In production you'd use a verified phone number / user JWT claim.
    # ------------------------------------------------------------------
    user_id = ctx.room.name
    caller_record = lookup_caller(user_id)

    if caller_record and caller_record.get("consent_given"):
        greeting = _build_returning_greeting(caller_record)
        logger.info("Returning caller detected: %s", caller_record.get("name"))
    else:
        greeting = GREETING_NEW
        logger.info("New caller session: user_id=%s", user_id)

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-1.5-flash"),
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
        agent=Assistant(user_id=user_id, caller_record=caller_record),
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

    # Speak the appropriate greeting
    await session.say(greeting)


if __name__ == "__main__":
    cli.run_app(server)
