import asyncio
import logging
import json
from datetime import datetime

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
    UserInputTranscribedEvent,
    function_tool,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

try:
    from prompt import SYSTEM_PROMPT
except ImportError:
    from src.prompt import SYSTEM_PROMPT

try:
    from specialist_prompts import (
        FRAUD_SPECIALIST_PROMPT,
        GOV_SCHEMES_SPECIALIST_PROMPT,
        LOAN_SPECIALIST_PROMPT,
        AGRI_SPECIALIST_PROMPT,
        SPECIALIST_PROMPTS,
        SPECIALIST_DISPLAY_NAMES,
        SPECIALIST_HINDI_NAMES,
        build_specialist_prompt,
    )
except ImportError:
    from src.specialist_prompts import (
        FRAUD_SPECIALIST_PROMPT,
        GOV_SCHEMES_SPECIALIST_PROMPT,
        LOAN_SPECIALIST_PROMPT,
        AGRI_SPECIALIST_PROMPT,
        SPECIALIST_PROMPTS,
        SPECIALIST_DISPLAY_NAMES,
        SPECIALIST_HINDI_NAMES,
        build_specialist_prompt,
    )

try:
    import db
except ImportError:
    import src.db as db


# ==============================================================================
# MURF VOICE PROFILES & DYNAMIC VOICE SWITCHING
# ==============================================================================
# Voice Profiles & Personas:
# - Default (Main Intake Guide): Anisha (Conversation style)
# - Specialists (On Transfer/Handoff):
#     * Cyber Safety & Fraud: Samar (en-IN, Conversational style)
#     * Government Schemes: Pooja (en-IN / hi-IN, Conversational style)
#     * Micro-Credit & Loans: Samar (en-IN, Conversational style)
#     * Agri & PMFBY: Palak (en-IN / hi-IN, Conversational style)
VOICE_PROFILES = {
    "default": {"voice": "Anisha", "style": "Conversation", "locale": None},
    "fraud": {"voice": "Samar", "locale": "en-IN", "style": "Conversational"},
    "government_scheme": {"voice": "Pooja", "locale": "en-IN", "style": "Conversational"},
    "schemes": {"voice": "Pooja", "locale": "en-IN", "style": "Conversational"},
    "pension": {"voice": "Pooja", "locale": "en-IN", "style": "Conversational"},
    "loan": {"voice": "Samar", "locale": "en-IN", "style": "Conversational"},
    "agri": {"voice": "Palak", "locale": "en-IN", "style": "Conversational"},
}


def get_voice_config_for_agent(agent_type: str = "default", language_pref: str = "English") -> dict:
    """Returns the Murf TTS voice, locale, and style for the given agent role and language preference."""
    profile = VOICE_PROFILES.get(agent_type.lower(), VOICE_PROFILES["default"]).copy()
    if agent_type.lower() == "default":
        return profile

    if language_pref.lower() == "hindi":
        # Palak and Pooja support native hi-IN (Hindi - India)
        if profile.get("voice") in ["Palak", "Pooja"]:
            profile["locale"] = "hi-IN"
        else:
            profile["locale"] = "en-IN"
    else:
        profile["locale"] = "en-IN"
    return profile


# ==============================================================================
# BASE AGENT WITH SHARED CAPABILITIES
# ==============================================================================

class BaseDhanRakshakAgent(Agent):
    """Base class for Dhan Rakshak AI Agents with shared memory and safety tools."""

    def __init__(self, user_id: str, call_id: str, instructions: str = SYSTEM_PROMPT) -> None:
        super().__init__(instructions=instructions)
        self.user_id = user_id
        self.call_id = call_id

    @function_tool
    async def lookup_caller(self) -> str:
        """Looks up the current caller's details and saved facts in the database.
        Always execute this tool at the very beginning of the call to check if they are a returning caller.
        """
        logger.info(f"Tool lookup_caller called for current user: {self.user_id}")
        user_info = db.get_user(self.user_id)
        if user_info:
            return json.dumps(user_info)
        return f"No record found for user ID: {self.user_id}"

    @function_tool
    async def record_caller_query(self, caller_query: str, domain: str = "general") -> str:
        """Records the caller's initial inquiry topic in the database during the welcoming turn.
        
        Args:
            caller_query: Summary of what the caller asked about.
            domain: The domain topic ('government_scheme', 'fraud', 'loan', 'agri', 'general').
        """
        logger.info(f"Recording caller initial query for user {self.user_id}: {caller_query} (domain: {domain})")
        user_info = db.get_user(self.user_id) or {}
        facts = user_info.get("facts", {})
        facts["last_query"] = caller_query
        facts["inquiry_domain"] = domain
        caller_name = str(user_info.get("name", "Citizen")) if user_info.get("name") else "Citizen"
        raw_lang = user_info.get("language_preference", "English")
        if isinstance(raw_lang, dict):
            raw_lang = raw_lang.get("language", raw_lang.get("language_preference", "English"))
        lang_pref = str(raw_lang)
        db.save_user(self.user_id, caller_name, lang_pref, facts)
        return f"Successfully logged caller inquiry topic: '{caller_query}' in database."

    @function_tool
    async def save_caller_facts(self, name: str, language_preference: str, facts: dict) -> str:
        """Saves current caller's details and facts (e.g. checked schemes, eligibility answers) to the database.
        Always verify the caller has given verbal permission/consent before calling this.
        
        Args:
            name: The caller's name.
            language_preference: The caller's preferred language (e.g., Hindi, English, Hinglish).
            facts: A dictionary of key-value pairs representing facts about the caller. Do not store account or ID numbers.
        """
        logger.info(f"Tool save_caller_facts called for user_id: {self.user_id}, name: {name}")
        cleaned_facts = {}
        for k, v in facts.items():
            if "id" in k.lower() or "account" in k.lower() or "number" in k.lower() or "pin" in k.lower() or "otp" in k.lower():
                continue
            cleaned_facts[k] = v
        
        db.save_user(self.user_id, name, language_preference, cleaned_facts)
        return f"Successfully saved details for user {name} (ID: {self.user_id})."

    @function_tool
    async def create_escalation(
        self,
        caller_name: str,
        situation: str,
        what_happened: str,
        urgency: str,
        language: str,
        follow_up_method: str,
        contact_details: str,
        checked_facts: dict = {}
    ) -> str:
        """Creates a human support request/escalation in the database when the caller reports fraud or requests a manual decision.
        Always verify the caller has given verbal permission/consent before calling this.
        Do NOT save credit card numbers, passwords, OTPs, PINs, or account numbers in the what_happened details.
        
        Args:
            caller_name: The caller's name.
            situation: Short description of the reason, e.g. "Fraud Reporting" or "Manual Approval Request".
            what_happened: Detailed explanation of the caller's concern.
            urgency: How urgent this issue is. Must be exactly one of: "Low", "Medium", "High", "Emergency".
            language: The caller's preferred language.
            follow_up_method: The caller's preferred contact method (e.g., Phone Call, SMS, Email).
            contact_details: Phone number or email to reach them.
            checked_facts: Key-value facts/context the agent already checked.
        """
        logger.info(f"Tool create_escalation called for user_id: {self.user_id}, name: {caller_name}")
        ref_id = db.create_escalation(
            caller_id=self.user_id,
            caller_name=caller_name,
            situation=situation,
            what_happened=what_happened,
            checked_facts=checked_facts,
            urgency=urgency,
            language=language,
            follow_up_method=follow_up_method,
            contact_details=contact_details
        )
        db.update_call_progress(self.call_id, status="success", outcome_type="Escalation")
        return ref_id

    @function_tool
    async def record_refusal(self, reason: str) -> str:
        """Call this tool if the caller explicitly declines to participate, says 'no' to receiving details or consent, or requests to stop the call/communication.
        
        Args:
            reason: The reason for refusal (e.g. 'Declined outbound offer', 'Refused consent to save facts', 'Refused escalation permission').
        """
        logger.info(f"Tool record_refusal called: {reason}")
        db.update_call_progress(self.call_id, failure_category="User declined")
        return "Refusal recorded successfully."


