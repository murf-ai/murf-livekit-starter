import json

import pytest

try:
    from agent import Assistant
    from schemes_data import (
        DATA_TIMESTAMP,
        evaluate_eligibility,
        get_document_checklist,
        list_all_schemes,
    )
except ImportError:
    from src.agent import Assistant
    from src.schemes_data import (
        DATA_TIMESTAMP,
        evaluate_eligibility,
        get_document_checklist,
        list_all_schemes,
    )


def test_list_all_schemes():
    result = list_all_schemes()
    assert result["status"] == "success"
    assert result["as_of_date"] == DATA_TIMESTAMP
    assert result["total_schemes"] >= 7
    scheme_ids = [s["scheme_id"] for s in result["schemes"]]
    assert "pmjdy" in scheme_ids
    assert "apy" in scheme_ids
    assert "ssy" in scheme_ids
    assert "pm_kisan" in scheme_ids


def test_evaluate_eligibility_pmjdy_success():
    res = evaluate_eligibility(scheme_id="pmjdy", age=25, is_taxpayer=False)
    assert res["status"] == "success"
    assert res["is_eligible"] is True
    assert res["eligibility_status"] == "ELIGIBLE"
    assert res["as_of_date"] == DATA_TIMESTAMP


def test_evaluate_eligibility_apy_taxpayer_ineligible():
    # APY excludes income taxpayers
    res = evaluate_eligibility(scheme_id="apy", age=30, is_taxpayer=True)
    assert res["status"] == "success"
    assert res["is_eligible"] is False
    assert res["eligibility_status"] == "NOT_ELIGIBLE"
    assert any("tax" in r.lower() for r in res["reasons"])


def test_evaluate_eligibility_pm_kisan_no_land_ineligible():
    # PM-KISAN requires land ownership
    res = evaluate_eligibility(
        scheme_id="pm_kisan", age=40, is_taxpayer=False, land_holding_acres=0.0
    )
    assert res["status"] == "success"
    assert res["is_eligible"] is False
    assert any("land" in r.lower() for r in res["reasons"])


def test_evaluate_eligibility_pm_kisan_with_land_eligible():
    res = evaluate_eligibility(
        scheme_id="pm_kisan", age=40, is_taxpayer=False, land_holding_acres=2.5
    )
    assert res["status"] == "success"
    assert res["is_eligible"] is True


def test_get_document_checklist_success():
    res = get_document_checklist(scheme_id="pmjdy")
    assert res["status"] == "success"
    assert res["as_of_date"] == DATA_TIMESTAMP
    assert len(res["mandatory_documents"]) > 0
    assert any("Aadhaar" in doc for doc in res["mandatory_documents"])


def test_failure_path_out_loud_simulated_error():
    res = evaluate_eligibility(scheme_id="pmjdy", simulate_failure=True)
    assert res["status"] == "error"
    assert "OUT_LOUD_FAILURE" in res["error_message"]
    assert res["as_of_date"] == DATA_TIMESTAMP


def test_failure_path_unknown_scheme():
    res = evaluate_eligibility(scheme_id="unknown_scheme_xyz")
    assert res["status"] == "error"
    assert "OUT_LOUD_FAILURE" in res["error_message"]


@pytest.mark.asyncio
async def test_assistant_function_tools():
    assistant = Assistant(user_id="test_user_123")

    # 1. Test list_available_schemes tool
    schemes_json = await assistant.list_available_schemes()
    schemes_dict = json.loads(schemes_json)
    assert schemes_dict["status"] == "success"

    # 2. Test check_scheme_eligibility tool
    elig_json = await assistant.check_scheme_eligibility(
        scheme_id="ssy", age=5, gender="female"
    )
    elig_dict = json.loads(elig_json)
    assert elig_dict["is_eligible"] is True
    assert elig_dict["as_of_date"] == DATA_TIMESTAMP

    # 3. Test get_scheme_document_checklist tool
    docs_json = await assistant.get_scheme_document_checklist(scheme_id="ssy")
    docs_dict = json.loads(docs_json)
    assert docs_dict["status"] == "success"
    assert len(docs_dict["mandatory_documents"]) > 0
