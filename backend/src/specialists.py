"""Focused agents used by Jan Sahay's specialist handoff team.

The active ``AgentSession`` owns the chat context, so replacing the active agent
with ``session.update_agent`` keeps the caller's conversation available to the
specialist.  Specialists deliberately have smaller instructions than the
primary assistant and can hand control back when the topic changes.
"""

import json
from typing import TYPE_CHECKING

from livekit.agents import Agent, RunContext, function_tool, llm
from livekit.agents.llm import StopResponse

import db
import escalation
import schemes

if TYPE_CHECKING:
    from agent import Assistant


SPECIALIST_IDS = {"government_schemes", "digital_safety", "account_support"}


def specialist_reply_instructions(
    display_name: str,
    *,
    security_incident: bool = False,
    escalation_ref: str | None = None,
) -> str:
    """Force the active specialist to answer the latest question in character."""
    extra = ""
    if security_incident:
        if escalation_ref:
            extra = (
                f" Reference ticket {escalation_ref} has already been created for this report. "
                f"Confirm ticket ID {escalation_ref} to the caller, provide clear safety steps, "
                "and ask how else you can assist. Do not ask for permission again and do not call create_specialist_case."
            )
        else:
            extra = (
                " This is a card-loss, compromise, phishing, or fraud report. "
                "Give a short safety answer, recap the incident without secrets, "
                "ask permission, and call create_specialist_case when they agree."
            )
    return (
        f"You are {display_name}. You already introduced yourself. "
        "Answer the caller's latest question now, in character as this specialist. "
        "Do not introduce yourself again. Do not say you are Jan Sahay. "
        "Stay on this turn and keep helping; do not stop after one sentence." + extra
    )