# ==============================================================================
# SPECIALIST AGENT CLASSES (STEP 2: FOCUSED ROLES, INSTRUCTIONS, AND LIMITS)
# ==============================================================================

class FraudSpecialist(BaseDhanRakshakAgent):
    """Dedicated Cyber Fraud & Emergency Account Containment Specialist."""

    def __init__(self, user_id: str, call_id: str, instructions: str = FRAUD_SPECIALIST_PROMPT) -> None:
        super().__init__(user_id=user_id, call_id=call_id, instructions=instructions)

    @function_tool
    async def get_bank_fraud_hotlines(self, bank_name: str = "All") -> str:
        """Returns verified emergency helpline numbers for Indian banks to freeze compromised accounts/cards.
        
        Args:
            bank_name: Name of the bank (e.g., 'SBI', 'HDFC', 'ICICI', 'PNB', 'Axis', 'Bank of Baroda', or 'All').
        """
        hotlines = {
            "National Cyber Crime Helpline": "1930 (Immediate 24x7 Golden Hour Reporting)",
            "State Bank of India (SBI)": "1800 1234 / 1800 2100 / SMS 'BLOCK' to 567676",
            "HDFC Bank": "1800 1600 / 1800 2600",
            "ICICI Bank": "1800 1080",
            "Punjab National Bank (PNB)": "1800 1800 / 1800 2021",
            "Axis Bank": "1860 419 5555 / 1860 500 5555",
            "Bank of Baroda": "1800 5700",
            "Official Cyber Crime Reporting Portal": "https://cybercrime.gov.in"
        }
        name_upper = bank_name.upper().strip()
        matched = {k: v for k, v in hotlines.items() if name_upper in k.upper()}
        result = matched if matched else hotlines
        return json.dumps(result)

    @function_tool
    async def file_cyber_complaint_guide(self) -> str:
        """Provides official step-by-step instructions for reporting financial cyber fraud to the government."""
        return json.dumps({
            "immediate_steps": [
                "1. Dial 1930 immediately (National Cyber Crime Helpline) to request transaction freeze in the recipient account.",
                "2. Visit https://cybercrime.gov.in and file a complaint under 'Financial Fraud'.",
                "3. Keep transaction IDs, bank statements, SMS alerts, and suspect phone numbers ready.",
                "4. Visit your nearest Police Station / Cyber Cell if amount exceeds Rs 50,000 or upon request from 1930."
            ],
            "safety_warning": "Never share OTP, ATM PIN, UPI PIN, or internet banking passwords with anyone, including bank representatives."
        })


