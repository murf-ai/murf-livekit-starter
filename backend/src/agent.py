import logging
from datetime import datetime
from typing import Optional

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
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("health-access-agent")

load_dotenv(".env.local")

try:
    from .prompt import FIRST_GREETING, SYSTEM_PROMPT
except ImportError:
    from prompt import FIRST_GREETING, SYSTEM_PROMPT




# In-memory stores for session runtime
ASHA_VISIT_LOGS: list[dict] = []
MEDICATION_REMINDERS: list[dict] = [
    {
        "id": "1",
        "medication_name": "Iron Folic Acid (IFA)",
        "dosage": "1 tablet",
        "time_of_day": "Morning after breakfast",
        "food_relation": "with water, avoid tea/coffee",
        "taken_today": False,
    },
    {
        "id": "2",
        "medication_name": "Calcium & Vitamin D3",
        "dosage": "500 mg",
        "time_of_day": "Afternoon after lunch",
        "food_relation": "after food",
        "taken_today": True,
    },
]

# Knowledge base for Health Schemes
HEALTH_SCHEMES = {
    "AB_PMJAY": {
        "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
        "benefit": "Free health insurance coverage up to 5 Lakh Rupees per family per year for secondary and tertiary hospitalization.",
        "eligibility": "BPL card holders, SECC 2011 listed families, vulnerable occupational categories (laborers, rickshaw pullers, domestic workers).",
        "documents": "Aadhaar Card, Ration Card, PM-JAY Golden Card.",
        "helpline": "14555 or 1800-111-565",
    },
    "VAYA_VANDANA": {
        "name": "Ayushman Vaya Vandana Scheme",
        "benefit": "Free health coverage up to 5 Lakh Rupees per year specifically for ALL senior citizens aged 70 years and above, irrespective of income.",
        "eligibility": "All Indian citizens aged 70 years or older.",
        "documents": "Aadhaar Card with correct date of birth.",
        "helpline": "14555",
    },
    "JSY": {
        "name": "Janani Suraksha Yojana (JSY)",
        "benefit": "Cash assistance for pregnant women choosing institutional delivery: 1,400 Rupees in rural areas and 1,000 Rupees in urban areas, plus ASHA incentive.",
        "eligibility": "All pregnant women delivering in government health centers or accredited private hospitals, priority for BPL/SC/ST.",
        "documents": "Mother and Child Protection (MCP) Card, Aadhaar Card, Bank Account details.",
        "helpline": "104 or nearest PHC",
    },
    "PMMVY": {
        "name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
        "benefit": "Maternity benefit of 5,000 Rupees in installments for first living child, and 6,000 Rupees for second child if it is a girl child.",
        "eligibility": "Pregnant women and lactating mothers (except government employees).",
        "documents": "MCP Card, Aadhaar of mother and husband, Bank Account linked with Aadhaar.",
        "helpline": "1800-11-6555",
    },
    "NIKSHAY": {
        "name": "Nikshay Poshan Yojana (NTEP)",
        "benefit": "Financial support of 500 to 1,000 Rupees per month direct benefit transfer for nutritional support during Tuberculosis treatment.",
        "eligibility": "All notified Tuberculosis patients undergoing treatment.",
        "documents": "Nikshay ID, Bank account details, Aadhaar.",
        "helpline": "1800-11-6666",
    },
}