class SpecialistAgent(Agent):
    """Base class for a single-topic specialist with a safe return path."""

    specialist_id: str
    display_name: str
    hindi_display_name: str
    scope: str
    hindi_scope: str
    spoken_help_en: str
    spoken_help_hi: str
    ticket_trigger_type = "user_requested"
    ticket_urgency = "medium"

    def __init__(self, primary_agent: "Assistant", reply_lang: str) -> None:
        self._primary_agent = primary_agent
        self._reply_lang = reply_lang
        super().__init__(
            instructions=self._instructions(reply_lang), id=self.specialist_id
        )

    def _instructions(self, reply_lang: str) -> str:
        language = "Hindi" if reply_lang == "hi" else "English"
        return f"""
You are {self.display_name}, part of the Jan Sahay specialist team.
Your only job is: {self.scope}
Continue the caller's existing conversation; they must not repeat details already
shared. Reply in {language}, briefly and respectfully. Do not use markdown.
Never ask for or repeat OTPs, PINs, passwords, card numbers, Aadhaar numbers, or
bank account numbers. Never promise approval, payment, or account changes.

IDENTITY:
- Always speak as {self.display_name}. Never say you are Jan Sahay.
- You already introduced yourself. Do not introduce yourself again.
- Answer every in-scope follow-up. Do not stop after one message.

SPECIALIST TICKET POLICY:
If a reference ticket (e.g. JS-XXXXXXX) is already created or mentioned, acknowledge it, give practical security steps, and do not ask for permission again.
Only ask for permission if no ticket exists yet and the caller explicitly asks for a formal ticket or escalation.

Do NOT call return_to_main_agent for follow-up questions in your domain.
The system switches specialists automatically when the topic changes.
Only call return_to_main_agent for clearly unrelated small talk, or when the
caller asks to go back to Jan Sahay.
"""

    def introduction(self) -> str:
        """Short spoken introduction after this agent becomes active."""
        if self._reply_lang == "hi":
            return (
                f"Namaste, main aapki {self.hindi_display_name} hoon. "
                f"Main {self.spoken_help_hi} mein madad kar sakti hoon."
            )
        return (
            f"Hello, I am your {self.display_name}. "
            f"I can help with {self.spoken_help_en}."
        )

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Stay active, switch specialists, or return manager-portal work."""
        import re as _re

        text = new_message.text_content or ""
        text_clean = text.strip().lower()

        # ── Noise / echo filter (mirrors Assistant) ────────────────
        _noise = {
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
        if not text_clean or text_clean in _noise:
            raise StopResponse()
        words = _re.findall(r"[a-zA-Z\u0900-\u097F']+", text_clean)
        text_norm = _re.sub(r"[^\w\s]", "", text_clean).lower().strip()

        _known_echo_frags = (
            "tell me your name",
            "could you please tell me",
            "can you please tell me",
            "save this chat window",
            "share the salmonella",
            "pass this case",
            "share a summary of your issue",
            "permission to proceed",
            "taking over your case",
            "human specialist team",
            "digital banking safety specialist",
            "bank account support specialist",
            "government scheme specialist",
            "wanna share",
            "for this query",
        )
        if any(frag in text_norm for frag in _known_echo_frags):
            raise StopResponse()

        from agent import _ALLOWED_SHORT_GREETS

        is_short_greet = text_norm in _ALLOWED_SHORT_GREETS
        if not is_short_greet and len(words) < 2 and len(text_clean) < 6:
            raise StopResponse()
        # ── End noise filter ───────────────────────────────────────

        primary = self._primary_agent
        try:
            await primary.apply_language(
                text, primary._last_stt_language, turn_ctx=turn_ctx
            )
            self._reply_lang = primary._reply_lang
        except Exception:
            pass

        import agent as agent_mod

        if agent_mod._is_manager_portal_intent(text):
            primary._active_specialist_id = None
            primary._session = self.session
            self.session.update_agent(primary)
            await primary.on_user_turn_completed(turn_ctx, new_message)
            raise StopResponse()

        route = agent_mod._specialist_route_for_text(text)
        if route and route != self.specialist_id:
            # Primary's session is stale (specialist owns it); pass it through.
            primary._session = self.session
            await primary._handoff_current_session(route, text)
            raise StopResponse()

        if route is None and agent_mod._is_general_jan_sahay_turn(text):
            primary._active_specialist_id = None
            primary._session = self.session
            self.session.update_agent(primary)
            message = (
                "I will return you to Jan Sahay for this."
                if self._reply_lang == "en"
                else "Is sawaal ke liye main aapko Jan Sahay ke paas wapas bhej rahi hoon."
            )
            await self.session.say(message, allow_interruptions=False)
            await primary.on_user_turn_completed(turn_ctx, new_message)
            raise StopResponse()

        # In-scope follow-up: stay here and let this specialist generate.

    @function_tool
    async def return_to_main_agent(
        self, ctx: RunContext, reason: str = "The caller's topic changed."
    ) -> str:
        """Return the caller to Jan Sahay when the request is outside this
        specialist's narrow scope, the specialist's work is complete, or the
        caller explicitly asks to speak with the main assistant. The full
        conversation remains available after the return.
        """
        self._primary_agent._active_specialist_id = None
        message = (
            "I have completed that part. I will return you to Jan Sahay for the next step."
            if self._reply_lang == "en"
            else "Maine is hissa ki madad poori kar di hai. Main aapko agle kadam ke liye Jan Sahay ke paas wapas bhej rahi hoon."
        )
        ctx.session.update_agent(self._primary_agent)
        await ctx.session.say(message, allow_interruptions=False)
        return json.dumps({"returned": True, "reason": reason})

    @function_tool
    async def create_specialist_case(
        self,
        ctx: RunContext,
        issue_description: str,
        user_consent: bool,
        requester_name: str = "",
        contact_hint: str = "",
        diagnostic_steps: str | None = None,
    ) -> str:
        """Create one follow-up ticket for this specialist's domain.

        Use only after listening to the full story and receiving explicit consent
        to share a non-sensitive summary. The caller must have supplied a clear
        description of the incident or assistance needed. Use a name or contact
        preference when already available, but do not make the caller repeat it.
        Never include OTPs, PINs,
        passwords, account/card numbers, Aadhaar, PAN, or other secrets.

        For Digital Banking Safety reports, include what happened (for example,
        phishing message, suspicious link, UPI scam, or unsafe login), but never
        ask the caller for their account credentials. The ticket appears in the
        Jan Sahay escalations dashboard and duplicate open cases are updated,
        rather than duplicated.
        """
        name = (
            requester_name.strip() or self._primary_agent._known_caller_name or "Caller"
        )
        if not issue_description.strip():
            return json.dumps(
                {
                    "ok": False,
                    "message": "Ask for a clear, non-sensitive incident or assistance description before creating a case.",
                }
            )

        result = escalation.create_escalation(
            user_id=name.lower().replace(" ", "_"),
            requester_name=name,
            contact_hint=contact_hint,
            issue_description=issue_description,
            diagnostic_steps=diagnostic_steps
            or [
                f"Case collected by {self.display_name}.",
                "Caller gave permission to share a non-sensitive summary.",
            ],
            user_consent=user_consent,
            trigger_type=self.ticket_trigger_type,
            urgency=self.ticket_urgency,
            preferred_language=self._reply_lang,
        )
        if result.get("ok"):
            self._primary_agent._last_escalation_ref = result.get("reference_id")
            self._primary_agent._last_user_topic = self.scope
            if self._primary_agent._call_room_id:
                db.record_escalation(self._primary_agent._call_room_id)
        return json.dumps(result)


class GovernmentSchemeSpecialist(SpecialistAgent):
    specialist_id = "government_schemes"
    display_name = "Government Scheme Specialist"
    hindi_display_name = "Sarkari Yojana Specialist"
    scope = (
        "explain PMJDY, PMSBY, PMJJBY, and APY; help with eligibility, documents, "
        "benefits, premiums, and application preparation"
    )
    hindi_scope = "sarkari yojanaon, paatrata, dastavezon aur aavedan ki taiyari"
    spoken_help_en = "government schemes, eligibility, documents, and application steps"
    spoken_help_hi = "sarkari yojanaon, paatrata, dastavezon aur aavedan"
    ticket_trigger_type = "complex_decision"

    @function_tool
    async def get_scheme_details(self, ctx: RunContext, scheme_name: str) -> str:
        """Look up official-style local data for PMJDY, PMSBY, PMJJBY, or APY.
        Use for benefits, premium, age range, or a short scheme explanation.
        Always state the returned data_as_of date to the caller.
        """
        return json.dumps(schemes.get_scheme_overview(scheme_name))

    @function_tool
    async def check_scheme_eligibility(
        self,
        ctx: RunContext,
        scheme_name: str,
        age: int | None = None,
        has_bank_account: bool | None = None,
        is_indian_resident: bool | None = None,
    ) -> str:
        """Check likely eligibility after the caller has provided the needed
        non-sensitive facts. Do not infer missing facts or guarantee approval.
        """
        return json.dumps(
            schemes.check_eligibility(
                scheme_name=scheme_name,
                age=age,
                has_bank_account=has_bank_account,
                is_indian_resident=is_indian_resident,
            )
        )

    @function_tool
    async def get_document_checklist(self, ctx: RunContext, scheme_name: str) -> str:
        """Get the application document checklist for a supported government
        scheme. Remind the caller that their bank or CSC may require extra KYC.
        """
        return json.dumps(schemes.get_document_checklist(scheme_name))


class DigitalSafetySpecialist(SpecialistAgent):
    specialist_id = "digital_safety"
    display_name = "Digital Banking Safety Specialist"
    hindi_display_name = "Digital Banking Suraksha Specialist"
    scope = (
        "give practical UPI, mobile-banking, ATM, phishing, and scam-prevention "
        "guidance; explain safe next steps without accessing accounts"
    )
    hindi_scope = "UPI, ATM, phishing aur digital banking suraksha"
    spoken_help_en = "UPI, ATM safety, phishing, lost cards, and scam prevention"
    spoken_help_hi = "UPI, ATM suraksha, phishing, gum card aur scam roktham"
    ticket_trigger_type = "fraud_suspected"
    ticket_urgency = "high"

    def _instructions(self, reply_lang: str) -> str:
        return (
            super()._instructions(reply_lang)
            + """