class GovernmentSchemeSpecialist(BaseDhanRakshakAgent):
    """Dedicated Government Schemes & Welfare Programs Specialist (Pooja)."""

    def __init__(self, user_id: str, call_id: str, instructions: str = GOV_SCHEMES_SPECIALIST_PROMPT) -> None:
        super().__init__(user_id=user_id, call_id=call_id, instructions=instructions)

    @function_tool
    async def calculate_apy_contribution(self, current_age: int, desired_monthly_pension: int = 5000) -> str:
        """Calculates exact monthly, quarterly, and half-yearly contributions for Atal Pension Yojana (APY).
        
        Args:
            current_age: The citizen's age in years (must be between 18 and 40).
            desired_monthly_pension: Desired monthly pension after age 60. Must be 1000, 2000, 3000, 4000, or 5000.
        """
        if current_age < 18 or current_age > 40:
            return json.dumps({
                "eligible": False,
                "error": f"Age {current_age} is outside APY entry age limits (18 to 40 years). Individuals above 40 can explore NPS Tier 1 or Senior Citizen Savings Scheme."
            })
        
        if desired_monthly_pension not in [1000, 2000, 3000, 4000, 5000]:
            return json.dumps({
                "eligible": False,
                "error": "Desired pension slab must be exactly 1000, 2000, 3000, 4000, or 5000 Rupees per month."
            })

        multiplier = desired_monthly_pension // 1000
        
        base_monthly = {
            18: 42, 19: 46, 20: 50, 21: 54, 22: 59, 23: 64, 24: 70, 25: 76,
            26: 82, 27: 90, 28: 97, 29: 106, 30: 116, 31: 126, 32: 138, 33: 151,
            34: 165, 35: 181, 36: 198, 37: 218, 38: 240, 39: 264, 40: 291
        }
        
        monthly = base_monthly.get(current_age, 116) * multiplier
        quarterly = monthly * 3
        half_yearly = monthly * 6
        years_of_contribution = 60 - current_age
        
        return json.dumps({
            "eligible": True,
            "entry_age": current_age,
            "years_to_contribute": years_of_contribution,
            "guaranteed_monthly_pension_at_60": f"Rs {desired_monthly_pension:,}",
            "monthly_contribution": f"Rs {monthly:,}",
            "quarterly_contribution": f"Rs {quarterly:,}",
            "half_yearly_contribution": f"Rs {half_yearly:,}",
            "tax_payer_exclusion": "Note: Income tax payers are ineligible to join APY (effective Oct 1, 2022).",
            "nominee_benefit": "Full accumulated corpus is returned to nominee/spouse upon subscriber's demise."
        })

    @function_tool
    async def get_nps_guidelines(self, current_age: int = 30) -> str:
        """Returns National Pension System (NPS) Tier-1 guidelines, equity/debt allocation, and tax benefits under Sec 80CCD(1B)."""
        return json.dumps({
            "scheme": "National Pension System (NPS)",
            "eligibility": "Any Indian citizen aged 18 to 70 years.",
            "tax_benefits": "Deduction up to Rs 1.5 Lakh under 80C, plus EXCLUSIVE additional deduction of Rs 50,000 under Section 80CCD(1B).",
            "withdrawal_at_60": "60% corpus is tax-free lump-sum withdrawal, 40% mandatory annuity for lifetime regular pension."
        })


# Alias for backwards compatibility
PensionSpecialist = GovernmentSchemeSpecialist


class LoanSpecialist(BaseDhanRakshakAgent):
    """Dedicated Small Business & Micro-Credit Specialist (Mudra, SVANidhi, Stand-Up India)."""

    def __init__(self, user_id: str, call_id: str, instructions: str = LOAN_SPECIALIST_PROMPT) -> None:
        super().__init__(user_id=user_id, call_id=call_id, instructions=instructions)

    @function_tool
    async def check_mudra_eligibility(self, loan_amount: int, business_type: str, is_new_business: bool = False) -> str:
        """Evaluates Mudra loan category (Shishu, Kishore, Tarun, Tarun Plus), document checklist, and collateral-free rules.
        
        Args:
            loan_amount: Loan amount requested in INR. Up to Rs 20,000,000 (20 Lakhs).
            business_type: Type of non-farm micro/small enterprise (e.g. retail, manufacturing, repair, food).
            is_new_business: True if starting fresh, False if expanding an existing enterprise.
        """
        if loan_amount <= 50000:
            category = "Shishu (शिशु)"
            max_limit = "Rs 50,000"
            processing_fee = "NIL"
            doc_requirements = ["Aadhaar Card / Voter ID", "Proof of business address", "Quotation of machinery/items to purchase"]
        elif loan_amount <= 500000:
            category = "Kishore (किशोर)"
            max_limit = "Rs 50,001 to Rs 5 Lakhs"
            processing_fee = "0.50% (often waived by PSBs)"
            doc_requirements = ["Aadhaar & PAN", "Udyam Registration", "Last 6 months bank statement", "Business proof & projected balance sheet"]
        elif loan_amount <= 1000000:
            category = "Tarun (तरुण)"
            max_limit = "Rs 5 Lakhs to Rs 10 Lakhs"
            processing_fee = "0.50%"
            doc_requirements = ["Aadhaar & PAN", "Udyam Registration", "Last 12 months bank statement", "2 years ITR / sales tax records", "Project report"]
        elif loan_amount <= 2000000:
            category = "Tarun Plus (तरुण प्लस - Expanded 2024-2026 Limit)"
            max_limit = "Rs 10 Lakhs to Rs 20 Lakhs (for repeat entrepreneurs with good repayment record)"
            processing_fee = "Standard bank charges"
            doc_requirements = ["Prior Mudra repayment clearance certificate", "Audited financial statements", "Udyam Certificate", "ITR records"]
        else:
            return json.dumps({
                "eligible": False,
                "reason": "Mudra loans are capped at Rs 20 Lakhs. For higher loans, explore CGTMSE or MSME loan schemes."
            })

        return json.dumps({
            "category": category,
            "loan_amount_requested": f"Rs {loan_amount:,}",
            "limit_bracket": max_limit,
            "collateral_required": "NO collateral security required (backed by Credit Guarantee Fund for Micro Units - CGFMU).",
            "processing_fee": processing_fee,
            "document_checklist": doc_requirements,
            "how_to_apply": "Apply online via www.udyamimitra.in or visit any commercial bank, Regional Rural Bank (RRB), or NBFC."
        })

    @function_tool
    async def get_pm_svanidhi_details(self, vendor_type: str = "street_vendor") -> str:
        """Returns PM SVANidhi micro-credit details for street vendors (10k, 20k, 50k tranches with 7% interest subsidy)."""
        return json.dumps({
            "scheme": "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
            "tranches": [
                "1st Tranche: Rs 10,000 (1 year tenure)",
                "2nd Tranche: Rs 20,000 (upon timely repayment of 1st)",
                "3rd Tranche: Rs 50,000 (upon timely repayment of 2nd)"
            ],
            "interest_subsidy": "7% annual interest subsidy credited directly to bank account.",
            "digital_incentive": "Cashback up to Rs 1,200 per year for conducting digital UPI transactions.",
            "documents": "Vending Certificate / Urban Local Body (ULB) Identity Card, Aadhaar Card, Bank Passbook."
        })