# Knowledge base for Medications
MEDICATION_DB = {
    "iron folic acid": "Take 1 tablet daily. Always swallow with water or orange juice rich in Vitamin C. DO NOT take with milk, tea, coffee, or calcium pills as they block iron absorption. Dark stools are normal and harmless.",
    "ifa": "Take 1 tablet daily with water or citrus juice. Avoid tea, coffee, milk, or calcium within 2 hours. Mild constipation or dark stools can occur.",
    "paracetamol": "Used for mild to moderate fever and body pain. Adult dose is typically 500mg to 650mg every 6 hours as needed. Do not exceed 4000mg in 24 hours. Safe in pregnancy under medical advice.",
    "calcium": "Take after meals with water. Do not take at the same time as Iron Folic Acid; keep at least a 2-hour gap between Calcium and Iron tablets.",
    "ors": "Oral Rehydration Salts. Dissolve 1 full packet in exactly 1 liter of clean drinking water. Sip continuously during diarrhea or dehydration. Use solution within 24 hours.",
    "zinc": "Zinc supplementation for children with diarrhea: 20mg daily for 14 full days (10mg for infants under 6 months) even if diarrhea stops early.",
    "amoxicillin": "Antibiotic. Take full course as prescribed by a medical doctor even if symptoms improve early. Take with or without food.",
    "dots": "Directly Observed Treatment Short-course for TB. Must be taken continuously without missing any doses for the full 6-month duration under health supervisor guidance.",
}


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def triage_symptoms(
        self,
        context: RunContext,
        symptoms: str,
        age: Optional[int] = None,
        is_pregnant: Optional[bool] = False,
        duration_days: Optional[int] = None,
    ) -> str:
        """Evaluate user symptoms and classify severity into Red (Emergency), Yellow (Urgent PHC visit), or Green (Routine home care).

        Args:
            symptoms: Description of symptoms reported by the patient (e.g., chest pain, high fever with stiff neck, cough for 3 weeks).
            age: Patient age in years.
            is_pregnant: Whether the patient is currently pregnant.
            duration_days: How many days symptoms have persisted.
        """
        logger.info(f"Triaging symptoms: {symptoms}, age={age}, pregnant={is_pregnant}")
        symptoms_lower = symptoms.lower()

        # Red Flags (Emergency)
        red_flags = [
            "chest pain", "difficulty breathing", "severe breathlessness", "unconscious",
            "fainting", "convulsion", "seizure", "stiff neck", "heavy bleeding",
            "coughing blood", "blue lips", "sudden paralysis", "slurred speech", "snake bite"
        ]

        # Maternal red flags
        maternal_red_flags = [
            "vaginal bleeding", "severe headache with blurred vision", "fits",
            "swelling of face and hands", "high fever", "decreased fetal movement", "water breaking early"
        ]

        is_red = any(rf in symptoms_lower for rf in red_flags)
        if is_pregnant and any(mrf in symptoms_lower for mrf in maternal_red_flags):
            is_red = True

        if age is not None and age < 1 and ("high fever" in symptoms_lower or "lethargy" in symptoms_lower or "unable to feed" in symptoms_lower):
            is_red = True

        if is_red:
            return (
                "TRIAGE ASSESSMENT: RED FLAG - EMERGENCY. "
                "The symptoms reported require immediate medical attention at the nearest emergency hospital or Community Health Centre. "
                "Please call 108 Emergency Ambulance service immediately or 102 for maternity transport. "
                "Do not delay seeking emergency care."
            )

        # Urgent Flags (Yellow)
        urgent_flags = [
            "fever for more than 3 days", "cough for more than 2 weeks", "blood in stool",
            "persistent vomiting", "severe belly pain", "pus from ear", "painful urination",
            "diarrhea for over 2 days", "unexplained weight loss"
        ]
        is_yellow = any(uf in symptoms_lower for uf in urgent_flags) or (duration_days and duration_days >= 3)

        if is_yellow:
            return (
                "TRIAGE ASSESSMENT: URGENT - PHC VISIT RECOMMENDED. "
                "Symptoms suggest a condition that needs clinical evaluation within 24 hours. "
                "Please visit your local Primary Health Centre (PHC) or consult an ASHA worker / doctor. "
                "Stay hydrated, rest, and watch for worsening symptoms like breathing difficulty or extreme weakness."
            )

        # Green Flag (Routine)
        return (
            "TRIAGE ASSESSMENT: ROUTINE - HOME CARE & MONITORING. "
            "Symptoms appear mild and can be managed with home care, adequate rest, fluids, and standard OTC remedies. "
            "If symptoms persist beyond 3 days or become more severe, please consult your nearest PHC doctor or ASHA worker. "
            "Please note: this guidance is for preliminary triage only and does not replace medical consultation."
        )

    @function_tool
    async def log_asha_home_visit(
        self,
        context: RunContext,
        patient_name: str,
        patient_type: str,
        vitals: Optional[str] = None,
        visit_notes: str = "",
        followup_date: Optional[str] = None,
    ) -> str:
        """Log a field home visit performed by an ASHA or ANM community health worker.

        Args:
            patient_name: Name of patient visited.
            patient_type: Type of patient (e.g. pregnant_woman, newborn, infant, elderly, chronic_illness, TB_patient).
            vitals: Vitals recorded (e.g. BP 120/80, Hb 10.5 g/dl, Weight 55kg, Temp 98.6F).
            visit_notes: Field notes on health status, counseling given, or supplements provided.
            followup_date: Scheduled date for next home visit or ANC checkup.
        """
        logger.info(f"Logging ASHA visit for {patient_name} ({patient_type})")
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "patient_name": patient_name,
            "patient_type": patient_type,
            "vitals": vitals or "Not recorded",
            "visit_notes": visit_notes,
            "followup_date": followup_date or "In 14 days",
        }
        ASHA_VISIT_LOGS.append(log_entry)

        # Check for High-Risk Pregnancy (HRP) indicators
        hrp_warning = ""
        vitals_lower = (vitals or "").lower()
        notes_lower = visit_notes.lower()
        if "pregnant" in patient_type.lower() or "anc" in notes_lower:
            if "hb" in vitals_lower:
                hrp_warning += " High-Risk Screening: Please ensure hemoglobin is above 11 g/dl to avoid severe anemia."
            if "bp" in vitals_lower:
                hrp_warning += " Monitor BP closely for pre-eclampsia flags if systolic is above 140 or diastolic above 90."

        return (
            f"Successfully recorded home visit log for {patient_name} ({patient_type}). "
            f"Vitals: {vitals or 'None'}. Notes saved: '{visit_notes}'. Next follow-up set for: {log_entry['followup_date']}.{hrp_warning}"
        )

    @function_tool
    async def get_asha_care_protocol(
        self,
        context: RunContext,
        topic: str,
    ) -> str:
        """Look up ASHA / ANM national health mission clinical care protocols and guidelines.

        Args:
            topic: Protocol topic, such as high_risk_pregnancy, immunization_schedule, diarrhea_management, malnutrition_sam, newborn_care, or anemia_ifa.
        """
        logger.info(f"Looking up ASHA protocol for {topic}")
        topic_lower = topic.lower()

        if "pregnancy" in topic_lower or "hrp" in topic_lower or "anc" in topic_lower:
            return (
                "ASHA GUIDELINE FOR ANTENATAL CARE (ANC) & HRP: "
                "Ensure minimum 4 ANC checkups during pregnancy. Check Hb, blood pressure, weight, and urine at every visit. "
                "Administer 2 Tetanus Toxoid (TT/Td) injections. Provide 180 Iron Folic Acid (IFA) tablets and 360 Calcium tablets. "
                "Screen for High-Risk Pregnancy flags: Hb below 7 g/dl (severe anemia), BP above 140/90, severe swelling, twin pregnancy, or past C-section. "
                "Refer HRP cases immediately to Medical Officer at CHC."
            )
        elif "immunization" in topic_lower or "vaccine" in topic_lower:
            return (
                "ASHA IMMUNIZATION SCHEDULE GUIDELINE: "
                "At Birth: BCG, OPV-0, Hepatitis B birth dose. "
                "At 6, 10, 14 Weeks: Pentavalent (DPT+HepB+Hib), OPV, Rotavirus, fIPV. "
                "At 9 Months: MR 1st dose, Vitamin A 1st dose, PCV booster. "
                "At 16-24 Months: MR 2nd dose, DPT 1st booster, OPV booster, Vitamin A 2nd dose. "
                "Ensure MCP Card entries are complete."
            )
        elif "diarrhea" in topic_lower or "ors" in topic_lower or "zinc" in topic_lower:
            return (
                "CHILDHOOD DIARRHEA MANAGEMENT PROTOCOL: "
                "1. Give ORS solution: 1 packet mixed in 1 liter clean drinking water. Give after every loose stool. "
                "2. Zinc Supplementation: 14-day full course of Zinc tablets (20mg daily for age 6 months+, 10mg daily for infants under 6 months). "
                "3. Continue breastfeeding and normal feeding. "
                "4. Refer to PHC immediately if child shows sunken eyes, severe thirst, extreme lethargy, or high fever."
            )
        elif "malnutrition" in topic_lower or "sam" in topic_lower or "mam" in topic_lower:
            return (
                "CHILD MALNUTRITION ASSESSMENT (SAM/MAM): "
                "Use MUAC (Mid-Upper Arm Circumference) tape on left arm for children 6 to 59 months. "
                "Red (below 11.5 cm) or bilateral edema: Severe Acute Malnutrition (SAM). Refer urgently to Nutrition Rehabilitation Centre (NRC). "
                "Yellow (11.5 cm to 12.5 cm): Moderate Acute Malnutrition (MAM). Provide Anganwadi supplementary nutrition (Take Home Ration) and weekly counseling. "
                "Green (above 12.5 cm): Normal growth."
            )
        else:
            return (
                "ASHA COMMUNITY HEALTH PROTOCOL: "
                "Focus on early identification, counseling, health education, MCP card updating, and timely referral to Primary Health Centres (PHC). "
                "Promote institutional deliveries, exclusive breastfeeding for 6 months, complementary feeding from 6 months, full immunization, and hygiene."
            )

    @function_tool
    async def manage_medication_reminder(
        self,
        context: RunContext,
        action: str,
        medication_name: Optional[str] = None,
        dosage: Optional[str] = None,
        time_of_day: Optional[str] = None,
        food_relation: Optional[str] = None,
    ) -> str:
        """Manage daily medication reminders and track adherence.

        Args:
            action: Action to perform: 'list' (view all reminders), 'add' (add new medication reminder), or 'mark_taken' (mark medication as taken today).
            medication_name: Name of medication (e.g. Iron Folic Acid, Metformin, Amlodipine).
            dosage: Dosage details (e.g. 1 tablet, 500mg).
            time_of_day: Scheduled timing (e.g. Morning, Afternoon, Night, 8 AM).
            food_relation: Meal instructions (e.g. after food, before food, with water).
        """
        logger.info(f"Managing medication reminder: action={action}, med={medication_name}")
        action_lower = action.lower()

        if "add" in action_lower:
            if not medication_name:
                return "Please specify the medication name to add a reminder."
            new_id = str(len(MEDICATION_REMINDERS) + 1)
            item = {
                "id": new_id,
                "medication_name": medication_name,
                "dosage": dosage or "1 dose",
                "time_of_day": time_of_day or "Daily morning",
                "food_relation": food_relation or "as advised by doctor",
                "taken_today": False,
            }
            MEDICATION_REMINDERS.append(item)
            return (
                f"Added medication reminder for {medication_name}, dosage {item['dosage']}, "
                f"scheduled for {item['time_of_day']} ({item['food_relation']})."
            )

        elif "taken" in action_lower or "mark" in action_lower:
            if not medication_name:
                return "Please specify which medication you have taken."
            for rem in MEDICATION_REMINDERS:
                if medication_name.lower() in rem["medication_name"].lower():
                    rem["taken_today"] = True
                    return f"Great job! Marked {rem['medication_name']} as taken for today. Keep maintaining good medication adherence."
            return f"Could not find medication matching '{medication_name}' in your active schedule."

        else:
            # List reminders
            if not MEDICATION_REMINDERS:
                return "You currently have no active medication reminders set."
            summary_list = []
            for r in MEDICATION_REMINDERS:
                status = "Taken today" if r.get("taken_today") else "Pending today"
                summary_list.append(f"{r['medication_name']} ({r['dosage']}) at {r['time_of_day']} [{status}]")
            return "Your current medication schedule: " + ", ".join(summary_list) + "."

    @function_tool
    async def check_medication_info(
        self,
        context: RunContext,
        medication_name: str,
    ) -> str:
        """Check safety instructions, food relations, and dosage rules for common medicines.

        Args:
            medication_name: Name of medication (e.g. IFA, Iron Folic Acid, Paracetamol, ORS, Calcium, DOTS TB medicine).
        """
        logger.info(f"Checking medication info for {medication_name}")
        med_lower = medication_name.lower()

        for key, info in MEDICATION_DB.items():
            if key in med_lower or med_lower in key:
                return f"MEDICATION GUIDANCE FOR {medication_name.upper()}: {info}"

        return (
            f"MEDICATION ADVISORY FOR {medication_name}: Always take medications strictly as prescribed by your doctor or PHC health supervisor. "
            "Take with clean drinking water and check expiry dates before consuming. "
            "If you experience side effects like dizziness, rash, or persistent nausea, consult your nearest health worker or doctor."
        )

    @function_tool
    async def check_scheme_eligibility(
        self,
        context: RunContext,
        scheme_name: Optional[str] = "ALL",
        income_category: Optional[str] = None,
        is_pregnant: Optional[bool] = False,
        age: Optional[int] = None,
    ) -> str:
        """Check eligibility rules, cash benefits, and registration details for government healthcare schemes (AB-PMJAY, JSY, PMMVY, Ayushman Vaya Vandana, Nikshay).

        Args:
            scheme_name: Scheme code or keyword (e.g. AB_PMJAY, JSY, PMMVY, VAYA_VANDANA, NIKSHAY, or ALL).
            income_category: Economic status (e.g., BPL, SECC, low_income, general).
            is_pregnant: Whether user or beneficiary is currently pregnant.
            age: Beneficiary age in years.
        """
        logger.info(f"Checking scheme eligibility: scheme={scheme_name}, age={age}, pregnant={is_pregnant}")
        scheme_key = (scheme_name or "ALL").upper()

        results = []

        # Ayushman Vaya Vandana for seniors 70+
        if age is not None and age >= 70:
            vaya = HEALTH_SCHEMES["VAYA_VANDANA"]
            results.append(f"ELIGIBLE FOR {vaya['name']}: {vaya['benefit']} All senior citizens 70+ qualify automatically regardless of income. Required doc: Aadhaar.")

        # Ayushman Bharat PM-JAY
        if (
            "AB" in scheme_key or "PMJAY" in scheme_key or "AYUSHMAN" in scheme_key or scheme_key == "ALL"
        ) and ((income_category and "BPL" in income_category.upper()) or age is None or age < 70):
            ab = HEALTH_SCHEMES["AB_PMJAY"]
            results.append(f"{ab['name']}: {ab['benefit']} Eligibility: {ab['eligibility']} Helpline: {ab['helpline']}.")

        # Janani Suraksha Yojana & PMMVY for pregnant women
        if is_pregnant or "JSY" in scheme_key or "PMMVY" in scheme_key or "MATERNITY" in scheme_key:
            jsy = HEALTH_SCHEMES["JSY"]
            pmmvy = HEALTH_SCHEMES["PMMVY"]
            results.append(f"{jsy['name']}: {jsy['benefit']} Required docs: {jsy['documents']}.")
            results.append(f"{pmmvy['name']}: {pmmvy['benefit']} Required docs: {pmmvy['documents']}.")

        # Nikshay Poshan for TB
        if "NIKSHAY" in scheme_key or "TB" in scheme_key:
            nik = HEALTH_SCHEMES["NIKSHAY"]
            results.append(f"{nik['name']}: {nik['benefit']} Eligibility: {nik['eligibility']}.")

        if not results:
            results.append(
                "You may check eligibility at your local Ayushman Bharat Arogya Mandir, PHC, or Gram Panchayat office with your Ration Card and Aadhaar Card."
            )

        return "GOVERNMENT HEALTH SCHEME ADVISORY: " + " ".join(results)

    @function_tool
    async def lookup_facility_info(
        self,
        context: RunContext,
        facility_type: str,
        district: Optional[str] = None,
    ) -> str:
        """Find contact helplines, emergency numbers, and services available at local health facilities (PHC, CHC, District Hospital, Ambulance).

        Args:
            facility_type: Facility or service type (e.g. Ambulance, PHC, CHC, District Hospital, Tele-MANAS, Women Helpline).
            district: District or locality name.
        """
        logger.info(f"Looking up facility info: {facility_type}, district={district}")
        fac_lower = facility_type.lower()
        dist_str = f" in {district}" if district else ""

        if "ambulance" in fac_lower or "emergency" in fac_lower:
            return (
                f"EMERGENCY HELPLINES{dist_str}: "
                "Dial 108 for Emergency Medical Response Service (24x7 Ambulance with paramedic). "
                "Dial 102 for Free Referral Transport for pregnant mothers and sick infants. "
                "Dial 104 for Health Information & Advice Helpline."
            )
        elif "mental" in fac_lower or "tele-manas" in fac_lower or "counseling" in fac_lower:
            return (
                "MENTAL HEALTH HELPLINE: "
                "Dial 14477 or 1800-891-4477 for Tele-MANAS (24x7 free national mental health counseling support in multiple languages)."
            )
        elif "phc" in fac_lower or "chc" in fac_lower or "sub-centre" in fac_lower:
            return (
                f"PRIMARY HEALTH CENTRE (PHC) SERVICES{dist_str}: "
                "Open daily 9:00 AM to 4:00 PM. Services provided free of cost: General OPD, Free diagnostic tests (Hb, malaria, blood sugar), "
                "Free Essential Medicines, ANC checkups, Routine Immunization, and Referral to District Hospital."
            )
        else:
            return (
                f"HEALTHCARE FACILITY DIRECTORY{dist_str}: "
                "Visit your nearest Ayushman Bharat Arogya Mandir (Health & Wellness Centre) or Community Health Centre (CHC). "
                "For 24/7 emergency transport call 108."
            )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="Anisha",
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    hindi_keywords = {
        "namaste", "namaskar", "kya", "hai", "haan", "nahi",
        "main", "mera", "meri", "mujhe", "aap", "tum",
        "doctor", "hospital", "appointment", "dawai",
        "bukhar", "khansi", "sardi", "dard", "madad"
    }

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev):
        transcript = ev.transcript.strip().lower()

        has_devanagari = any(
            0x0900 <= ord(c) <= 0x097F
            for c in transcript
        )

        words = set(transcript.split())
        has_hindi_words = not words.isdisjoint(hindi_keywords)

        if has_devanagari or has_hindi_words:
            session.tts.update_options(
                voice="hi-IN-anisha"
            )
        else:
            session.tts.update_options(
                voice="en-IN-anisha"
            )

    await session.start(
        agent=Assistant(),
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



if __name__ == "__main__":
    cli.run_app(server)

