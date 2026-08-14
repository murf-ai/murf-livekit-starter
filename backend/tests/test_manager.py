"""Unit tests for manager module."""

import tempfile
from pathlib import Path

import pytest

from manager import (
    approve_manager_request,
    create_manager_request,
    init_manager_db,
    list_manager_requests,
    reject_manager_request,
    update_manager_request,
)


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    init_manager_db(db_path)
    yield db_path
    if db_path.exists():
        db_path.unlink()


def test_create_account_activation_request(temp_db):
    req = create_manager_request(
        request_type="ACCOUNT_ACTIVATION",
        requester_name="Rohan Sharma",
        safe_key="SECRET_SAFE_KEY_789",
        details={"account_type": "Savings"},
        db_path=temp_db,
    )
    assert req["ok"]
    assert req["status"] == "PENDING_APPROVAL"
    assert req["requester_name"] == "Rohan Sharma"
    assert req["safe_key"] == "SECRET_SAFE_KEY_789"

    items = list_manager_requests(db_path=temp_db)
    assert len(items) == 1
    assert items[0]["request_id"] == req["request_id"]
    assert items[0]["safe_key"] == "SECRET_SAFE_KEY_789"


def test_approve_and_reject_request(temp_db):
    req1 = create_manager_request(
        request_type="ACCOUNT_ACTIVATION",
        requester_name="Anita Roy",
        safe_key="KEY_ANITA",
        db_path=temp_db,
    )
    req2 = create_manager_request(
        request_type="TRANSACTION_TRANSFER",
        requester_name="Priya Patel",
        safe_key="KEY_PRIYA",
        details={"amount": 5000},
        db_path=temp_db,
    )

    app_res = approve_manager_request(req1["request_id"], db_path=temp_db)
    assert app_res["ok"]
    assert app_res["status"] == "APPROVED"

    rej_res = reject_manager_request(req2["request_id"], db_path=temp_db)
    assert rej_res["ok"]
    assert rej_res["status"] == "REJECTED"

    pending = list_manager_requests(status="PENDING_APPROVAL", db_path=temp_db)
    assert len(pending) == 0

    approved = list_manager_requests(status="APPROVED", db_path=temp_db)
    assert len(approved) == 1
    assert approved[0]["requester_name"] == "Anita Roy"


def test_update_request(temp_db):
    req = create_manager_request(
        request_type="TRANSACTION_TRANSFER",
        requester_name="Varun Sen",
        db_path=temp_db,
    )
    update_res = update_manager_request(
        req["request_id"],
        status="REJECTED",
        resolution_notes="Failed Safe Key check",
        details={"amount": 1000, "failure": "Wrong key input"},
        db_path=temp_db,
    )
    assert update_res["ok"]

    items = list_manager_requests(status="REJECTED", db_path=temp_db)
    assert len(items) == 1
    assert items[0]["requester_name"] == "Varun Sen"
    assert items[0]["resolution_notes"] == "Failed Safe Key check"
    assert items[0]["details"]["failure"] == "Wrong key input"