class AgriSpecialist(BaseDhanRakshakAgent):
    """Dedicated Agri-Financial, Crop Insurance (PMFBY), and Farmer Welfare Specialist."""

    def __init__(self, user_id: str, call_id: str, instructions: str = AGRI_SPECIALIST_PROMPT) -> None:
        super().__init__(user_id=user_id, call_id=call_id, instructions=instructions)

    @function_tool
    async def check_crop_insurance_details(self, crop_name: str, season: str, state: str = "All India") -> str:
        """Returns PMFBY premium rates, localized damage claims rules, and 72-hour intimation requirements.
        
        Args:
            crop_name: Name of the crop (e.g. Paddy, Wheat, Cotton, Soybean, Mustard, Sugarcane, Onion).
            season: Season: 'Kharif', 'Rabi', or 'Commercial/Horticultural'.
            state: State name.
        """
        season_lower = season.lower()
        if "kharif" in season_lower:
            premium_rate = "2.0% of Sum Insured (Farmer's share; balance paid 50:50 by Central & State Govts)"
        elif "rabi" in season_lower:
            premium_rate = "1.5% of Sum Insured"
        else:
            premium_rate = "5.0% of Sum Insured (Commercial / Horticultural crops)"

        return json.dumps({
            "scheme": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "crop": crop_name,
            "season": season,
            "premium_payable_by_farmer": premium_rate,
            "CRITICAL_72_HOUR_CLAIM_RULE": "In case of localized disaster (hailstorm, unseasonal rain, inundation, landslide), farmer MUST intimate crop loss within 72 hours via Crop Insurance App, helpline 14447, or local agriculture officer.",
            "required_documents": ["Land Record (Khasra/Khatauni/7/12/RoR)", "Sowing Certificate / Patwari report", "Aadhaar Card", "Bank Passbook linked with DBT"],
            "helpline": "14447 (National Toll-Free Crop Insurance Helpline)"
        })

    @function_tool
    async def get_pm_kisan_details(self) -> str:
        """Returns PM-KISAN guidelines, Rs 6,000 benefit, eKYC status instructions, and land seeding rules."""
        return json.dumps({
            "scheme": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
            "annual_financial_benefit": "Rs 6,000 per year transferred in 3 equal installments of Rs 2,000 directly to bank account.",
            "mandatory_criteria": [
                "1. Aadhaar-based eKYC completed on pmkisan.gov.in or CSC center.",
                "2. Land details seeded and verified in State land records.",
                "3. Bank account linked with Aadhaar and active DBT enabled."
            ],
            "helpline": "155261 / 011-24300606"
        })

    @function_tool
    async def get_kisan_credit_card_details(self, land_size_acres: float = 0) -> str:
        """Returns Kisan Credit Card (KCC) limit guidelines, 4% interest rate, and application checklist."""
        return json.dumps({
            "scheme": "Kisan Credit Card (KCC)",
            "effective_interest_rate": "4% per annum (7% basic rate minus 3% prompt repayment incentive).",
            "collateral_free_limit": "Up to Rs 1.60 Lakhs (and up to Rs 3 Lakhs with tie-up arrangements).",
            "revolving_credit": "Valid for 5 years with annual review and flexible drawdowns for seed/fertilizer/pesticide purchases."
        })


# ==============================================================================
# MAIN ASSISTANT AGENT (STEPS 3, 4, 5: HANDOFF TOOL, CONTEXT PASSING & ANNOUNCEMENT)
# ==============================================================================

