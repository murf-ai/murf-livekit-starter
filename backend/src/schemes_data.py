"""Indian Financial Services Scheme Dataset and Eligibility Checker Engine.

Data Source Notice:
Uses a curated dataset based on official Indian Government scheme guidelines (PMJDY, PMSBY, PMJJBY, APY, SSY, PM-KISAN, PMMY).
Updated and effective as of August 2026.
"""

from typing import Any

DATA_TIMESTAMP = "August 2026 (Official FY 2026-27 Government Guidelines)"

SCHEMES_DB: dict[str, dict[str, Any]] = {
    "pmjdy": {
        "scheme_id": "pmjdy",
        "full_name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "category": "Banking & Financial Inclusion",
        "description": "National Mission for Financial Inclusion providing zero-balance savings bank accounts.",
        "min_age": 10,
        "max_age": 100,
        "max_income": None,
        "taxpayer_allowed": True,
        "target_gender": "all",
        "requires_land": False,
        "benefits": "Zero balance account, free RuPay debit card, ₹2 Lakh accidental insurance, ₹10,000 overdraft facility.",
        "document_checklist": [
            "Aadhaar Card (or official valid proof like Voter ID, Passport, or Driving License)",
            "2 passport-sized photographs",
            "Proof of address (if Aadhaar address is not current)",
        ],
        "application_process": "Visit any commercial bank branch, Bank Mitra, or Post Office Bank to submit the PMJDY account opening form.",
    },
    "pmsby": {
        "scheme_id": "pmsby",
        "full_name": "Pradhan Mantri Suraksha Bima Yojana (PMSBY)",
        "category": "Accident Insurance",
        "description": "Government-backed accidental death and disability insurance scheme with ₹20 annual premium.",
        "min_age": 18,
        "max_age": 70,
        "max_income": None,
        "taxpayer_allowed": True,
        "target_gender": "all",
        "requires_land": False,
        "benefits": "₹2 Lakh for accidental death or total disability, ₹1 Lakh for partial disability.",
        "document_checklist": [
            "Aadhaar Card linked to bank account",
            "Savings bank account details",
            "Auto-debit authorization consent form",
            "Nominee details and ID proof",
        ],
        "application_process": "Submit consent form at your bank branch or activate through net banking / mobile banking app.",
    },
    "pmjjby": {
        "scheme_id": "pmjjby",
        "full_name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "category": "Life Insurance",
        "description": "Renewable one-year term life insurance scheme offering ₹2 Lakh cover for ₹436 annual premium.",
        "min_age": 18,
        "max_age": 50,
        "max_income": None,
        "taxpayer_allowed": True,
        "target_gender": "all",
        "requires_land": False,
        "benefits": "₹2 Lakh life insurance benefit payable to nominee on subscriber death due to any cause.",
        "document_checklist": [
            "Aadhaar Card",
            "Savings bank account details",
            "Self-declaration of good health form",
            "Nominee full name and relation details",
        ],
        "application_process": "Fill out consent form at participating bank branch or enable auto-debit via bank portal.",
    },
    "apy": {
        "scheme_id": "apy",
        "full_name": "Atal Pension Yojana (APY)",
        "category": "Pension & Retirement",
        "description": "Guaranteed pension scheme targeting workers in the unorganized sector.",
        "min_age": 18,
        "max_age": 40,
        "max_income": None,
        "taxpayer_allowed": False,  # Income tax payers are not eligible since Oct 2022
        "target_gender": "all",
        "requires_land": False,
        "benefits": "Guaranteed monthly pension of ₹1,000 to ₹5,000 after age 60 based on contribution.",
        "document_checklist": [
            "Aadhaar Card",
            "Active savings bank account or post office account details",
            "Mobile number registered with bank",
            "Spouse and nominee details",
        ],
        "application_process": "Fill APY registration form at your bank or register online through bank internet banking.",
    },
    "ssy": {
        "scheme_id": "ssy",
        "full_name": "Sukanya Samriddhi Yojana (SSY)",
        "category": "Girl Child Welfare & Savings",
        "description": "Small deposit savings scheme for girl child with attractive interest rate and tax benefit.",
        "min_age": 0,
        "max_age": 10,  # Girl child must be under 10 years at account opening
        "max_income": None,
        "taxpayer_allowed": True,
        "target_gender": "female",
        "requires_land": False,
        "benefits": "High tax-free interest rate (~8.2% p.a.), account matures at 21 years or on girl's marriage after age 18.",
        "document_checklist": [
            "Birth certificate of the girl child",
            "Identity proof of parent/guardian (Aadhaar, PAN, or Passport)",
            "Address proof of parent/guardian",
            "Passport photos of girl child and parent",
        ],
        "application_process": "Visit any designated post office or authorized commercial bank branch with the documents.",
    },
    "pm_kisan": {
        "scheme_id": "pm_kisan",
        "full_name": "PM Kisan Samman Nidhi (PM-KISAN)",
        "category": "Agriculture & Farmer Welfare",
        "description": "Direct income support of ₹6,000 per year to land-holding farmer families.",
        "min_age": 18,
        "max_age": 100,
        "max_income": None,
        "taxpayer_allowed": False,  # Institutional landholders & IT payers excluded
        "target_gender": "all",
        "requires_land": True,
        "benefits": "₹6,000 per year transferred directly in 3 equal installments of ₹2,000 into Aadhaar-seeded bank account.",
        "document_checklist": [
            "Aadhaar Card (e-KYC mandatory)",
            "Cultivable land ownership document (RoR / Khatoni copy)",
            "Aadhaar-seeded savings bank account details",
            "Active mobile number",
        ],
        "application_process": "Apply via PM-KISAN portal (pmkisan.gov.in), PM-Kisan mobile app, or nearest Common Service Centre (CSC).",
    },
    "pmmy": {
        "scheme_id": "pmmy",
        "full_name": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "category": "Business & Micro-Enterprise Loan",
        "description": "Collateral-free business loans up to ₹10 Lakhs for micro and small enterprises.",
        "min_age": 18,
        "max_age": 65,
        "max_income": None,
        "taxpayer_allowed": True,
        "target_gender": "all",
        "requires_land": False,
        "benefits": "Collateral-free loans across 3 categories: Shishu (up to ₹50k), Kishore (₹50k-₹5L), Tarun (₹5L-₹10L).",
        "document_checklist": [
            "Aadhaar Card and PAN Card",
            "Proof of business address (Electricity bill, Trade License, Rent agreement)",
            "Applicant photo (2 copies)",
            "Quotations/Invoices for equipment/inventory to be purchased",
            "Bank account statement for past 6 months (if existing business)",
        ],
        "application_process": "Apply at any bank branch, NBFC, Microfinance institution, or online via udyamimitra.in portal.",
    },
}


