"""Keep bank-account opening separate from Safe Key profile registration."""

from agent import (
    _ACCOUNT_CREATION_INTENT_RE,
    _TRANSACTION_INTENT_RE,
    _specialist_route_for_text,
)


def test_bank_account_requests_do_not_start_safe_key_profile_registration() -> None:
    bank_requests = [
        "I want to open a bank account",
        "I want to add a bank account",
        "Mujhe bank account kholna hai",
    ]
    assert all(not _ACCOUNT_CREATION_INTENT_RE.search(text) for text in bank_requests)


def test_explicit_app_profile_requests_start_safe_key_profile_registration() -> None:
    profile_requests = [
        "Create a Jan Sahay profile",
        "I want to register a user ID",
        "Create an app profile",
        "Add a profile account",
    ]
    assert all(_ACCOUNT_CREATION_INTENT_RE.search(text) for text in profile_requests)


def test_transaction_amount_phrase_requires_transaction_verification() -> None:
    assert _TRANSACTION_INTENT_RE.search("I want the transaction of five thousand")


def test_latest_specialist_topic_has_a_deterministic_route() -> None:
    assert _specialist_route_for_text("I want to know about government schemes") == (
        "government_schemes"
    )
    assert _specialist_route_for_text("How do I open a bank account?") == (
        "account_support"
    )
    assert _specialist_route_for_text("What is UPI?") == "digital_safety"
    assert _specialist_route_for_text("My card was lost") == "digital_safety"
    assert _specialist_route_for_text("I need to report an unauthorized debit") == (
        "digital_safety"
    )