class Assistant(BaseDhanRakshakAgent):
    """Main Dhan Rakshak Assistant handling general intake, welfare schemes, and handoffs to specialists."""

    def __init__(
        self,
        user_id: str,
        call_id: str,
        instructions: str = SYSTEM_PROMPT,
        session: AgentSession | None = None
    ) -> None:
        super().__init__(user_id=user_id, call_id=call_id, instructions=instructions)
        self.active_specialist = None
        self._voice_session = session

    # Step 3: Add handoff tool to main agent
    @function_tool
    async def handoff_to_specialist(
        self,
        specialist_type: str,
        user_inquiry_summary: str,
        caller_crop_or_scheme: str = ""
    ) -> str:
        """Transfers the caller and conversation to a dedicated financial specialist guide.
        
        CRITICAL RULE: Call this tool ONLY after the caller's second question or when deep domain calculations/checklists are needed.
        
        Choose the appropriate specialist_type:
        - 'government_scheme' (or 'schemes', 'pension'): For all Central/State Government Schemes, APY, SSY, PMJDY, PMSBY, PMJJBY, NPS. (Voice: Pooja)
        - 'fraud': For urgent UPI scams, unauthorized debits, compromised OTP/passwords, fake loan apps, or account freezing. (Voice: Samar)
        - 'loan': For Pradhan Mantri Mudra Yojana (Shishu/Kishore/Tarun), small business loans, or PM SVANidhi. (Voice: Samar)
        - 'agri': For PM Fasal Bima Yojana (PMFBY), crop damage intimation (72h rule), PM-KISAN, or Kisan Credit Card (KCC). (Voice: Palak)
        
        Args:
            specialist_type: The domain specialist to hand off to. Must be one of: 'government_scheme', 'fraud', 'loan', 'agri', 'schemes', 'pension'.
            user_inquiry_summary: A concise summary of the caller's specific problem or request so the specialist can immediately continue.
            caller_crop_or_scheme: Optional name of the crop, scheme, or bank mentioned by the user.
        """
        spec_key = specialist_type.lower().strip()
        if spec_key in ["pension", "schemes", "scheme", "gov_scheme", "government_schemes"]:
            spec_key = "government_scheme"
            
        if spec_key not in ["fraud", "government_scheme", "loan", "agri"]:
            spec_key = "government_scheme"  # Default fallback
            
        spec_name_en = SPECIALIST_DISPLAY_NAMES.get(spec_key, "Specialist")
        spec_name_hi = SPECIALIST_HINDI_NAMES.get(spec_key, "विशेषज्ञ")
        
        logger.info(f"Handoff initiated for user {self.user_id} to specialist '{spec_key}'. Summary: {user_inquiry_summary}")
        
        # Track transition state in DB: Connecting to specialist
        db.update_call_progress(self.call_id, outcome_type=f"Connecting to {spec_name_en}...")
        self.active_specialist = spec_key
        
        # Step 4: Pass the conversation context & user facts to the specialist
        user_info = db.get_user(self.user_id) or {}
        caller_name = str(user_info.get("name", "")) if user_info.get("name") else ""
        raw_lang = user_info.get("language_preference", "English")
        if isinstance(raw_lang, dict):
            raw_lang = raw_lang.get("language", raw_lang.get("language_preference", "English"))
        language_pref = str(raw_lang)
        facts = user_info.get("facts", {})
        if caller_crop_or_scheme:
            facts["focused_topic"] = caller_crop_or_scheme
            
        new_instructions = build_specialist_prompt(
            specialist_type=spec_key,
            user_inquiry_summary=user_inquiry_summary,
            caller_name=caller_name,
            language_pref=language_pref,
            facts=facts
        )
        
        # Dynamically update the active agent's instructions with specialist prompt & preserved memory
        await self.update_instructions(new_instructions)

        # Step 5: Speak the connection message in the FIRST/MAIN agent's voice (Anisha)
        if language_pref.lower() == "hindi":
            connecting_line = f"मैं आपको हमारे {spec_name_hi} से कनेक्ट कर रही हूँ। कृपया एक पल रुकिए।"
            specialist_intro = f"नमस्ते! मैं आपकी {spec_name_hi} हूँ।"
            lang_rule = "STRICT LANGUAGE RULE: Respond ONLY in 100% Hindi (Devanagari script). Do NOT speak English."
        else:
            connecting_line = f"I will connect you to our {spec_name_en}. Please hold on a moment."
            specialist_intro = f"Hello! I am your {spec_name_en}."
            lang_rule = "STRICT LANGUAGE RULE: Respond ONLY in 100% English. Do NOT speak Hindi."

        activity = getattr(self, "_activity", None)
        active_session = getattr(self, "_voice_session", None) or (activity.session if activity is not None else None)
        if active_session:
            try:
                logger.info(f"Main agent (Anisha) speaking transition announcement: '{connecting_line}'")
                await active_session.say(connecting_line, allow_interruptions=False)
            except Exception as e:
                logger.warning(f"Could not speak handoff announcement: {e}")

        # Transition directly to specialist voice with minimal delay
        logger.info(f"[TRANSITION IN PROGRESS] Connecting to {spec_name_en}... Switching voice immediately.")
        await asyncio.sleep(0.2)

        # Step 7: Dynamically switch Murf TTS voice to specialist voice (Samar/Pooja/Palak)
        voice_cfg = get_voice_config_for_agent(spec_key, language_pref)
        if active_session and hasattr(active_session, "tts") and active_session.tts:
            try:
                logger.info(
                    f"[VOICE SWITCH] Switching TTS voice to {voice_cfg['voice']} (locale={voice_cfg['locale']}, "
                    f"style={voice_cfg['style']}) for {spec_name_en}"
                )
                active_session.tts.update_options(
                    voice=voice_cfg["voice"],
                    locale=voice_cfg["locale"],
                    style=voice_cfg["style"]
                )
            except Exception as e:
                logger.warning(f"Could not dynamically update TTS voice options: {e}")

        # Update DB outcome to fully connected
        db.update_call_progress(self.call_id, status="success", outcome_type=f"Connected: {spec_name_en}")
        logger.info(f"[CONNECTED] Specialist {spec_name_en} is now active with voice {voice_cfg['voice']}")

        return (
            f"[HANDOFF TO {spec_name_en.upper()} SUCCESSFUL - VOICE HAS SWITCHED TO {voice_cfg['voice'].upper()}]\n"
            f"{lang_rule}\n"
            f"IMPORTANT: The main agent (Anisha) has ALREADY spoken '{connecting_line}'. Do NOT repeat 'I will connect you...'.\n"
            f"1. Specialist Introduction: Start your reply directly with '{specialist_intro}'\n"
            f"2. Direct Answer: Immediately address '{user_inquiry_summary}' with clear guidance in that same single language."
        )

    @function_tool
    async def handoff_to_main_guide(self, user_inquiry_summary: str = "") -> str:
        """Transfers the caller back to the main Dhan Rakshak Intake Guide (Anisha) for general scheme inquiries.
        
        Args:
            user_inquiry_summary: Optional summary of what the user needs help with next.
        """
        self.active_specialist = None
        user_info = db.get_user(self.user_id) or {}
        raw_lang = user_info.get("language_preference", "English")
        if isinstance(raw_lang, dict):
            raw_lang = raw_lang.get("language", raw_lang.get("language_preference", "English"))
        language_pref = str(raw_lang)
        
        # Track transition state in DB: Connecting back to main guide
        db.update_call_progress(self.call_id, outcome_type="Connecting to Main Dhan Rakshak Guide (Anisha)...")
        
        # Reset instructions back to main SYSTEM_PROMPT
        await self.update_instructions(SYSTEM_PROMPT)
        
        if language_pref.lower() == "hindi":
            connecting_line = "मैं आपको वापस हमारे जन सहाय मुख्य गाइड, अनीशा जी से जोड़ रहा हूँ। कृपया एक पल रुकिए।"
            main_intro = "नमस्ते! मैं जन सहाय से अनीशा हूँ।"
            lang_rule = "STRICT LANGUAGE RULE: Respond ONLY in 100% Hindi (Devanagari script)."
        else:
            connecting_line = "I am connecting you back to our main Dhan Rakshak Guide, Anisha. Please hold on a moment."
            main_intro = "Hello! I am Anisha from Dhan Rakshak."
            lang_rule = "STRICT LANGUAGE RULE: Respond ONLY in 100% English."

        activity = getattr(self, "_activity", None)
        active_session = getattr(self, "_voice_session", None) or (activity.session if activity else None)
        if active_session:
            try:
                logger.info(f"Specialist speaking return transition announcement: '{connecting_line}'")
                await active_session.say(connecting_line, allow_interruptions=False)
            except Exception as e:
                logger.warning(f"Could not speak return announcement: {e}")

        # Transition directly back to main guide with minimal delay
        logger.info("[TRANSITION IN PROGRESS] Connecting back to Anisha... Switching voice immediately.")
        await asyncio.sleep(0.2)

        # Reset voice back to main intake guide (Anisha)
        voice_cfg = get_voice_config_for_agent("default", language_pref)
        if active_session and hasattr(active_session, "tts") and active_session.tts:
            try:
                logger.info(f"[VOICE RESET] Resetting TTS voice back to main guide {voice_cfg['voice']}")
                active_session.tts.update_options(
                    voice=voice_cfg["voice"],
                    style=voice_cfg.get("style", "Conversation")
                )
            except Exception as e:
                logger.warning(f"Could not reset TTS voice options: {e}")

        # Update DB outcome to fully connected with main guide
        db.update_call_progress(self.call_id, status="success", outcome_type="Connected: Main Dhan Rakshak Guide (Anisha)")
        logger.info("[CONNECTED] Main Dhan Rakshak Guide (Anisha) is now active.")
                
        return (
            f"[HANDOFF TO MAIN GUIDE SUCCESSFUL - VOICE HAS SWITCHED BACK TO ANISHA]\n"
            f"{lang_rule}\n"
            f"IMPORTANT: The specialist has ALREADY spoken '{connecting_line}'. Do NOT repeat 'I am connecting you...'.\n"
            f"1. Main Guide Greeting: Say '{main_intro}'\n"
            f"2. Ask how you can help them with government schemes."
        )



    # Built-in Scheme Eligibility Checker for General Schemes
    @function_tool
    async def check_scheme_eligibility(
        self,
        scheme_name: str,
        age: int,
        is_income_tax_payer: bool = False,
        girl_child_age: int = -1,
        is_indian_resident: bool = True
    ) -> str:
        """Checks the eligibility of a caller for a specific Indian government financial scheme and returns the required document checklist.
        
        Supported schemes: PMJDY, PMSBY, PMJJBY, APY, SSY.
        """
        today_str = datetime.now().strftime("%B %d, %Y")
        
        try:
            name_upper = scheme_name.upper().strip()
            supported_schemes = ["PMJDY", "PMSBY", "PMJJBY", "APY", "SSY"]
            
            if name_upper not in supported_schemes:
                return json.dumps({
                    "eligible": False,
                    "reason": f"Scheme '{scheme_name}' is not in the general list. Supported schemes are: {', '.join(supported_schemes)}.",
                    "document_checklist": [],
                    "scheme_benefits": {},
                    "data_last_updated": today_str,
                    "error": f"Unsupported scheme: {scheme_name}"
                })
                
            if not is_indian_resident:
                return json.dumps({
                    "eligible": False,
                    "reason": f"Only Indian residents are eligible for {name_upper}.",
                    "document_checklist": [],
                    "scheme_benefits": {},
                    "data_last_updated": today_str
                })
                
            is_eligible = False
            reason = ""
            docs = []
            benefits = {}
            if name_upper == "PMJDY":
                is_eligible = age >= 10
                reason = "Eligible. Open to any resident Indian citizen aged 10 or above." if is_eligible else "Ineligible. Min age to open PMJDY account is 10 years."
                docs = ["Aadhaar Card (primary KYC)", "PAN Card (if available)", "Or other officially valid document"]
                benefits = {
                    "benefits_and_interest": "Zero balance savings account, interest on savings deposit, free Rupay debit card with Rs 2 Lakh accidental insurance, and overdraft facility up to Rs 10,000."
                }
                
            elif name_upper == "PMSBY":
                is_eligible = 18 <= age <= 70
                reason = "Eligible. Open to individuals aged between 18 and 70 years." if is_eligible else f"Ineligible. Age must be between 18 and 70 years. Provided age: {age}."
                docs = ["Aadhaar Card (primary KYC)", "Savings bank account details", "Consent form for auto-debit of premium"]
                benefits = {
                    "premium": "Rs 20 per annum (auto-debited from savings account)",
                    "insurance_cover": "Rs 2 Lakh for accidental death or total permanent disability, and Rs 1 Lakh for partial permanent disability.",
                    "validity": "1 year (June 1 to May 31), auto-renewed annually."
                }
                
            elif name_upper == "PMJJBY":
                is_eligible = 18 <= age <= 50
                reason = "Eligible. Open to individuals aged between 18 and 50 years." if is_eligible else f"Ineligible. Age must be between 18 and 50 years. Provided age: {age}."
                docs = ["Aadhaar Card (primary KYC)", "Savings bank account details", "Consent form for auto-debit of premium"]
                benefits = {
                    "premium": "Rs 436 per annum (auto-debited from savings account)",
                    "insurance_cover": "Rs 2 Lakh life insurance cover for death due to any cause.",
                    "validity": "1 year (June 1 to May 31), auto-renewed annually."
                }
                
            elif name_upper == "APY":
                if is_income_tax_payer:
                    is_eligible = False
                    reason = "Ineligible. Income tax payers are not eligible to join Atal Pension Yojana (rule effective since October 1, 2022)."
                else:
                    is_eligible = 18 <= age <= 40
                    reason = "Eligible. Open to all non-taxpaying citizens aged between 18 and 40 years." if is_eligible else f"Ineligible. Age must be between 18 and 40 years to enroll. Provided age: {age}."
                docs = ["Aadhaar Card (primary KYC)", "Mobile number", "Savings bank account details", "Auto-debit authorization form"]
                benefits = {
                    "premium": "Varies based on entry age and selected pension slab.",
                    "pension_benefit": "Guaranteed minimum pension of Rs 1,000 to Rs 5,000 per month after age 60."
                }
                
            elif name_upper == "SSY":
                if girl_child_age == -1:
                    return json.dumps({
                        "eligible": "uncertain",
                        "reason": "Please provide the age of the girl child using the 'girl_child_age' parameter.",
                        "document_checklist": [],
                        "scheme_benefits": {},
                        "data_last_updated": today_str
                    })
                is_eligible = 0 <= girl_child_age <= 10
                reason = "Eligible. Open for girl child aged 10 years or below." if is_eligible else f"Ineligible. The account can only be opened for a girl child aged 10 years or below. Provided girl child age: {girl_child_age}."
                docs = ["Birth certificate of the girl child (mandatory)", "Aadhaar Card and PAN Card of the parent/guardian", "Proof of address"]
                benefits = {
                    "interest_rate": f"8.2% per annum (compounded annually, tax-free interest as of {today_str})",
                    "tax_benefits": "Triple tax exemption under Section 80C.",
                    "maturity": "Matures after 21 years from account opening or upon marriage after age 18."
                }
                
            db.update_call_progress(self.call_id, status="success", outcome_type="Eligibility Check")
            return json.dumps({
                "eligible": is_eligible,
                "reason": reason,
                "document_checklist": docs,
                "scheme_benefits": benefits,
                "data_last_updated": today_str
            })
            
        except Exception as e:
            logger.error(f"Error checking scheme eligibility: {e}")
            db.update_call_progress(self.call_id, failure_category="API error")
            return json.dumps({
                "eligible": "error",
                "reason": "The eligibility checker system is temporarily experiencing technical issues. Please check the inputs or try again shortly.",
                "document_checklist": [],
                "scheme_benefits": {},
                "data_last_updated": today_str,
                "error": str(e)
            })

    # Specialist Domain Tools callable after handoff or directly
    @function_tool
    async def get_bank_fraud_hotlines(self, bank_name: str = "All") -> str:
        """Returns official emergency toll-free numbers and helpline links to report unauthorized transactions and freeze bank accounts/cards."""
        hotlines = {
            "National Cyber Crime Helpline": "1930 (Immediate 24x7 Golden Hour Reporting)",
            "State Bank of India (SBI)": "1800 1234 / 1800 2100 / SMS 'BLOCK' to 567676",
            "HDFC Bank": "1800 1600 / 1800 2600",
            "ICICI Bank": "1800 1080",
            "Punjab National Bank (PNB)": "1800 1800 / 1800 2021",
            "Axis Bank": "1860 419 5555 / 1860 500 5555",
            "Bank of Baroda": "1800 5700",
            "Official Cyber Crime Reporting Portal": "https://cybercrime.gov.in"
        }
        name_upper = bank_name.upper().strip()
        matched = {k: v for k, v in hotlines.items() if name_upper in k.upper()}
        return json.dumps(matched if matched else hotlines)

    @function_tool
    async def calculate_apy_contribution(self, current_age: int, desired_monthly_pension: int = 5000) -> str:
        """Calculates exact monthly, quarterly, and half-yearly contributions for Atal Pension Yojana (APY)."""
        if current_age < 18 or current_age > 40:
            return json.dumps({
                "eligible": False,
                "error": f"Age {current_age} is outside APY entry age limits (18 to 40 years)."
            })
        
        if desired_monthly_pension not in [1000, 2000, 3000, 4000, 5000]:
            return json.dumps({
                "eligible": False,
                "error": "Desired pension slab must be 1000, 2000, 3000, 4000, or 5000 Rupees."
            })

        multiplier = desired_monthly_pension // 1000
        base_monthly = {
            18: 42, 19: 46, 20: 50, 21: 54, 22: 59, 23: 64, 24: 70, 25: 76,
            26: 82, 27: 90, 28: 97, 29: 106, 30: 116, 31: 126, 32: 138, 33: 151,
            34: 165, 35: 181, 36: 198, 37: 218, 38: 240, 39: 264, 40: 291
        }
        monthly = base_monthly.get(current_age, 116) * multiplier
        return json.dumps({
            "eligible": True,
            "entry_age": current_age,
            "years_to_contribute": 60 - current_age,
            "guaranteed_monthly_pension_at_60": f"Rs {desired_monthly_pension:,}",
            "monthly_contribution": f"Rs {monthly:,}",
            "quarterly_contribution": f"Rs {monthly * 3:,}",
            "half_yearly_contribution": f"Rs {monthly * 6:,}"
        })

    @function_tool
    async def check_mudra_eligibility(self, loan_amount: int, business_type: str, is_new_business: bool = False) -> str:
        """Evaluates Mudra loan category (Shishu, Kishore, Tarun, Tarun Plus) and document checklist for business credit."""
        if loan_amount <= 50000:
            category = "Shishu (up to Rs 50,000)"
            docs = ["Aadhaar Card", "Proof of business/shop address", "Machinery/item purchase quotation"]
        elif loan_amount <= 500000:
            category = "Kishore (Rs 50,001 to Rs 5 Lakhs)"
            docs = ["Aadhaar & PAN", "Udyam Registration", "6 months bank statement", "Business proof"]
        elif loan_amount <= 1000000:
            category = "Tarun (Rs 5 Lakhs to Rs 10 Lakhs)"
            docs = ["Aadhaar & PAN", "Udyam Registration", "12 months bank statement", "2 years ITR / Sales records"]
        elif loan_amount <= 2000000:
            category = "Tarun Plus (Rs 10 Lakhs to Rs 20 Lakhs)"
            docs = ["Prior Mudra repayment clearance certificate", "Audited balance sheet", "Udyam Certificate"]
        else:
            return json.dumps({"eligible": False, "reason": "Mudra loans are capped at Rs 20 Lakhs."})

        return json.dumps({
            "category": category,
            "loan_amount_requested": f"Rs {loan_amount:,}",
            "collateral_required": "NO collateral security required.",
            "document_checklist": docs,
            "application_portal": "www.udyamimitra.in or any commercial bank"
        })

    @function_tool
    async def check_crop_insurance_details(self, crop_name: str, season: str, state: str = "All India") -> str:
        """Returns PMFBY premium rates, 72-hour localized damage claims rules, and helpline 14447."""
        season_lower = season.lower()
        if "kharif" in season_lower:
            premium_rate = "2.0% of Sum Insured (Kharif food/oilseed crops)"
        elif "rabi" in season_lower:
            premium_rate = "1.5% of Sum Insured (Rabi crops like Wheat/Mustard)"
        else:
            premium_rate = "5.0% of Sum Insured (Commercial / Horticultural crops)"

        return json.dumps({
            "scheme": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "crop": crop_name,
            "season": season,
            "premium_rate": premium_rate,
            "CRITICAL_72_HOUR_CLAIM_RULE": "Localized crop damage must be intimated within 72 hours via Crop Insurance App or helpline 14447.",
            "helpline": "14447 (National Toll-Free Helpline)"
        })

    @function_tool
    async def get_pm_kisan_details(self) -> str:
        """Returns PM-KISAN entitlement (Rs 6,000/yr in 3 installments), eKYC rules, and land seeding requirements."""
        return json.dumps({
            "scheme": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
            "benefit": "Rs 6,000 per year in 3 equal installments of Rs 2,000.",
            "requirements": ["1. Aadhaar eKYC on pmkisan.gov.in", "2. Land seeding in State records", "3. DBT-linked bank account"],
            "helpline": "155261"
        })


