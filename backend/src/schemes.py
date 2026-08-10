"""Local scheme dataset + eligibility / document helpers for Jan Sahay.

DATA SOURCE (Day 5):
  Hand-built local dataset compiled from publicly documented parameters of
  major Indian financial-inclusion schemes (PMJDY, PMSBY, PMJJBY, APY).
  No live government API is used — India scheme portals do not expose a
  free, stable public eligibility API suitable for voice agents.
  Parameters are labelled with ``data_as_of`` so the agent can say the
  vintage out loud. Confirm latest figures at the bank branch / official
  portal before applying.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("agent.schemes")

# Vintage stamp — update when you refresh scheme numbers from official sources.
DATA_AS_OF = "2025-04 (local hand-built dataset from public scheme summaries)"
DATA_SOURCE = (
    "Local hand-built dataset (not a live government API). "
    "Figures cross-checked against public PMJDY / PMSBY / PMJJBY / APY summaries. "
    "Always reconfirm at bank branch, CSC, or the official portal before applying."
)

# Canonical scheme registry keyed by short code.
SCHEMES: dict[str, dict[str, Any]] = {
    "pmjdy": {
        "code": "pmjdy",
        "short_name": "PMJDY",
        "full_name": "Pradhan Mantri Jan Dhan Yojana",
        "hindi_name": "प्रधानमंत्री जन धन योजना",
        "category": "zero_balance_bank_account",
        "summary": (
            "Zero-balance savings account for every Indian household, with "
            "RuPay debit card, accidental insurance cover, and overdraft facility "
            "after satisfactory operation."
        ),
        "eligibility": {
            "min_age": 10,  # minor accounts with guardian; adult account typically 18+
            "adult_age": 18,
            "max_age": None,
            "citizen_or_resident": True,
            "requires_existing_account": False,
            "income_cap_monthly_inr": None,
            "notes": (
                "Any Indian citizen or eligible resident without a full-KYC savings "
                "account can open one. Minors 10+ may open with guardian support."
            ),
        },
        "benefits": [
            "Zero-balance savings account",
            "RuPay debit card",
            "Accident insurance cover on RuPay card (amount varies by issuance year)",
            "Overdraft facility after satisfactory account operation (bank discretion)",
        ],
        "documents": [
            {
                "id": "identity_proof",
                "name_en": "Identity proof (Aadhaar / Voter ID / Passport / Driving Licence)",
                "name_hi": "पहचान प्रमाण (आधार / वोटर आईडी / पासपोर्ट / ड्राइविंग लाइसेंस)",
                "required": True,
            },
            {
                "id": "address_proof",
                "name_en": "Address proof (Aadhaar / utility bill / passport)",
                "name_hi": "पता प्रमाण (आधार / यूटिलिटी बिल / पासपोर्ट)",
                "required": True,
            },
            {
                "id": "photo",
                "name_en": "Passport-size photograph",
                "name_hi": "पासपोर्ट साइज़ फोटो",
                "required": True,
            },
            {
                "id": "guardian_docs",
                "name_en": "Guardian ID + consent (only if applicant is a minor)",
                "name_hi": "अभिभावक का पहचान पत्र और सहमति (केवल नाबालिग आवेदक के लिए)",
                "required": False,
            },
        ],
        "where_to_apply": "Any bank branch, Business Correspondent (BC), or CSC",
        "official_hint": "https://pmjdy.gov.in / your bank branch",
    },
    "pmsby": {
        "code": "pmsby",
        "short_name": "PMSBY",
        "full_name": "Pradhan Mantri Suraksha Bima Yojana",
        "hindi_name": "प्रधानमंत्री सुरक्षा बीमा योजना",
        "category": "accident_insurance",
        "summary": (
            "Low-premium accidental death and disability insurance linked to a "
            "bank account. Annual premium auto-debited around 1 June."
        ),
        "eligibility": {
            "min_age": 18,
            "max_age": 70,
            "requires_bank_account": True,
            "requires_existing_account": True,
            "income_cap_monthly_inr": None,
            "annual_premium_inr": 20,
            "cover_death_inr": 200_000,
            "cover_disability_full_inr": 200_000,
            "cover_disability_partial_inr": 100_000,
            "notes": (
                "Age 18-70 with a savings bank account. One person, one cover. "
                "Premium ~₹20/year (confirm current premium with bank)."
            ),
        },
        "benefits": [
            "₹2 lakh on accidental death",
            "₹2 lakh on total permanent disability",
            "₹1 lakh on partial permanent disability",
        ],
        "documents": [
            {
                "id": "bank_account",
                "name_en": "Active savings bank account (auto-debit of premium)",
                "name_hi": "सक्रिय बचत खाता (प्रीमियम ऑटो-डेबिट के लिए)",
                "required": True,
            },
            {
                "id": "aadhaar_or_kyc",
                "name_en": "Aadhaar or other KYC already linked to the bank account",
                "name_hi": "खाते से जुड़ा आधार या अन्य KYC",
                "required": True,
            },
            {
                "id": "consent_form",
                "name_en": "PMSBY enrolment / auto-debit consent form at bank or BC",
                "name_hi": "बैंक या BC पर PMSBY नामांकन / ऑटो-डेबिट सहमति फॉर्म",
                "required": True,
            },
            {
                "id": "nominee",
                "name_en": "Nominee details (name + relationship)",
                "name_hi": "नामांकित व्यक्ति का नाम और संबंध",
                "required": True,
            },
        ],
        "where_to_apply": "Bank branch, net banking, or Business Correspondent",
        "official_hint": "Your bank / https://www.jansuraksha.gov.in",
    },
    "pmjjby": {
        "code": "pmjjby",
        "short_name": "PMJJBY",
        "full_name": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "hindi_name": "प्रधानमंत्री जीवन ज्योति बीमा योजना",
        "category": "life_insurance",
        "summary": (
            "Low-premium life insurance (any-cause death cover) linked to a bank "
            "account. Annual premium auto-debited around 1 June."
        ),
        "eligibility": {
            "min_age": 18,
            "max_age": 50,  # join by 50; cover can continue to 55 with renewal
            "cover_continues_to": 55,
            "requires_bank_account": True,
            "requires_existing_account": True,
            "income_cap_monthly_inr": None,
            "annual_premium_inr": 436,
            "cover_death_inr": 200_000,
            "notes": (
                "Join between ages 18-50. Cover continues up to 55 if renewed. "
                "Premium ~₹436/year (confirm current premium with bank). "
                "Death cover for any cause (with standard exclusions)."
            ),
        },
        "benefits": [
            "₹2 lakh life cover on death (any cause, subject to scheme exclusions)",
        ],
        "documents": [
            {
                "id": "bank_account",
                "name_en": "Active savings bank account (auto-debit of premium)",
                "name_hi": "सक्रिय बचत खाता (प्रीमियम ऑटो-डेबिट के लिए)",
                "required": True,
            },
            {
                "id": "aadhaar_or_kyc",
                "name_en": "Aadhaar or other KYC already linked to the bank account",
                "name_hi": "खाते से जुड़ा आधार या अन्य KYC",
                "required": True,
            },
            {
                "id": "consent_form",
                "name_en": "PMJJBY enrolment / auto-debit consent form + good-health declaration",
                "name_hi": "PMJJBY नामांकन फॉर्म और स्वास्थ्य घोषणा",
                "required": True,
            },
            {
                "id": "nominee",
                "name_en": "Nominee details (name + relationship)",
                "name_hi": "नामांकित व्यक्ति का नाम और संबंध",
                "required": True,
            },
            {
                "id": "age_proof",
                "name_en": "Age proof if bank does not already have it on file",
                "name_hi": "आयु प्रमाण (यदि बैंक के पास पहले से न हो)",
                "required": False,
            },
        ],
        "where_to_apply": "Bank branch, net banking, or Business Correspondent",
        "official_hint": "Your bank / https://www.jansuraksha.gov.in",
    },
    "apy": {
        "code": "apy",
        "short_name": "APY",
        "full_name": "Atal Pension Yojana",
        "hindi_name": "अटल पेंशन योजना",
        "category": "pension",
        "summary": (
            "Government co-contributed pension scheme for workers in the "
            "unorganised sector. Guaranteed pension of ₹1,000-₹5,000 per month "
            "from age 60, based on contribution tier chosen."
        ),
        "eligibility": {
            "min_age": 18,
            "max_age": 40,
            "requires_bank_account": True,
            "requires_existing_account": True,
            "income_cap_monthly_inr": None,
            "pension_options_inr": [1000, 2000, 3000, 4000, 5000],
            "notes": (
                "Age 18-40 with a savings bank account. Primarily aimed at "
                "unorganised-sector workers. Contribution amount depends on "
                "entry age and chosen pension tier."
            ),
        },
        "benefits": [
            "Guaranteed monthly pension ₹1,000-₹5,000 from age 60",
            "Spouse continues to receive pension after subscriber's death (as per rules)",
            "Return of corpus to nominee on death of both subscriber and spouse",
        ],
        "documents": [
            {
                "id": "bank_account",
                "name_en": "Active savings bank account for auto-debit of contribution",
                "name_hi": "सक्रिय बचत खाता (योगदान ऑटो-डेबिट)",
                "required": True,
            },
            {
                "id": "aadhaar",
                "name_en": "Aadhaar number (for e-KYC / seeding)",
                "name_hi": "आधार नंबर (e-KYC / सीडिंग)",
                "required": True,
            },
            {
                "id": "mobile",
                "name_en": "Registered mobile number linked to bank account",
                "name_hi": "बैंक खाते से जुड़ा मोबाइल नंबर",
                "required": True,
            },
            {
                "id": "age_proof",
                "name_en": "Age / date-of-birth proof",
                "name_hi": "आयु / जन्मतिथि प्रमाण",
                "required": True,
            },
            {
                "id": "nominee",
                "name_en": "Nominee and spouse details",
                "name_hi": "नामांकित व्यक्ति और पति/पत्नी का विवरण",
                "required": True,
            },
            {
                "id": "form",
                "name_en": "APY subscription form at bank / post office",
                "name_hi": "बैंक / पोस्ट ऑफिस पर APY सब्सक्रिप्शन फॉर्म",
                "required": True,
            },
        ],
        "where_to_apply": "Bank branch, post office, or net banking where offered",
        "official_hint": "Your bank / https://www.npscra.nsdl.co.in (APY section)",
    },
}

# Friendly aliases the LLM / STT may produce.
_SCHEME_ALIASES: dict[str, str] = {
    "pmjdy": "pmjdy",
    "jan dhan": "pmjdy",
    "jandhan": "pmjdy",
    "jan dhan yojana": "pmjdy",
    "pradhan mantri jan dhan": "pmjdy",
    "pradhan mantri jan dhan yojana": "pmjdy",
    "जन धन": "pmjdy",
    "जनधन": "pmjdy",
    "pmsby": "pmsby",
    "suraksha bima": "pmsby",
    "suraksha beema": "pmsby",
    "accident insurance": "pmsby",
    "pradhan mantri suraksha bima": "pmsby",
    "प्रधानमंत्री सुरक्षा बीमा": "pmsby",
    "सुरक्षा बीमा": "pmsby",
    "pmjjby": "pmjjby",
    "jeevan jyoti": "pmjjby",
    "jeevan jyoti bima": "pmjjby",
    "life insurance": "pmjjby",
    "pradhan mantri jeevan jyoti": "pmjjby",
    "जीवन ज्योति": "pmjjby",
    "apy": "apy",
    "atal pension": "apy",
    "atal pension yojana": "apy",
    "pension yojana": "apy",
    "अटल पेंशन": "apy",
    "पेंशन योजना": "apy",
}


def resolve_scheme_code(scheme_name: str) -> str | None:
    """Map free-text scheme name to a canonical code, or None if unknown."""
    raw = (scheme_name or "").strip().lower()
    if not raw:
        return None
    if raw in SCHEMES:
        return raw
    # Direct alias
    if raw in _SCHEME_ALIASES:
        return _SCHEME_ALIASES[raw]
    # Substring / contains match (longest alias first to avoid weak hits)
    for alias in sorted(_SCHEME_ALIASES.keys(), key=len, reverse=True):
        if alias in raw or raw in alias:
            return _SCHEME_ALIASES[alias]
    return None


def list_supported_schemes() -> list[str]:
    return [s["short_name"] for s in SCHEMES.values()]


def _meta() -> dict[str, str]:
    return {
        "data_as_of": DATA_AS_OF,
        "data_source": DATA_SOURCE,
        "checked_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def check_eligibility(
    scheme_name: str,
    age: int | None = None,
    has_bank_account: bool | None = None,
    is_indian_resident: bool | None = None,
    monthly_income_inr: int | None = None,
    already_has_scheme: bool | None = None,
) -> dict[str, Any]:
    """Evaluate rough eligibility from collected answers.

    Returns a structured result the agent can speak. Never invents approval —
    status is informational only. On unknown scheme or bad inputs, returns a
    failure payload the agent must read out loud (no silent fail).
    """
    meta = _meta()
    code = resolve_scheme_code(scheme_name)
    if not code:
        return {
            "ok": False,
            "error": "unknown_scheme",
            "message": (
                f"I could not match '{scheme_name}' to a scheme I know. "
                f"I can check: {', '.join(list_supported_schemes())}."
            ),
            "supported_schemes": list_supported_schemes(),
            **meta,
        }

    scheme = SCHEMES[code]
    rules = scheme["eligibility"]
    reasons: list[str] = []
    blockers: list[str] = []
    missing: list[str] = []

    # Age checks
    if age is None:
        missing.append("age")
    else:
        try:
            age_i = int(age)
        except (TypeError, ValueError):
            return {
                "ok": False,
                "error": "invalid_age",
                "message": (
                    "Age must be a whole number in years. "
                    "Please ask the caller their age again."
                ),
                **meta,
            }
        if age_i < 0 or age_i > 120:
            return {
                "ok": False,
                "error": "invalid_age",
                "message": "That age does not look valid. Please re-confirm the caller's age.",
                **meta,
            }
        min_age = rules.get("min_age")
        max_age = rules.get("max_age")
        if min_age is not None and age_i < min_age:
            blockers.append(
                f"Minimum age for {scheme['short_name']} is {min_age}; caller is {age_i}."
            )
        elif max_age is not None and age_i > max_age:
            blockers.append(
                f"Maximum joining age for {scheme['short_name']} is {max_age}; "
                f"caller is {age_i}."
            )
        else:
            reasons.append(f"Age {age_i} is within the scheme age band.")

    # Bank account
    if rules.get("requires_bank_account") or rules.get("requires_existing_account"):
        if has_bank_account is None:
            missing.append("has_bank_account")
        elif has_bank_account is False:
            blockers.append(
                f"{scheme['short_name']} needs an active savings bank account "
                "for enrolment / auto-debit."
            )
        else:
            reasons.append("Caller has a bank account.")

    # Residency / citizenship (mainly PMJDY)
    if rules.get("citizen_or_resident"):
        if is_indian_resident is None:
            missing.append("is_indian_resident")
        elif is_indian_resident is False:
            blockers.append(
                f"{scheme['short_name']} is intended for Indian citizens / eligible residents."
            )
        else:
            reasons.append("Caller is an Indian resident / citizen.")

    # Income cap (none of the current four hard-cap, but keep the hook)
    cap = rules.get("income_cap_monthly_inr")
    if cap is not None and monthly_income_inr is not None:
        if monthly_income_inr > cap:
            blockers.append(
                f"Monthly income ₹{monthly_income_inr} is above the scheme cap of ₹{cap}."
            )
        else:
            reasons.append(f"Income within cap (₹{cap}/month).")

    if already_has_scheme is True:
        reasons.append(
            f"Caller says they already have {scheme['short_name']} — "
            "confirm with the bank; duplicate cover is usually not needed."
        )

    # Decide status
    if blockers:
        status = "likely_not_eligible"
        speak = (
            f"Based on the answers given, the caller is likely NOT eligible for "
            f"{scheme['short_name']} ({scheme['full_name']}). "
            + " ".join(blockers)
            + f" Data as of {DATA_AS_OF}. This is guidance only — the bank or "
            "government decides final eligibility."
        )
    elif missing:
        status = "need_more_info"
        speak = (
            f"I need a few more answers before I can check {scheme['short_name']}: "
            f"{', '.join(missing)}. Ask these one at a time, then call this tool again."
        )
    else:
        status = "likely_eligible"
        speak = (
            f"Based on the answers given, the caller appears LIKELY ELIGIBLE for "
            f"{scheme['short_name']} ({scheme['full_name']}). "
            + (" ".join(reasons) + " " if reasons else "")
            + f"Premium/cover notes: {rules.get('notes', '')} "
            f"Data as of {DATA_AS_OF}. Final approval is only by the bank or government — "
            "never promise enrolment success."
        )

    return {
        "ok": True,
        "status": status,
        "scheme_code": code,
        "scheme_short_name": scheme["short_name"],
        "scheme_full_name": scheme["full_name"],
        "reasons": reasons,
        "blockers": blockers,
        "missing_fields": missing,
        "speak_summary": speak,
        "where_to_apply": scheme["where_to_apply"],
        "disclaimer": (
            "Informational only. Not a guarantee of approval. "
            "Bank / government decides."
        ),
        **meta,
    }


def get_document_checklist(scheme_name: str) -> dict[str, Any]:
    """Return the document checklist for a scheme, with data vintage."""
    meta = _meta()
    code = resolve_scheme_code(scheme_name)
    if not code:
        return {
            "ok": False,
            "error": "unknown_scheme",
            "message": (
                f"I could not match '{scheme_name}' to a scheme I know. "
                f"I can list documents for: {', '.join(list_supported_schemes())}."
            ),
            "supported_schemes": list_supported_schemes(),
            **meta,
        }

    scheme = SCHEMES[code]
    required = [d for d in scheme["documents"] if d.get("required")]
    optional = [d for d in scheme["documents"] if not d.get("required")]

    required_names = [d["name_en"] for d in required]
    optional_names = [d["name_en"] for d in optional]

    speak_parts = [
        f"For {scheme['short_name']} ({scheme['full_name']}), typically carry: "
        + "; ".join(required_names)
        + "."
    ]
    if optional_names:
        speak_parts.append(
            "Also useful if applicable: " + "; ".join(optional_names) + "."
        )
    speak_parts.append(
        f"Apply at: {scheme['where_to_apply']}. "
        f"Document list as of {DATA_AS_OF}. "
        "Banks may ask for extra KYC — confirm at the branch."
    )

    return {
        "ok": True,
        "scheme_code": code,
        "scheme_short_name": scheme["short_name"],
        "scheme_full_name": scheme["full_name"],
        "required_documents": required,
        "optional_documents": optional,
        "where_to_apply": scheme["where_to_apply"],
        "official_hint": scheme["official_hint"],
        "speak_summary": " ".join(speak_parts),
        **meta,
    }


def get_scheme_overview(scheme_name: str) -> dict[str, Any]:
    """Compact scheme facts (premium, cover, age band) with vintage stamp."""
    meta = _meta()
    code = resolve_scheme_code(scheme_name)
    if not code:
        return {
            "ok": False,
            "error": "unknown_scheme",
            "message": (
                f"Unknown scheme '{scheme_name}'. "
                f"Supported: {', '.join(list_supported_schemes())}."
            ),
            "supported_schemes": list_supported_schemes(),
            **meta,
        }
    scheme = SCHEMES[code]
    rules = scheme["eligibility"]
    return {
        "ok": True,
        "scheme_code": code,
        "scheme_short_name": scheme["short_name"],
        "scheme_full_name": scheme["full_name"],
        "hindi_name": scheme["hindi_name"],
        "summary": scheme["summary"],
        "eligibility_notes": rules.get("notes"),
        "min_age": rules.get("min_age"),
        "max_age": rules.get("max_age"),
        "annual_premium_inr": rules.get("annual_premium_inr"),
        "benefits": scheme["benefits"],
        "where_to_apply": scheme["where_to_apply"],
        "speak_summary": (
            f"{scheme['short_name']}: {scheme['summary']} "
            f"Notes: {rules.get('notes', '')} "
            f"Data as of {DATA_AS_OF}."
        ),
        **meta,
    }