For a report of phishing, a lost/stolen/compromised card, a scam, an
unauthorised debit, suspicious login, or account compromise: the handoff
announcement has already told the caller this needs the Security Specialist.
A reference ticket is created as soon as the incident is handed over. Confirm
the reference ID, give short safe next steps, and do not create a second ticket
unless the caller reports a new incident. Never request credentials or tell the
caller that Jan Sahay can block a card or access an account.
"""
        )


class AccountSupportSpecialist(SpecialistAgent):
    specialist_id = "account_support"
    display_name = "Bank Account Support Specialist"
    hindi_display_name = "Bank Khata Sahayata Specialist"
    scope = (
        "explain non-transactional bank-account opening, KYC preparation, and "
        "general account-service steps; you cannot access or change any account"
    )
    hindi_scope = "bank khata kholne, KYC aur samanya khata sahayata"
    spoken_help_en = "KYC, opening a bank account, and general account steps"
    spoken_help_hi = "KYC, bank khata kholna aur samanya khata madad"
    ticket_trigger_type = "user_requested"

    def _instructions(self, reply_lang: str) -> str:
        return (
            super()._instructions(reply_lang)
            + """
For a bank account, explain the normal application/KYC process and next steps.
Do NOT ask for a Safe Key: it is only for a separate Jan Sahay profile, not for
opening, adding, or applying for a bank account. You cannot create, activate,
or link a bank account on the caller's behalf.
"""
        )


def create_specialist(
    specialist_id: str, primary_agent: "Assistant", reply_lang: str
) -> SpecialistAgent:
    """Create only the requested focused agent; invalid routes fail safely."""
    specialist_types = {
        "government_schemes": GovernmentSchemeSpecialist,
        "digital_safety": DigitalSafetySpecialist,
        "account_support": AccountSupportSpecialist,
    }
    try:
        return specialist_types[specialist_id](primary_agent, reply_lang)
    except KeyError as exc:
        raise ValueError(f"Unknown specialist: {specialist_id}") from exc