# ==============================================================================
# LIVEKIT SERVER SETUP & RTC SESSION
# ==============================================================================

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.15,
        min_silence_duration=0.25
    )


server.setup_fnc = prewarm


@server.rtc_session(agent_name="myagent")
async def my_agent(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize SQLite database
    db.init_db()

    # Join the room first
    await ctx.connect()

    # Wait for the participant to connect
    participant = await ctx.wait_for_participant()
    user_id = participant.identity if participant else "unknown_user"
    is_sip = (
        (participant is not None and participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP)
        or ctx.room.name.startswith("outbound_call_room")
    )

    logger.info(f"Active connection with user_id: {user_id}, is_sip: {is_sip}")
    db.init_call_outcome(ctx.job.id, user_id, is_sip)

    import time
    call_start_time = time.time()

    async def on_shutdown():
        import time
        duration = int(time.time() - call_start_time)
        logger.info(f"Call {ctx.job.id} shutdown callback. Duration: {duration}s")
        db.finalize_call_outcome(ctx.job.id, duration)

    ctx.add_shutdown_callback(on_shutdown)

    import random
    schemes_list = [
        "Pradhan Mantri Jan Dhan Yojana",
        "Pradhan Mantri Suraksha Bima Yojana",
        "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "Atal Pension Yojana",
        "Sukanya Samriddhi Yojana"
    ]
    selected_scheme = random.choice(schemes_list)

    if is_sip:
        instructions = (
            f"{SYSTEM_PROMPT}\n\n"
            "OUTBOUND CALL SCENARIO:\n"
            "- Ignore any default returning caller logic. Do NOT check for returning caller facts or greet them by name at the start.\n"
            "- IMPORTANT: You MUST strictly open the conversation with these first two sentences in English:\n"
            "  1. 'Hello, this is Shreya calling from Dhan Rakshak.'\n"
            f"  2. 'We found you eligible for the {selected_scheme} scheme, and the deadline is on August 15th, so hurry up! If you want to know more, say yes, and if you want to stop these calls, say no.'\n"
            f"- If the user says 'yes', you must explain the eligibility criteria for ONLY the {selected_scheme} scheme in EXACTLY ONE SHORT SENTENCE (under 15 words). Do NOT explain any other schemes and do NOT use long paragraphs.\n"
            "- IMPORTANT: To avoid speaking all at once, you MUST speak slowly and keep your responses extremely short (under 15 words).\n"
            "- If the user says 'no', you must wrap up the call. If they ask how to stop these types of calls, reply exactly: 'To stop these calls, press or say 1.'\n"
            "- Do not ask any questions during the main explanation.\n"
            "- Do not say anything else in your opening turn. Wait for the user's response after this opening."
        )
    else:
        instructions = (
            f"{SYSTEM_PROMPT}\n\n"
            f"CURRENT USER CALL INFO:\n"
            f"- Current Caller User ID: {user_id}\n"
            f"- IMPORTANT: You MUST immediately call `lookup_caller` at the very start of the conversation. "
            f"If a record is returned, welcome the user back by name and reference their previous interaction. "
            f"If no record is found, greet them as a new user."
        )

    # Set up low-latency voice AI pipeline using Murf Falcon, Gemini 2.5 Flash, Deepgram Nova-3, and preemptive generation
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-flash-latest",
            temperature=0.7,
        ),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Set up latency listeners on session
    user_stopped_time = 0.0

    @session.on("user_stopped_speaking")  # type: ignore
    def on_user_stopped_speaking():
        nonlocal user_stopped_time
        import time
        user_stopped_time = time.time()

    @session.on("agent_started_speaking")  # type: ignore
    def on_agent_started_speaking():
        nonlocal user_stopped_time
        import time
        if user_stopped_time > 0:
            latency = time.time() - user_stopped_time
            db.add_latency_measurement(ctx.job.id, latency)
            user_stopped_time = 0.0

    # Start the session, which initializes the voice pipeline and warms up the models
    assistant_agent = Assistant(
        user_id=user_id,
        call_id=ctx.job.id,
        instructions=instructions,
        session=session
    )
    await session.start(
        agent=assistant_agent,
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

    if is_sip:
        await session.say(
            f"Hello, this is Shreya calling from Dhan Rakshak. "
            f"We found you eligible for the {selected_scheme} scheme, and the deadline is on August 15th, so hurry up! "
            f"If you want to know more, say yes, and if you want to stop these calls, say no.",
            allow_interruptions=True
        )
    else:
        # Trigger the agent to initiate the conversation for web users
        session.generate_reply(user_input="A user just connected. Please start the conversation as instructed.")


if __name__ == "__main__":
    cli.run_app(server)