def list_all_schemes() -> dict[str, Any]:
    """Returns a list of all available scheme titles, IDs, and categories."""
    try:
        schemes_summary = [
            {
                "scheme_id": s["scheme_id"],
                "full_name": s["full_name"],
                "category": s["category"],
                "short_description": s["description"],
            }
            for s in SCHEMES_DB.values()
        ]
        return {
            "status": "success",
            "as_of_date": DATA_TIMESTAMP,
            "total_schemes": len(schemes_summary),
            "schemes": schemes_summary,
        }
    except Exception as e:
        return {
            "status": "error",
            "as_of_date": DATA_TIMESTAMP,
            "error_message": f"SYSTEM_FAILURE: Unable to read scheme database due to technical error: {e}. Please state out loud that dataset is temporarily unavailable and offer standard assistance.",
        }


def evaluate_eligibility(
    scheme_id: str,
    age: int | None = None,
    annual_income: float | None = None,
    is_taxpayer: bool | None = None,
    gender: str | None = None,
    land_holding_acres: float | None = None,
    simulate_failure: bool = False,
) -> dict[str, Any]:
    """Evaluates applicant eligibility against official scheme criteria."""
    if simulate_failure:
        return {
            "status": "error",
            "as_of_date": DATA_TIMESTAMP,
            "error_message": "OUT_LOUD_FAILURE: Database connection timed out while querying scheme rules. Please inform the user out loud: 'I am experiencing a temporary connection delay accessing the official scheme database. I can explain general requirements from memory or retry.'",
        }

    key = scheme_id.strip().lower()
    if key not in SCHEMES_DB:
        available_ids = ", ".join(SCHEMES_DB.keys())
        return {
            "status": "error",
            "as_of_date": DATA_TIMESTAMP,
            "error_message": f"OUT_LOUD_FAILURE: Scheme '{scheme_id}' was not found in our records. Available scheme codes are: {available_ids}. Please inform the user out loud that the requested scheme is not found and mention available schemes.",
        }

    scheme = SCHEMES_DB[key]
    reasons: list[str] = []
    eligible = True

    # 1. Age check
    if age is not None:
        if age < scheme["min_age"]:
            eligible = False
            reasons.append(
                f"Applicant age ({age} years) is below minimum required age of {scheme['min_age']} years."
            )
        elif age > scheme["max_age"]:
            eligible = False
            reasons.append(
                f"Applicant age ({age} years) exceeds maximum allowed age of {scheme['max_age']} years."
            )

    # 2. Taxpayer check
    if is_taxpayer is True and not scheme["taxpayer_allowed"]:
        eligible = False
        reasons.append(
            f"Income tax payers are not eligible for {scheme['full_name']} according to official guidelines."
        )

    # 3. Gender check
    if (
        gender
        and scheme["target_gender"] != "all"
        and gender.strip().lower() != scheme["target_gender"]
    ):
        eligible = False
        reasons.append(
            f"This scheme is exclusively for {scheme['target_gender']} applicants."
        )

    # 4. Land holding check
    if scheme["requires_land"] and (
        land_holding_acres is None or land_holding_acres <= 0
    ):
        eligible = False
        reasons.append(
            f"{scheme['full_name']} requires cultivable land ownership. No land holding was recorded."
        )

    if eligible:
        status_text = "ELIGIBLE"
        conclusion = (
            f"The applicant meets all primary criteria for {scheme['full_name']}."
        )
    else:
        status_text = "NOT_ELIGIBLE"
        conclusion = (
            f"The applicant does NOT meet eligibility criteria for {scheme['full_name']} due to: "
            + " ".join(reasons)
        )

    return {
        "status": "success",
        "as_of_date": DATA_TIMESTAMP,
        "scheme_id": scheme["scheme_id"],
        "scheme_name": scheme["full_name"],
        "eligibility_status": status_text,
        "is_eligible": eligible,
        "reasons": reasons,
        "conclusion": conclusion,
        "benefits": scheme["benefits"],
        "application_process": scheme["application_process"],
    }


def get_document_checklist(
    scheme_id: str, simulate_failure: bool = False
) -> dict[str, Any]:
    """Retrieves document checklist for a scheme."""
    if simulate_failure:
        return {
            "status": "error",
            "as_of_date": DATA_TIMESTAMP,
            "error_message": "OUT_LOUD_FAILURE: System timed out while retrieving document checklist. Please inform the user out loud: 'I could not fetch the document checklist from the government records just now. Usually, an Aadhaar card and bank details are required, but let me retry in a moment.'",
        }

    key = scheme_id.strip().lower()
    if key not in SCHEMES_DB:
        return {
            "status": "error",
            "as_of_date": DATA_TIMESTAMP,
            "error_message": f"OUT_LOUD_FAILURE: Scheme '{scheme_id}' was not found. Please inform the user out loud that the requested scheme checklist is not available.",
        }

    scheme = SCHEMES_DB[key]
    return {
        "status": "success",
        "as_of_date": DATA_TIMESTAMP,
        "scheme_id": scheme["scheme_id"],
        "scheme_name": scheme["full_name"],
        "mandatory_documents": scheme["document_checklist"],
        "application_process": scheme["application_process"],
    }
